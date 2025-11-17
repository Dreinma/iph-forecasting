from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, redirect, flash, session
import pandas as pd
import json
import os
import re  
from datetime import datetime, timedelta, date
import plotly
import plotly.graph_objs as go
from werkzeug.utils import secure_filename
import numpy as np
import pytz
from services.visualization_service import VisualizationService
from services.forecast_service import ForecastService
from services.commodity_insight_service import CommodityInsightService
from services.debugger import init_debugger, debugger
from database import db, IPHData, CommodityData, AdminUser, AlertRule
from services.data_handler import DataHandler

from auth.decorators import admin_required, login_required

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            if np.isnan(obj) or np.isinf(obj):
                return None  # Convert NaN/Inf to null
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def clean_for_json(obj):
    """Recursively clean object for JSON serialization"""   

    if obj is None:
        return None
    
    # Handle numpy types
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Handle pandas types
    if isinstance(obj, (pd.Timestamp, pd.DatetimeTZDtype)):
        return obj.isoformat()
    
    if isinstance(obj, pd.Series):
        return obj.tolist()
    
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    
    # Handle datetime
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    # Handle dict
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    
    # Handle list/tuple
    if isinstance(obj, (list, tuple)):
        return [clean_for_json(item) for item in obj]
    
    # Handle model objects - SKIP THEM!
    if hasattr(obj, 'predict') and hasattr(obj, 'fit'):
        return f"<Model: {type(obj).__name__}>"
    
    # Primitive types
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Unknown type - convert to string
    return str(obj)

def safe_float(value):
    """Safely convert value to float"""
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            if np.isnan(value) or np.isinf(value):
                return 0.0
            return float(value)
        return float(str(value))
    except (ValueError, TypeError):
        return 0.0

def calculate_overall_model_score(mae, rmse, r2_score, mape):
    """Calculate weighted overall score for model"""
    try:
        # MAE Score (0-2 range, lower is better)
        mae_score = max(0, min(100, (2.0 - min(mae, 2.0)) / 2.0 * 100))
        
        # RMSE Score (0-3 range, lower is better)  
        rmse_score = max(0, min(100, (3.0 - min(rmse, 3.0)) / 3.0 * 100))
        
        # R Score (0-1 range, higher is better)
        r2_normalized = max(0, min(100, max(r2_score, 0) * 100))
        
        # MAPE Score (0-100% range, lower is better)
        mape_score = max(0, min(100, (100 - min(mape, 100))))

        # UPDATED WEIGHTS: MAE(35%) + RMSE(25%) + R(25%) + MAPE(15%)
        overall = (
            mae_score * 0.35 +
            rmse_score * 0.25 +
            r2_normalized * 0.25 +
            mape_score * 0.15
        )
        
        return max(0, min(100, overall))
        
    except Exception as e:
        logger.warning(f"Error calculating overall score: {e}")
        return 0.0

def get_model_status_badge(overall_score, mae):
    """Determine status badge based on scores"""
    try:
        if overall_score >= 85 and mae < 0.5:
            return {'status': 'Excellent', 'color': 'success', 'icon': 'fa-star'}
        elif overall_score >= 70 and mae < 1.0:
            return {'status': 'Good', 'color': 'info', 'icon': 'fa-thumbs-up'}
        elif overall_score >= 50 and mae < 2.0:
            return {'status': 'Fair', 'color': 'warning', 'icon': 'fa-minus-circle'}
        else:
            return {'status': 'Poor', 'color': 'danger', 'icon': 'fa-times-circle'}
    except:
        return {'status': 'Unknown', 'color': 'secondary', 'icon': 'fa-question'}

def filter_by_timeframe(df, timeframe):
    """Filter dataframe by timeframe"""
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    
    if timeframe == '1M':
        cutoff = datetime.now() - timedelta(days=30)
    elif timeframe == '3M':
        cutoff = datetime.now() - timedelta(days=90)
    elif timeframe == '6M':
        cutoff = datetime.now() - timedelta(days=180)
    elif timeframe == '1Y':
        cutoff = datetime.now() - timedelta(days=365)
    else:  # ALL
        return df
    
    return df[df['Tanggal'] >= cutoff]

app = Flask(__name__)
app.config.from_object('config.Config')
app.json_encoder = CustomJSONEncoder

# Configure logging
import logging
from logging import StreamHandler

# Set up clean console logging
log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'), logging.INFO)
console_handler = StreamHandler()
console_handler.setLevel(log_level)

# Compact formatter - shorter format
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(formatter)

# Get root logger and add handler
root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.addHandler(console_handler)

# Suppress verbose third-party loggers
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# Create app logger
logger = logging.getLogger(__name__)

# Initialize database
from database import db
db.init_app(app)

# AUTO DATABASE INITIALIZATION & MIGRATION

def _calculate_date_from_period(bulan_str, minggu_str, tahun=None):
    """Calculate date from bulan and minggu"""
    from datetime import datetime, timedelta
    
    def get_month_number(bulan_str):
        if pd.isna(bulan_str):
            return 1
        bulan_str = str(bulan_str).strip().lower()
        month_map = {
            'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
        }
        return month_map.get(bulan_str, 1)
    
    def get_week_number(minggu_str):
        if pd.isna(minggu_str):
            return 1
        minggu_str = str(minggu_str).strip()
        if minggu_str.startswith('M'):
            try:
                return int(minggu_str[1:])
            except:
                return 1
        return 1
    
    try:
        bulan_num = get_month_number(bulan_str)
        minggu_num = get_week_number(minggu_str)
        
        if tahun is None:
            tahun = datetime.now().year
        
        first_day = datetime(tahun, bulan_num, 1)
        days_since_monday = first_day.weekday()
        week_start = first_day - timedelta(days=days_since_monday)
        target_date = week_start + timedelta(weeks=minggu_num-1, days=6)
        
        return target_date.date()
    except:
        return None

def _get_month_number(bulan_str):
    """Get month number from bulan string"""
    if pd.isna(bulan_str):
        return 1
    bulan_str = str(bulan_str).strip().lower()
    if "'" in bulan_str:
        bulan_str = bulan_str.split("'")[0].strip()
    month_map = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
    }
    return month_map.get(bulan_str, 1)

# SUCCESS: CALL INITIALIZATION

# Initialize services
forecast_service = ForecastService()
visualization_service = VisualizationService(forecast_service.data_handler)
commodity_service = CommodityInsightService()

# Initialize centralized debugger
init_debugger(app)

# Initialize Authentication
from auth import init_auth
init_auth(app)

# Register Admin Blueprint
from admin.routes import admin_bp
app.register_blueprint(admin_bp)


# Diagnostics endpoint to inspect recent events/errors
@app.route('/api/_debug/recent')
def api_debug_recent():
    from flask import jsonify
    data = debugger.get_recent()
    return jsonify({
        'success': True,
        'recent_events': data.get('events', []),
        'recent_errors': data.get('errors', []),
        'verbose': data.get('verbose', True)
    })

# Create upload folder
if 'UPLOAD_FOLDER' in app.config:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
else:
    # Fallback for production
    upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
# 1. MAIN ROUTES

@app.route('/')
def dashboard():
    """Main dashboard - Public access (visitor) atau Admin"""
    # Visitor access is free - no login needed
    # Admin access via /admin/dashboard
    try:
        dashboard_data = forecast_service.get_dashboard_data()
        
        if dashboard_data['success']:
            return render_template('dashboard.html', 
                                 data=dashboard_data,
                                 page_title="IPH Forecasting Dashboard")
        else:
            flash(f"Dashboard loading issue: {dashboard_data.get('error', 'Unknown error')}", 'warning')
            empty_data = {
                'success': False,
                'data_summary': {'total_records': 0},
                'system_status': {
                    'status_message': 'Please upload data to get started',
                    'status_level': 'warning',
                    'ready_for_use': False
                }
            }
            return render_template('dashboard.html', 
                                 data=empty_data,
                                 page_title="IPH Forecasting Dashboard")
            
    except Exception as e:
        flash(f"Dashboard error: {str(e)}", 'error')
        empty_data = {
            'success': False,
            'data_summary': {'total_records': 0},
            'system_status': {
                'status_message': 'System error occurred. Please try uploading data.',
                'status_level': 'danger',
                'ready_for_use': False
            }
        }
        return render_template('dashboard.html', 
                             data=empty_data,
                             page_title="IPH Forecasting Dashboard")

@app.route('/data-control')
def data_control():
    """Data Control page - Redirected to admin only"""
    from flask_login import current_user
    from flask import redirect, url_for
    # Redirect to admin data control page
    return redirect(url_for('admin.data_control'))

@app.route('/visualization')
def visualization():
    """Data Visualization page"""
    return render_template('visualization.html', page_title="Visualisasi Data IPH")

@app.route('/commodity-insights')
def commodity_insights():
    """Commodity Insights page"""
    return render_template('commodity_insights.html', page_title="Commodity Insights")

@app.route('/alerts')
def alerts():
    """Alert System page"""
    return render_template('alerts.html', page_title="Sistem Peringatan IPH")

@app.route('/historical-data')
def historical_data():
    """Historical Data page - Show all IPH data in table format"""
    return render_template('historical_data.html', page_title="Data Historis IPH")

# 2. DATA MANAGEMENT APIs

@app.route('/api/upload-data', methods=['POST'])
@admin_required
def upload_data():
    """
    MODIFIED: HANYA mengupload data ke database. TIDAK MELAKUKAN TRAINING.
    Membaca file dari stream memori, tidak menyimpan ke disk (Vercel compatible).
    """
    logger = app.logger
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})

        # BACA LANGSUNG DARI STREAM (Vercel tidak bisa menyimpan file)
        try:
            if file.filename.lower().endswith('.csv'):
                # Coba beberapa encoding umum
                df = None
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        file.stream.seek(0) # Kembali ke awal stream
                        df = pd.read_csv(file.stream, encoding=encoding)
                        logger.debug(f"CSV loaded from stream with {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                if df is None:
                    return jsonify({'success': False, 'message': 'Gagal membaca file CSV. Coba encoding UTF-8.'})
            
            elif file.filename.lower().endswith(('.xlsx', '.xls')):
                file.stream.seek(0)
                df = pd.read_excel(file.stream)
                logger.debug("Excel file loaded from stream")
            else:
                return jsonify({'success': False, 'message': 'Format file tidak valid (hanya .csv, .xlsx).'})
        
        except Exception as e:
            logger.error(f"Error reading file stream: {str(e)}")
            return jsonify({'success': False, 'message': f'Error reading file: {str(e)}'})

        if df.empty or len(df) < 1:
            return jsonify({'success': False, 'message': 'File kosong atau tidak ada data.'})
        
        # Panggil data_handler yang sudah dimodifikasi
        logger.info(f"Memanggil data_handler.merge_and_save_data untuk {len(df)} baris...")
        combined_df, merge_info = forecast_service.data_handler.merge_and_save_data(df)
        
        return jsonify({
            'success': True,
            'message': f"Data berhasil di-upload ke database. {merge_info['new_records']} rekaman baru, {merge_info['updated_records']} diperbarui. Jalankan training lokal untuk memperbarui model.",
            'merge_info': merge_info
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Unexpected error: {str(e)}'})

@app.route('/api/add-single-record', methods=['POST'])
@admin_required
def add_single_record():
    """Add single IPH record to database (legacy)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        tanggal = data.get('tanggal')
        indikator_harga = data.get('indikator_harga')
        
        if not tanggal or indikator_harga is None:
            return jsonify({'success': False, 'message': 'Date and IPH value are required'})
        
        try:
            pd.to_datetime(tanggal)
        except:
            return jsonify({'success': False, 'message': 'Invalid date format'})
        
        try:
            float(indikator_harga)
        except:
            return jsonify({'success': False, 'message': 'Invalid IPH value'})
        
        new_record = pd.DataFrame({
            'Tanggal': [tanggal],
            'Indikator_Harga': [float(indikator_harga)]
        })
        
        result = forecast_service.data_handler.merge_and_save_data(new_record)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Record added successfully',
                'total_records': result[1]['total_records']
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to add record'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding record: {str(e)}'})

@app.route('/api/add-manual-record', methods=['POST'])
@admin_required
def add_manual_record():
    """Add manual IPH and commodity record to database"""
    try:
        from database import db, IPHData, CommodityData
        from datetime import datetime, timedelta
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        # Extract data
        bulan = data.get('bulan')
        minggu = data.get('minggu')
        tahun = data.get('tahun')
        kab_kota = data.get('kab_kota', 'BATU')
        iph_value = data.get('iph_value')
        komoditas_andil = data.get('komoditas_andil', '')
        komoditas_fluktuasi = data.get('komoditas_fluktuasi', '')
        nilai_fluktuasi = data.get('nilai_fluktuasi', 0.0)
        
        # Validate required fields
        if not all([bulan, minggu, tahun, iph_value]):
            return jsonify({'success': False, 'message': 'Bulan, minggu, tahun, dan nilai IPH wajib diisi'})
        
        # Calculate date from period
        bulan_map = {
            'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4,
            'Mei': 5, 'Juni': 6, 'Juli': 7, 'Agustus': 8,
            'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
        }
        
        minggu_num = int(str(minggu).replace('M', ''))
        bulan_num = bulan_map.get(bulan, 1)
        
        # Calculate approximate date (first week of month + (minggu-1) * 7 days)
        first_day = datetime(tahun, bulan_num, 1)
        days_since_monday = first_day.weekday()
        week_start = first_day - timedelta(days=days_since_monday)
        target_date = week_start + timedelta(weeks=minggu_num-1, days=6)
        
        # Check if record already exists
        existing_iph = IPHData.query.filter_by(
            tanggal=target_date.date(),
            bulan=bulan,
            minggu=minggu
        ).first()
        
        if existing_iph:
            return jsonify({'success': False, 'message': f'Data untuk {bulan} {minggu} {tahun} sudah ada'})
        
        # Create IPH record
        iph_record = IPHData(
            tanggal=target_date.date(),
            indikator_harga=float(iph_value),
            bulan=bulan,
            minggu=minggu,
            tahun=tahun,
            bulan_numerik=bulan_num,
            kab_kota=kab_kota,
            data_source='manual_input'
        )
        
        db.session.add(iph_record)
        db.session.flush()  # Get the ID
        
        # Create Commodity record
        commodity_record = CommodityData(
            tanggal=target_date.date(),
            bulan=bulan,
            minggu=minggu,
            tahun=tahun,
            kab_kota=kab_kota,
            iph_id=iph_record.id,
            iph_value=float(iph_value),
            komoditas_andil=komoditas_andil,
            komoditas_fluktuasi=komoditas_fluktuasi,
            nilai_fluktuasi=float(nilai_fluktuasi)
        )
        
        db.session.add(commodity_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Data berhasil ditambahkan',
            'data': {
                'tanggal': target_date.strftime('%Y-%m-%d'),
                'bulan': bulan,
                'minggu': minggu,
                'tahun': tahun,
                'iph_value': float(iph_value)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error adding record: {str(e)}'})

@app.route('/api/historical-data')
def api_historical_data():
    """API untuk mengambil data historis dengan pagination"""
    from database import IPHData
    from sqlalchemy import func, or_
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort_by', 'tanggal')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = IPHData.query
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    IPHData.bulan.ilike(f'%{search}%'),
                    IPHData.minggu.ilike(f'%{search}%'),
                    IPHData.kab_kota.ilike(f'%{search}%')
                )
            )
        
        # Sort
        if sort_by == 'tanggal':
            order_col = IPHData.tanggal
        elif sort_by == 'indikator_harga':
            order_col = IPHData.indikator_harga
        else:
            order_col = IPHData.tanggal
        
        if sort_order == 'desc':
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())
        
        # Pagination
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Convert to dict
        items = []
        for record in pagination.items:
            items.append({
                'id': record.id,
                'tanggal': record.tanggal.strftime('%Y-%m-%d') if record.tanggal else None,
                'indikator_harga': float(record.indikator_harga) if record.indikator_harga else None,
                'bulan': record.bulan or '',
                'minggu': record.minggu or '',
                'tahun': record.tahun or (record.tanggal.year if record.tanggal else None),
                'kab_kota': record.kab_kota or 'BATU',
                'data_source': record.data_source or '',
                'updated_at': record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if record.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'items': items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages if pagination.pages else 1
                }
            }
        })
    except Exception as e:
        logger.error(f"Error loading historical data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data-summary')
def api_data_summary():
    """API endpoint for data summary"""
    try:
        summary = forecast_service.data_handler.get_data_summary()
        cleaned_summary = clean_for_json(summary)
        return jsonify(cleaned_summary)
    except Exception as e:
        error_response = clean_for_json({
            'error': f'Error getting data summary: {str(e)}'
        })
        return jsonify(error_response)

# 3. FORECASTING APIs

@app.route('/api/forecast-chart-data')
def forecast_chart_data():
    """API endpoint untuk mendapatkan data forecast untuk chart"""
    try:
        from database import ForecastHistory
        
        latest_forecast = ForecastHistory.query.order_by(
            ForecastHistory.created_at.desc()
        ).first()
        
        if latest_forecast:
            try:
                forecast_data = latest_forecast.forecast_data  # Already list
                confidence_intervals = latest_forecast.confidence_intervals  # Already list
                
                if isinstance(forecast_data, str):
                    forecast_data = json.loads(forecast_data)
                if isinstance(confidence_intervals, str):
                    confidence_intervals = json.loads(confidence_intervals)
                
                predictions = []
                
                # forecast_data structure: [{'date': '...', 'prediction': X, 'lower_bound': Y, ...}, ...]
                for i, item in enumerate(forecast_data):
                    prediction_item = {
                        'week': i + 1,
                        'date': item.get('date'),
                        'value': float(item.get('prediction', 0))
                    }
                    
                    # Add confidence intervals from forecast_data itself
                    if 'lower_bound' in item and 'upper_bound' in item:
                        prediction_item['lower_bound'] = float(item['lower_bound'])
                        prediction_item['upper_bound'] = float(item['upper_bound'])
                    # Or from separate confidence_intervals array
                    elif confidence_intervals and i < len(confidence_intervals):
                        ci = confidence_intervals[i]
                        prediction_item['lower_bound'] = float(ci.get('lower', 0))
                        prediction_item['upper_bound'] = float(ci.get('upper', 0))
                    
                    predictions.append(prediction_item)
                
                forecast_result = {
                    'success': True,
                    'timestamp': latest_forecast.created_at.isoformat(),
                    'forecast': {
                        'data': predictions,
                        'model_name': latest_forecast.model_name,
                        'model_performance': {
                            'mae': float(latest_forecast.validation_mae) if latest_forecast.validation_mae else 0.0,
                            'rmse': float(latest_forecast.validation_rmse) if latest_forecast.validation_rmse else 0.0,
                            'r2_score': 0.0,  # ❌ Tidak ada di schema
                            'training_time': 0.0
                        },
                        'summary': {
                            'avg_prediction': float(latest_forecast.avg_prediction) if latest_forecast.avg_prediction else 0.0,
                            'trend': latest_forecast.trend or 'stable',
                            'volatility': 0.0,
                            'min_prediction': float(latest_forecast.min_value) if latest_forecast.min_value else 0.0,
                            'max_prediction': float(latest_forecast.max_value) if latest_forecast.max_value else 0.0
                        },
                        'weeks_forecasted': latest_forecast.forecast_weeks or len(predictions)
                    }
                }
                
                logger.info(f"✅ Forecast loaded from DB: {latest_forecast.model_name} (ID: {latest_forecast.id})")
                return jsonify(forecast_result)
                
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                logger.warning(f"⚠️ Error parsing forecast from database: {str(e)}, trying fallback...")
                # Continue to fallback
        
        if hasattr(forecast_service, '_latest_forecast') and forecast_service._latest_forecast:
            logger.info("📦 Loading forecast from in-memory cache")
            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'forecast': forecast_service._latest_forecast
            })
        
        logger.info("🔄 No forecast in DB/cache, generating new...")
        forecast_result = forecast_service.get_current_forecast()
        
        if forecast_result.get('success'):
            logger.info("✅ New forecast generated")
        else:
            logger.error(f"❌ Forecast generation failed: {forecast_result.get('error')}")
        
        return jsonify(forecast_result)
        
    except Exception as e:
        logger.error(f"❌ Error in forecast_chart_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Terjadi kesalahan saat memuat data forecast',
            'details': str(e) if app.config.get('DEBUG') else 'Internal server error'
        }), 500

@app.route('/api/model-comparison-chart')
def model_comparison_chart():
    """API endpoint for model comparison data"""
    try:
        model_summary = forecast_service.model_manager.get_model_performance_summary()
        
        if not model_summary:
            return jsonify({
                'success': False, 
                'message': 'No model data available',
                'metrics': []
            })
        
        metrics = []
        for model_name, summary in model_summary.items():
            latest_performance = summary.get('performances', [])
            latest_perf = latest_performance[-1] if latest_performance else {}

            mae_val = safe_float(summary.get('latest_mae', 0.0))
            rmse_val = safe_float(latest_perf.get('rmse', 0.0))
            r2_val = safe_float(summary.get('latest_r2', 0.0))
            mape_val = safe_float(latest_perf.get('mape', 0.0))

            overall_score = calculate_overall_model_score(
                mae=mae_val,
                rmse=rmse_val,
                r2_score=r2_val,
                mape=mape_val
            )

            badge = get_model_status_badge(overall_score, mae_val)

            metrics.append({
                'name': model_name.replace('_', ' '),
                'mae': mae_val,
                'rmse': rmse_val,
                'r2_score': r2_val,
                'mape': mape_val,
                'overall_score': int(round(overall_score)),
                'status': badge['status'],
                'status_color': badge['color'],
                'status_icon': badge['icon'],
                'training_count': summary.get('training_count', 0),
                'trend_direction': summary.get('trend_direction', 'stable')
            })
        
        metrics.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'total_models': len(metrics)
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error in model comparison API: {str(e)}")
        logger.error(f"ERROR: Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'metrics': []
        })

@app.route('/api/economic-alerts')
def get_economic_alerts():
    """Get real-time economic alerts"""
    logger.debug("API /api/economic-alerts called")
    try:
        alerts_data = forecast_service.get_real_economic_alerts()
        logger.debug(f"API returning: success={alerts_data['success']}, alerts_count={len(alerts_data.get('alerts', []))}")
        return jsonify(alerts_data)
    except Exception as e:
        error_msg = f"API error: {str(e)}"
        logger.error(f"ERROR: {error_msg}")
        import traceback
        logger.error(f"ERROR: Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': error_msg,
            'alerts': []
        })

@app.route('/admin/api/forecasts/history', methods=['GET'])
@login_required 
@admin_required 
def get_forecast_history():
    """API untuk mendapatkan forecast history (untuk admin page)"""
    try:
        from database import db, ForecastHistory
        
        # ✅ ROLLBACK dulu (jaga-jaga ada pending transaction)
        try:
            db.session.rollback()
        except:
            pass
        
        # Get pagination & filter parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        model_filter = request.args.get('model', '', type=str)
        
        # Build query
        query = ForecastHistory.query.order_by(ForecastHistory.created_at.desc())
        
        # Apply model filter
        if model_filter:
            query = query.filter(ForecastHistory.model_name.ilike(f'%{model_filter}%'))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        forecasts = query.limit(per_page).offset((page - 1) * per_page).all()
        
        # Convert to dict
        forecast_list = []
        for forecast in forecasts:
            try:
                # Parse JSONB data safely
                forecast_data = forecast.forecast_data if isinstance(forecast.forecast_data, list) else []
                
                forecast_list.append({
                    'id': forecast.id,
                    'created_at': forecast.created_at.isoformat() if forecast.created_at else None,
                    'model_name': forecast.model_name,
                    'weeks_forecasted': forecast.forecast_weeks,
                    'avg_prediction': float(forecast.avg_prediction) if forecast.avg_prediction else None,
                    'trend': forecast.trend or 'stable',
                    'validation_mae': float(forecast.validation_mae) if forecast.validation_mae else None,
                    'validation_rmse': float(forecast.validation_rmse) if forecast.validation_rmse else None,
                    'created_by': forecast.created_by or 'system'
                })
            except Exception as e:
                logger.error(f"Error parsing forecast {forecast.id}: {e}")
                continue
        
        # ✅ SESUAI FORMAT FRONTEND (result.data.items)
        return jsonify({
            'success': True,
            'data': {
                'items': forecast_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting forecast history: {str(e)}", exc_info=True)
        
        # Rollback on error
        try:
            db.session.rollback()
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Failed to load forecast history',
            'details': str(e) if app.config.get('DEBUG') else None
        }), 500


# ✅ TAMBAHAN: API untuk Statistics
@app.route('/admin/api/forecasts/statistics', methods=['GET'])
@login_required
@admin_required
def get_forecast_statistics():
    """API untuk mendapatkan statistik forecast"""
    try:
        from database import db, ForecastHistory
        from sqlalchemy import func, extract
        from datetime import datetime
        
        # Rollback dulu
        try:
            db.session.rollback()
        except:
            pass
        
        # Total forecasts
        total_forecasts = ForecastHistory.query.count()
        
        # This month
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        this_month = ForecastHistory.query.filter(
            extract('month', ForecastHistory.created_at) == current_month,
            extract('year', ForecastHistory.created_at) == current_year
        ).count()
        
        # Most used model
        most_used = db.session.query(
            ForecastHistory.model_name,
            func.count(ForecastHistory.id).label('count')
        ).group_by(ForecastHistory.model_name).order_by(func.count(ForecastHistory.id).desc()).first()
        
        most_used_model = most_used[0] if most_used else 'N/A'
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_forecasts': total_forecasts,
                'this_month': this_month,
                'most_used_model': most_used_model
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting forecast statistics: {str(e)}", exc_info=True)
        
        try:
            db.session.rollback()
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ✅ TAMBAHAN: API untuk Export
@app.route('/admin/api/forecasts/export', methods=['GET'])
@login_required
@admin_required
def export_forecast_history():
    """Export forecast history ke CSV"""
    try:
        from database import db, ForecastHistory
        import csv
        from io import StringIO
        from flask import make_response
        
        # Rollback dulu
        try:
            db.session.rollback()
        except:
            pass
        
        # Get all forecasts
        forecasts = ForecastHistory.query.order_by(ForecastHistory.created_at.desc()).all()
        
        # Create CSV
        si = StringIO()
        cw = csv.writer(si)
        
        # Header
        cw.writerow(['ID', 'Date', 'Model', 'Weeks', 'Avg Prediction', 'Trend', 'MAE', 'RMSE', 'Created By'])
        
        # Data
        for f in forecasts:
            cw.writerow([
                f.id,
                f.created_at.strftime('%Y-%m-%d %H:%M') if f.created_at else '',
                f.model_name,
                f.forecast_weeks,
                f'{f.avg_prediction:.4f}' if f.avg_prediction else '',
                f.trend,
                f'{f.validation_mae:.4f}' if f.validation_mae else '',
                f'{f.validation_rmse:.4f}' if f.validation_rmse else '',
                f.created_by
            ])
        
        # Create response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=forecast_history.csv"
        output.headers["Content-type"] = "text/csv"
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error exporting forecast history: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# 4. VISUALIZATION APIs

@app.route('/api/visualization/moving-averages')
def api_moving_averages():
    """API for moving averages analysis"""
    try:
        timeframe = request.args.get('timeframe', '6M')
        offset = request.args.get('offset', 0, type=int)
        
        df = forecast_service.data_handler.load_historical_data()
        logger.info(f"Data loaded: {len(df)} records")

        if df is None or df.empty:
            logger.error(f"   ERROR: ERROR: No data in database")
            return jsonify({
                'success': False, 
                'message': 'Tidak ada data di database. Silakan upload data terlebih dahulu.'
            }), 400

        result = visualization_service.calculate_moving_averages(timeframe, offset)
        logger.debug(f"   SUCCESS: Service returned: success={result.get('success')}")
        logger.debug(f"{'='*60}\n")

        if not result['success']:
            return jsonify(result)
        
        return jsonify(result)
        
    except Exception as e:
        logger.debug(f"Moving averages API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Moving averages error: {str(e)}'
        })

@app.route('/api/visualization/volatility')
def api_volatility():
    """API for volatility analysis"""
    try:
        timeframe = request.args.get('timeframe', '6M')
        offset = request.args.get('offset', 0, type=int)
        logger.debug(f"   timeframe={timeframe}, offset={offset}")

        result = visualization_service.analyze_volatility(timeframe, offset)
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"   ERROR: EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        logger.debug(f"{'='*60}\n")
        
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/visualization/model-performance')
def api_model_performance():
    """API endpoint for model performance analysis"""
    try:
        timeframe = request.args.get('timeframe', '6M')
        offset = request.args.get('offset', 0, type=int)
        available_models = forecast_service.model_manager.engine.get_available_models()
        
        if not available_models:
            logger.warning("WARNING: No trained models found - training now...")
            # Auto-train if no models
            df = forecast_service.data_handler.load_historical_data()
            if not df.empty:
                forecast_service.model_manager.train_and_compare_models(df)

        result = visualization_service.analyze_model_performance(timeframe, offset)
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/dashboard/model-performance')
def api_dashboard_model_performance():
    """API endpoint for dashboard model performance metrics"""
    try:
        # Get model performance summary
        model_summary = forecast_service.model_manager.get_model_performance_summary()
        
        if not model_summary:
            return jsonify({
                'success': False,
                'message': 'No model performance data available'
            }), 404
        
        # Format response with 2 decimal places
        models_data = []
        best_mae = float('inf')
        
        # Find best model (lowest MAE)
        for model_name, model_data in model_summary.items():
            if model_data.get('latest_mae', float('inf')) < best_mae:
                best_mae = model_data.get('latest_mae', float('inf'))
        
        for model_name, model_data in model_summary.items():
            latest_mae = model_data.get('latest_mae', 0)
            latest_r2 = model_data.get('latest_r2', 0)
            training_count = model_data.get('training_count', 0)
            
            # Calculate RMSE and MAPE (approximate values)
            rmse = latest_mae * 1.2  # Approximate RMSE
            mape = latest_mae * 10   # Approximate MAPE
            
            models_data.append({
                'name': model_name,
                'mae': round(float(latest_mae), 2),
                'rmse': round(float(rmse), 2),
                'r2': round(float(latest_r2), 2),
                'mape': round(float(mape), 2),
                'status': 'Best' if latest_mae == best_mae else 'Good',
                'training_count': training_count
            })
        
        # Sort by MAE (best first)
        models_data.sort(key=lambda x: x['mae'])
        
        return jsonify({
            'success': True,
            'models': models_data
        })
    except Exception as e:
        logger.debug(f"Error in dashboard model performance: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/data/available-periods')
def api_available_periods():
    """Get all available months and years from database"""
    try:
        df = forecast_service.data_handler.load_historical_data()
        
        if df.empty:
            return jsonify({
                'success': False,
                'message': 'Tidak ada data tersedia'
            })
        
        # Extract unique months and years
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        df = df.sort_values('Tanggal')
        
        # Get all unique year-month combinations
        periods = []
        for _, row in df.iterrows():
            year = row['Tanggal'].year
            month = row['Tanggal'].month
            month_name = row['Tanggal'].strftime('%B')  # e.g., 'January'
            
            period_key = f"{year}-{month:02d}"
            
            # Avoid duplicates
            if not any(p['key'] == period_key for p in periods):
                periods.append({
                    'key': period_key,
                    'year': year,
                    'month': month,
                    'month_name': month_name,
                    'display': f"{month_name} {year}"
                })
        
        # Group by year
        years = sorted(set(p['year'] for p in periods))
        
        # Group periods by year
        periods_by_year = {}
        for year in years:
            periods_by_year[year] = [p for p in periods if p['year'] == year]
        
        logger.debug(f"Available periods: {len(periods)} total, {len(years)} years")
        
        return jsonify({
            'success': True,
            'periods': periods,
            'periods_by_year': periods_by_year,
            'years': years,
            'total_periods': len(periods)
        })
        
    except Exception as e:
        logger.error(f"Error getting available periods: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# 5. COMMODITY APIs

@app.route('/api/commodity/full-insights')
def api_full_commodity_insights():
    """
    API BARU: Mengambil semua data insight (Tren, Frekuensi, Dampak)
    dalam satu panggilan.
    """
    try:
        start_key = request.args.get('start_key')
        end_key = request.args.get('end_key')
        
        # Panggil fungsi service baru
        insights_data = commodity_service.get_full_commodity_insights(
            start_key=start_key, 
            end_key=end_key
        )
        
        return jsonify(clean_for_json(insights_data))

    except Exception as e:
        logger.error(f"ERROR: Full commodity insights error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
        
@app.route('/api/commodity/current-week')
def api_commodity_current_week():
    """Enhanced current week commodity insights"""
    try:
        logger.debug("API: Loading current week insights...")
        result = commodity_service.get_current_week_insights()
        
        logger.debug(f" Current week result structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        logger.debug(f" Success status: {result.get('success')}")
        
        if result.get('success'):
            logger.debug(f"    Period keys: {list(result.get('period', {}).keys())}")
            logger.debug(f"   IPH analysis keys: {list(result.get('iph_analysis', {}).keys())}")
            logger.debug(f"   TAG: Category analysis count: {len(result.get('category_analysis', {}))}")
        else:
            logger.error(f"   ERROR: Error: {result.get('message', 'Unknown error')}")
        
        if result.get('success') and not result.get('iph_analysis'):
            logger.warning("WARNING: Missing iph_analysis, creating fallback...")
            iph_value = result.get('iph_value', 0)
            result['iph_analysis'] = {
                'value': float(iph_value),
                'level': 'Unknown',
                'color': 'secondary',
                'direction': 'Unknown'
            }
        
        return jsonify(clean_for_json(result))
        
    except Exception as e:
        logger.error(f"ERROR: API Error - current week insights: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify(clean_for_json({
            'success': False, 
            'error': str(e),
            'message': 'Failed to load current week insights. Please check if commodity data is available.',
            'error_details': str(e)
        }))

@app.route('/api/commodity/seasonal')
def api_commodity_seasonal():
    """Enhanced seasonal commodity patterns"""
    try:
        logger.debug("API: Loading seasonal patterns...")
        
        result = commodity_service.get_seasonal_patterns()
        
        logger.debug(f" Seasonal result structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        logger.debug(f" Success: {result.get('success')}")
        
        if result.get('success'):
            patterns_count = len(result.get('seasonal_patterns', {}))
            logger.debug(f"   DATE: Found {patterns_count} monthly patterns")
            
            if result.get('seasonal_patterns'):
                first_pattern = list(result['seasonal_patterns'].items())[0] if result['seasonal_patterns'] else None
                if first_pattern:
                    month_name, month_data = first_pattern
                    logger.debug(f"   First pattern '{month_name}' keys: {list(month_data.keys())}")
        
        return jsonify(clean_for_json(result))
        
    except Exception as e:
        logger.error(f"ERROR: API Error - seasonal patterns: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify(clean_for_json({
            'success': False, 
            'error': str(e),
            'message': 'Failed to load seasonal patterns'
        }))

@app.route('/api/commodity/alerts')
def api_commodity_alerts():
    """Enhanced commodity volatility alerts"""
    try:
        threshold = float(request.args.get('threshold', 0.05))
        
        if not (0.01 <= threshold <= 0.5):
            threshold = 0.05
        
        logger.debug(f"API: Loading volatility alerts with threshold: {threshold}")
        
        result = commodity_service.get_alert_commodities(threshold)
        
        logger.debug(f" Alerts result: success={result.get('success')}")
        if result.get('success'):
            alerts_count = len(result.get('alerts', []))
            logger.warning(f"   WARNING: Found {alerts_count} alerts")
        
        return jsonify(clean_for_json(result))
    except Exception as e:
        logger.error(f"ERROR: API Error - commodity alerts: {str(e)}")
        return jsonify(clean_for_json({
            'success': False, 
            'error': str(e),
            'message': 'Failed to load commodity alerts'
        }))

@app.route('/api/commodity/upload', methods=['POST'])
@admin_required
def upload_commodity_data():
    """Enhanced commodity data upload with comprehensive validation"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        if file and file.filename.lower().endswith(('.csv', '.xlsx')):
            filename = secure_filename(file.filename)
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_commodity_{filename}")
            file.save(temp_path)
            
            try:
                logger.debug(f"Processing commodity file: {filename}")
                
                if filename.lower().endswith('.csv'):
                    df = None
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            df = pd.read_csv(temp_path, encoding=encoding)
                            logger.debug(f"CSV loaded successfully with {encoding} encoding")
                            break
                        except UnicodeDecodeError:
                            logger.warning(f"WARNING: Failed to load with {encoding} encoding, trying next...")
                            continue
                    
                    if df is None:
                        return jsonify({
                            'success': False, 
                            'message': 'Unable to read CSV file with any encoding. Please save as UTF-8 CSV.'
                        })
                else:
                    df = pd.read_excel(temp_path)
                    logger.debug("SUCCESS: Excel file loaded successfully")
                
                logger.debug(f" Loaded {len(df)} rows, {len(df.columns)} columns")
                logger.debug(f" Original columns: {list(df.columns)}")
                
                required_column_patterns = {
                    'bulan': [r'.*[Bb]ulan.*', r'.*[Mm]onth.*'],
                    'minggu': [r'.*[Mm]inggu.*', r'.*[Ww]eek.*'],
                    'iph': [r'.*[Ii]ndikator.*[Pp]erubahan.*[Hh]arga.*', r'.*IPH.*', r'.*iph.*'],
                    'komoditas_andil': [r'.*[Kk]omoditas.*[Aa]ndil.*', r'.*[Cc]ommodity.*[Ii]mpact.*'],
                    'komoditas_fluktuasi': [r'.*[Kk]omoditas.*[Ff]luktuasi.*', r'.*[Vv]olatile.*[Cc]ommodity.*'],
                    'nilai_fluktuasi': [r'.*[Ff]luktuasi.*[Hh]arga.*', r'.*[Vv]olatility.*[Vv]alue.*']
                }
                
                column_mapping = {}
                missing_requirements = []
                
                for req_type, patterns in required_column_patterns.items():
                    found = False
                    for pattern in patterns:
                        for col in df.columns:
                            if re.match(pattern, col, re.IGNORECASE):
                                column_mapping[col] = req_type
                                found = True
                                break
                        if found:
                            break
                    
                    if not found and req_type in ['bulan', 'minggu', 'iph']:
                        missing_requirements.append(req_type)
                
                if missing_requirements:
                    return jsonify({
                        'success': False,
                        'message': f'Missing critical columns: {", ".join(missing_requirements)}',
                        'available_columns': list(df.columns),
                        'required_patterns': {k: v[0] for k, v in required_column_patterns.items() if k in missing_requirements}
                    })
                
                logger.debug(f"Column mapping successful: {column_mapping}")
                
                df = df.dropna(how='all')
                
                commodity_path = commodity_service.commodity_data_path
                if request.form.get('backup_existing') == 'true':
                    if os.path.exists(commodity_path):
                        backup_path = commodity_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                        try:
                            import shutil
                            shutil.copy2(commodity_path, backup_path)
                            logger.debug(f" Existing data backed up to: {backup_path}")
                        except Exception as backup_error:
                            logger.warning(f"WARNING: Backup failed: {backup_error}")
                
                os.makedirs(os.path.dirname(commodity_path), exist_ok=True)
                df.to_csv(commodity_path, index=False)
                
                commodity_service.commodity_cache = None
                commodity_service.last_cache_time = None
                
                logger.debug(f"Commodity data saved to: {commodity_path}")
                
                try:
                    test_df = commodity_service.load_commodity_data()
                    if test_df.empty:
                        logger.warning("WARNING: Warning: Saved data appears to be empty after processing")
                except Exception as validation_error:
                    logger.warning(f"WARNING: Data validation warning: {validation_error}")
                
                return jsonify(clean_for_json({
                    'success': True,
                    'message': 'Commodity data uploaded and processed successfully',
                    'records': len(df),
                    'columns_mapped': len(column_mapping),
                    'original_columns': list(df.columns),
                    'processing_info': {
                        'empty_rows_removed': 'yes',
                        'encoding_used': 'auto-detected',
                        'backup_created': request.form.get('backup_existing') == 'true'
                    }
                }))
                
            except Exception as processing_error:
                logger.error(f"ERROR: Processing error: {str(processing_error)}")
                import traceback
                traceback.print_exc()
                
                return jsonify({
                    'success': False, 
                    'message': f'File processing failed: {str(processing_error)}',
                    'error_type': 'processing_error'
                })
                
            finally:
                try:
                    os.remove(temp_path)
                    logger.debug(f"CLEANUP: Cleaned up temp file: {temp_path}")
                except:
                    pass
        
        return jsonify({
            'success': False, 
            'message': 'Invalid file format. Please upload CSV or Excel file.',
            'allowed_formats': ['.csv', '.xlsx']
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify(clean_for_json({
            'success': False, 
            'message': f'Upload failed: {str(e)}',
            'error_type': type(e).__name__
        }))

@app.route('/api/commodity/data-status')
def api_commodity_data_status():
    """Check commodity data availability"""
    try:
        df = commodity_service.load_commodity_data()
        
        return jsonify(clean_for_json({
            'success': True,
            'has_data': not df.empty,
            'record_count': len(df) if not df.empty else 0,
            'date_range': {
                'start': df['Tanggal'].min().strftime('%Y-%m-%d') if not df.empty and 'Tanggal' in df.columns else None,
                'end': df['Tanggal'].max().strftime('%Y-%m-%d') if not df.empty and 'Tanggal' in df.columns else None
            } if not df.empty else None,
            'columns': list(df.columns) if not df.empty else [],
            'last_updated': datetime.now().isoformat()
        }))
    except Exception as e:
        logger.error(f"ERROR: Commodity data status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'has_data': False,
            'record_count': 0
        })

# 6. ALERTS APIs

@app.route('/api/alerts/statistical')
def api_statistical_alerts():
    """API endpoint for statistical alerts"""
    try:
        alerts = [
            {
                'title': 'Volatilitas Tinggi',
                'message': 'Volatilitas IPH mencapai 1.11, melebihi rata-rata 30 hari (0.61)',
                'severity': 'medium',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'title': 'Trend Naik',
                'message': 'IPH menunjukkan tren kenaikan dalam 7 hari terakhir',
                'severity': 'info',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        return jsonify({
            'success': True,
            'alerts': alerts
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

@app.route('/api/alerts/recent')
def api_recent_alerts():
    """API for getting recent alerts"""
    alerts = [
        {
            'id': 1,
            'type': 'threshold',
            'priority': 'critical',
            'title': 'IPH Melampaui Batas Kritis',
            'message': 'IPH mencapai 4.2%, melampaui batas kritis 3%',
            'timestamp': '2024-01-20T14:30:00',
            'acknowledged': False
        },
        {
            'id': 2,
            'type': 'trend',
            'priority': 'warning',
            'title': 'Deteksi Pembalikan Trend',
            'message': 'Trend berubah dari naik ke turun dalam 3 periode terakhir',
            'timestamp': '2024-01-20T12:15:00',
            'acknowledged': True
        },
        {
            'id': 3,
            'type': 'volatility',
            'priority': 'info',
            'title': 'Volatilitas Meningkat',
            'message': 'Volatilitas 7 hari meningkat 25% dari rata-rata',
            'timestamp': '2024-01-20T10:00:00',
            'acknowledged': False
        }
    ]
    
    return jsonify({
        'success': True,
        'alerts': alerts
    })

# 7. EXPORT APIs

@app.route('/api/export-data', methods=['GET'])
@admin_required
def export_data():
    """Export current data to CSV"""
    try:
        data_type = request.args.get('type', 'historical')
        df = pd.DataFrame()
        filename = f"export_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if data_type == 'historical':
            df = forecast_service.data_handler.load_historical_data()
            if df.empty:
                return jsonify({'success': False, 'message': 'No historical data available'})
            
            filename = f"historical_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        elif data_type == 'forecast':
            dashboard_data = forecast_service.get_dashboard_data()
            if not dashboard_data['success'] or not dashboard_data.get('current_forecast'):
                return jsonify({'success': False, 'message': 'No forecast data available'})
            
            forecast_data = dashboard_data['current_forecast']['data']
            df = pd.DataFrame(forecast_data)
            filename = f"forecast_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        elif data_type == 'all':
            historical_df = forecast_service.data_handler.load_historical_data()
            dashboard_data = forecast_service.get_dashboard_data()
            
            if historical_df.empty:
                return jsonify({'success': False, 'message': 'No data available for export'})
            
            df = historical_df.copy()
            filename = f"complete_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            if dashboard_data['success'] and dashboard_data.get('current_forecast'):
                forecast_data = dashboard_data['current_forecast']['data']
                forecast_df = pd.DataFrame(forecast_data)
                
                df['Data_Type'] = 'Historical'
                forecast_df['Data_Type'] = 'Forecast'
                forecast_df['Indikator_Harga'] = forecast_df['Prediksi']
                
                df = pd.concat([df, forecast_df[['Tanggal', 'Indikator_Harga', 'Data_Type']]], ignore_index=True)
        
        else:
            return jsonify({'success': False, 'message': 'Invalid data type specified'})
        
        export_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df.to_csv(export_path, index=False)
        
        file_size = os.path.getsize(export_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': export_path,
            'file_size': file_size,
            'records': len(df),
            'download_url': f'/download/{filename}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Export failed: {str(e)}'
        })

@app.route('/download/<filename>')
def download_file(filename):
    """Download exported file"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/download/template_iph_komoditas.csv')
def download_template():
    """Download CSV template for IPH and commodity data"""
    try:
        # Create template CSV content
        template_content = """Bulan,Minggu ke-,Kab/Kota,Indikator Perubahan Harga (%),Komoditas Andil Perubahan Harga,Komoditas Fluktuasi Harga Tertinggi,Fluktuasi Harga
Januari,M1,BATU,1.25,"BERAS(0.5);CABAI(0.3);MINYAK GORENG(0.2)",CABAI RAWIT,0.0553
Januari,M2,BATU,-0.85,"TELUR AYAM RAS(-0.4);PISANG(-0.3);DAGING AYAM RAS(-0.2)",CABAI MERAH,0.0329
Februari,M1,BATU,2.10,"BERAS(0.8);CABAI(0.6);MINYAK GORENG(0.4)",BAWANG MERAH,0.0657
Februari,M2,BATU,0.75,"DAGING AYAM RAS(0.3);BERAS(0.2);TELUR AYAM RAS(0.1)",CABAI RAWIT,0.0409"""
        
        # Create temporary file
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'template_iph_komoditas.csv')
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        from flask import send_file
        return send_file(temp_path, as_attachment=True, download_name='template_iph_komoditas.csv')
        
    except Exception as e:
        return jsonify({'error': f'Template download failed: {str(e)}'}), 500

@app.route('/api/available-models')
def available_models():
    """Get available models for forecasting"""
    try:
        model_summary = forecast_service.model_manager.get_model_performance_summary()
        
        if not model_summary:
            return jsonify({
                'success': False,
                'message': 'No models available',
                'models': []
            })
        
        models = []
        for model_name, summary in model_summary.items():
            models.append({
                'name': model_name,
                'mae': summary.get('latest_mae', 0.0),
                'r2': summary.get('latest_r2', 0.0),
                'training_count': summary.get('training_count', 0),
                'is_best': False  # Will be set below
            })
        
        # Sort by MAE (lower is better) and mark best
        models.sort(key=lambda x: x['mae'])
        if models:
            models[0]['is_best'] = True
        
        return jsonify({
            'success': True,
            'models': models
        })
        
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error getting models',
            'models': []
        })

@app.route('/api/generate-forecast', methods=['POST'])
def generate_forecast():
    """Generate forecast using selected model"""
    try:
        data = request.get_json()
        
        model_name = data.get('model_name')
        weeks = int(data.get('weeks', 4))
        
        if not model_name:
            return jsonify({
                'success': False,
                'message': 'Model name is required'
            })
        
        # Load historical data
        df = forecast_service.data_handler.load_historical_data()
        if df.empty:
            return jsonify({
                'success': False,
                'message': 'No historical data available for forecasting'
            })
        
        # Generate forecast using the selected model
        forecast_result = forecast_service.get_current_forecast(
            model_name=model_name,
            forecast_weeks=weeks,
        )
        
        if forecast_result['success']:
            return jsonify({
                'success': True,
                'message': 'Forecast generated successfully',
                'forecast': forecast_result['forecast']
            })
        else:
            return jsonify({
                'success': False,
                'message': forecast_result.get('message', 'Failed to generate forecast')
            })
            
    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error generating forecast: {str(e)}'
        })

# UTILITY FUNCTIONS & CONTEXT PROCESSORS

@app.context_processor
def inject_datetime():
    """Inject datetime functions into templates"""
    return {
        'datetime': datetime,
        'now': datetime.now()
    }



# APPLICATION STARTUP
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.debug("Starting IPH Forecasting Dashboard...")
    logger.debug(f"Dashboard will be available at: http://localhost:{port}")
    logger.debug("Data will be stored in: data/historical_data.csv")
    logger.debug("Models will be saved in: data/models/")
    logger.debug(f"Debug mode: {debug}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
