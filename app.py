from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
import json
import os
import re  
from datetime import datetime, timedelta  
import plotly
import plotly.graph_objs as go
from werkzeug.utils import secure_filename
import numpy as np
import pytz
from services.visualization_service import VisualizationService
from services.forecast_service import ForecastService
from services.commodity_insight_service import CommodityInsightService


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
    if isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif pd.isna(obj):  # Handle pandas NA values
        return None
    else:
        return obj

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
        
        # R² Score (0-1 range, higher is better)
        r2_normalized = max(0, min(100, max(r2_score, 0) * 100))
        
        # MAPE Score (0-100% range, lower is better)
        mape_score = max(0, min(100, (100 - min(mape, 100))))

        # UPDATED WEIGHTS: MAE(35%) + RMSE(25%) + R²(25%) + MAPE(15%)
        overall = (
            mae_score * 0.35 +
            rmse_score * 0.25 +
            r2_normalized * 0.25 +
            mape_score * 0.15
        )
        
        return max(0, min(100, overall))
        
    except Exception as e:
        print(f"⚠️ Error calculating overall score: {e}")
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

# Initialize services
forecast_service = ForecastService()
visualization_service = VisualizationService(forecast_service.data_handler)
commodity_service = CommodityInsightService()

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 1. MAIN ROUTES

@app.route('/')
def dashboard():
    """Main dashboard"""
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
    """Data Control page"""
    try:
        data_summary = forecast_service.data_handler.get_data_summary()
        df = forecast_service.data_handler.load_historical_data()
        
        historical_records = []
        if not df.empty:
            df_sorted = df.sort_values('Tanggal', ascending=False)
            historical_records = df_sorted[['Tanggal', 'Indikator_Harga']].to_dict('records')
        
        return render_template('data_control.html', 
                             data_summary=data_summary,
                             historical_records=historical_records,
                             page_title="Data Control")
    except Exception as e:
        flash(f"Error loading data control: {str(e)}", 'error')
        return render_template('data_control.html', 
                             data_summary={'total_records': 0},
                             historical_records=[],
                             page_title="Data Control")

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

# 2. DATA MANAGEMENT APIs

@app.route('/api/upload-data', methods=['POST'])
def upload_data():
    """Upload new data and trigger forecasting pipeline"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        if file and file.filename.lower().endswith(('.csv', '.xlsx')):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                if filename.lower().endswith('.csv'):
                    for encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            df = pd.read_csv(filepath, encoding=encoding)
                            print(f"📊 CSV loaded with {encoding} encoding")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        return jsonify({'success': False, 'message': 'Unable to read CSV file. Please check file encoding.'})
                else:
                    df = pd.read_excel(filepath)
                    
                print(f"📊 Loaded {len(df)} rows, {len(df.columns)} columns")
                
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error reading file: {str(e)}'})
            
            if df.empty:
                return jsonify({'success': False, 'message': 'Uploaded file is empty'})
            
            if len(df) < 3:
                return jsonify({
                    'success': False, 
                    'message': f'Insufficient data: {len(df)} rows found. Minimum 3 rows required for processing.'
                })
            
            forecast_weeks = int(request.form.get('forecast_weeks', 8))
            if not (4 <= forecast_weeks <= 12):
                forecast_weeks = 8
            
            try:
                result = forecast_service.process_new_data_and_forecast(df, forecast_weeks)
            except ValueError as ve:
                return jsonify({
                    'success': False, 
                    'message': f'Data validation error: {str(ve)}',
                    'error_type': 'validation_error'
                })
            except Exception as pe:
                return jsonify({
                    'success': False, 
                    'message': f'Processing error: {str(pe)}',
                    'error_type': 'processing_error'
                })
            
            try:
                os.remove(filepath)
            except:
                pass
            
            cleaned_result = clean_for_json(result)
            return jsonify(cleaned_result)
        
        return jsonify({'success': False, 'message': 'Invalid file format. Please upload CSV or Excel file.'})
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_response = clean_for_json({
            'success': False, 
            'message': f'Unexpected error: {str(e)}',
            'error_type': type(e).__name__
        })
        return jsonify(error_response)

@app.route('/api/add-single-record', methods=['POST'])
def add_single_record():
    """Add single IPH record to database"""
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

@app.route('/api/retrain-models', methods=['POST'])
def retrain_models():
    """Retrain models with existing data"""
    try:
        result = forecast_service.retrain_models_only()
        cleaned_result = clean_for_json(result)
        return jsonify(cleaned_result)
        
    except Exception as e:
        error_response = clean_for_json({
            'success': False, 
            'message': f'Error retraining models: {str(e)}'
        })
        return jsonify(error_response)

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

@app.route('/api/generate-forecast', methods=['POST'])
def generate_forecast():
    """Generate forecast with specified parameters"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        model_name = data.get('model_name')
        forecast_weeks = int(data.get('forecast_weeks', 8))
        
        print("=" * 60)
        print("🔮 GENERATE FORECAST DEBUG:")
        print(f"   📊 Requested weeks: {forecast_weeks}")
        print(f"   🤖 Requested model: {model_name}")
        print("=" * 60)
        
        if not (4 <= forecast_weeks <= 12):
            return jsonify({
                'success': False, 
                'message': 'Forecast weeks must be between 4 and 12'
            })
        
        result = forecast_service.get_current_forecast(model_name, forecast_weeks)
        
        print("=" * 60)
        print("📊 FORECAST RESULT DEBUG:")
        print(f"   ✅ Success: {result.get('success')}")
        if result.get('success'):
            forecast_data = result.get('forecast', {})
            print(f"   🤖 Model used: {forecast_data.get('model_name')}")
            print(f"   📊 Weeks generated: {forecast_data.get('weeks_forecasted')}")
            print(f"   📈 Data points: {len(forecast_data.get('data', []))}")
        else:
            print(f"   ❌ Error: {result.get('error')}")
        print("=" * 60)
        
        cleaned_result = clean_for_json(result)
        
        if cleaned_result.get('success'):
            cleaned_result['chart_refresh_token'] = datetime.now().isoformat()
            print(f"🔄 Chart refresh token: {cleaned_result['chart_refresh_token']}")
        
        return jsonify(cleaned_result)
        
    except Exception as e:
        print(f"❌ Generate forecast error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_response = clean_for_json({
            'success': False, 
            'message': f'Error generating forecast: {str(e)}'
        })
        return jsonify(error_response)

@app.route('/api/forecast-chart-data')
def forecast_chart_data():
    """Simple and reliable forecast chart data API"""
    try:
        print("📊 API /api/forecast-chart-data called")
        
        try:
            historical_df = forecast_service.data_handler.load_historical_data()
            print(f"📈 Loaded {len(historical_df)} historical records")
        except Exception as e:
            print(f"❌ Error loading historical data: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Historical data error: {str(e)}'
            })
        
        if historical_df.empty:
            return jsonify({
                'success': False,
                'error': 'No historical data available'
            })
        
        historical_df['Tanggal'] = pd.to_datetime(historical_df['Tanggal'])
        historical_df = historical_df.sort_values('Tanggal')
        
        historical_data = []
        for _, row in historical_df.iterrows():
            try:
                historical_data.append({
                    'date': row['Tanggal'].strftime('%Y-%m-%d'),
                    'value': float(row['Indikator_Harga'])
                })
            except Exception as e:
                print(f"⚠️ Error processing historical row: {e}")
                continue
        
        print(f"✅ Processed {len(historical_data)} historical points")
        
        forecast_data = []
        metadata = {
            'model_name': 'No Model',
            'weeks_forecasted': 0,
            'has_forecast': False
        }
        
        try:
            forecast_result = forecast_service.get_current_forecast()
            print(f"🔮 Forecast result success: {forecast_result.get('success', False)}")
            
            if forecast_result.get('success') and forecast_result.get('forecast', {}).get('data'):
                forecast_info = forecast_result['forecast']
                
                metadata.update({
                    'model_name': forecast_info.get('model_name', 'Unknown Model'),
                    'weeks_forecasted': forecast_info.get('weeks_forecasted', len(forecast_info.get('data', []))),
                    'has_forecast': True
                })
                
                for item in forecast_info['data']:
                    try:
                        forecast_data.append({
                            'date': item['Tanggal'][:10] if isinstance(item['Tanggal'], str) else item['Tanggal'].strftime('%Y-%m-%d'),
                            'prediction': float(item['Prediksi']),
                            'lower_bound': float(item.get('Batas_Bawah', item['Prediksi'])),
                            'upper_bound': float(item.get('Batas_Atas', item['Prediksi']))
                        })
                    except Exception as e:
                        print(f"⚠️ Error processing forecast row: {e}")
                        continue
                
                print(f"✅ Processed {len(forecast_data)} forecast points")
            else:
                print("ℹ️ No forecast data available")
                
        except Exception as e:
            print(f"⚠️ Error getting forecast: {str(e)}")
        
        result = {
            'success': True,
            'historical': historical_data,
            'forecast': forecast_data,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ API returning: historical={len(historical_data)}, forecast={len(forecast_data)}")
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"API Error: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'historical': [],
            'forecast': [],
            'metadata': {'model_name': 'Error', 'weeks_forecasted': 0}
        })

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
        print(f"❌ Error in model comparison API: {str(e)}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'metrics': []
        })

@app.route('/api/economic-alerts')
def get_economic_alerts():
    """Get real-time economic alerts"""
    print("🔍 API /api/economic-alerts called")
    try:
        alerts_data = forecast_service.get_real_economic_alerts()
        print(f"✅ API returning: success={alerts_data['success']}, alerts_count={len(alerts_data.get('alerts', []))}")
        return jsonify(alerts_data)
    except Exception as e:
        error_msg = f"API error: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': error_msg,
            'alerts': []
        })

# 4. VISUALIZATION APIs

@app.route('/api/visualization/moving-averages')
def api_moving_averages():
    """API for moving averages analysis"""
    try:
        timeframe = request.args.get('timeframe', '6M')
        result = visualization_service.calculate_moving_averages(timeframe)
        
        if not result['success']:
            return jsonify(result)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Moving averages API error: {str(e)}")
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
        result = visualization_service.analyze_volatility(timeframe)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/visualization/model-performance')
def api_model_performance():
    """API endpoint for model performance analysis"""
    try:
        timeframe = request.args.get('timeframe', '6M')
        result = visualization_service.analyze_model_performance(timeframe)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

# 5. COMMODITY APIs

@app.route('/api/commodity/current-week')
def api_commodity_current_week():
    """Enhanced current week commodity insights"""
    try:
        print("🔍 API: Loading current week insights...")
        result = commodity_service.get_current_week_insights()
        
        print(f"📊 Current week result structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"📊 Success status: {result.get('success')}")
        
        if result.get('success'):
            print(f"   📅 Period keys: {list(result.get('period', {}).keys())}")
            print(f"   📈 IPH analysis keys: {list(result.get('iph_analysis', {}).keys())}")
            print(f"   🏷️ Category analysis count: {len(result.get('category_analysis', {}))}")
        else:
            print(f"   ❌ Error: {result.get('message', 'Unknown error')}")
        
        if result.get('success') and not result.get('iph_analysis'):
            print("⚠️ Missing iph_analysis, creating fallback...")
            iph_value = result.get('iph_value', 0)
            result['iph_analysis'] = {
                'value': float(iph_value),
                'level': 'Unknown',
                'color': 'secondary',
                'direction': 'Unknown'
            }
        
        return jsonify(clean_for_json(result))
        
    except Exception as e:
        print(f"❌ API Error - current week insights: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify(clean_for_json({
            'success': False, 
            'error': str(e),
            'message': 'Failed to load current week insights. Please check if commodity data is available.',
            'error_details': str(e)
        }))

@app.route('/api/commodity/monthly-analysis')
def api_commodity_monthly():
    """Enhanced monthly commodity analysis"""
    try:
        month = request.args.get('month', '').strip()
        print(f"🔍 API: Loading monthly analysis for month: '{month}'")
        
        result = commodity_service.get_monthly_analysis(month if month else None)
        
        print(f"📊 Monthly analysis result structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"📊 Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"   📅 Month: {result.get('month')}")
            print(f"   📊 Analysis period keys: {list(result.get('analysis_period', {}).keys())}")
            print(f"   📈 IPH stats keys: {list(result.get('iph_statistics', {}).keys())}")
        else:
            print(f"   ❌ Error: {result.get('message')}")
        
        return jsonify(clean_for_json(result))
        
    except Exception as e:
        print(f"❌ API Error - monthly analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify(clean_for_json({
            'success': False, 
            'error': str(e),
            'message': 'Failed to load monthly analysis. Please check if commodity data is available.',
            'error_type': 'processing_error'
        }))

@app.route('/api/commodity/trends')
def api_commodity_trends():
    """Enhanced commodity trends"""
    try:
        commodity = request.args.get('commodity', '').strip()
        periods = int(request.args.get('periods', 4))
        
        if not (2 <= periods <= 24):
            periods = 4
        
        print(f"🔍 API: Loading commodity trends - periods: {periods}, commodity: '{commodity}'")
        
        result = commodity_service.get_commodity_trends(
            commodity if commodity else None, 
            periods
        )
        
        print(f"📊 Trends result structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"📊 Success: {result.get('success')}")
        
        if result.get('success'):
            trends_count = len(result.get('commodity_trends', {}))
            print(f"   📈 Found {trends_count} commodity trends")
            
            if result.get('commodity_trends'):
                first_trend = list(result['commodity_trends'].items())[0] if result['commodity_trends'] else None
                if first_trend:
                    trend_name, trend_data = first_trend
                    print(f"   🔍 First trend '{trend_name}' keys: {list(trend_data.keys())}")
        
        return jsonify(clean_for_json(result))
        
    except Exception as e:
        print(f"❌ API Error - commodity trends: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify(clean_for_json({
            'success': False, 
            'error': str(e),
            'message': 'Failed to load commodity trends'
        }))

@app.route('/api/commodity/seasonal')
def api_commodity_seasonal():
    """Enhanced seasonal commodity patterns"""
    try:
        print("🔍 API: Loading seasonal patterns...")
        
        result = commodity_service.get_seasonal_patterns()
        
        print(f"📊 Seasonal result structure: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"📊 Success: {result.get('success')}")
        
        if result.get('success'):
            patterns_count = len(result.get('seasonal_patterns', {}))
            print(f"   🗓️ Found {patterns_count} monthly patterns")
            
            if result.get('seasonal_patterns'):
                first_pattern = list(result['seasonal_patterns'].items())[0] if result['seasonal_patterns'] else None
                if first_pattern:
                    month_name, month_data = first_pattern
                    print(f"   🔍 First pattern '{month_name}' keys: {list(month_data.keys())}")
        
        return jsonify(clean_for_json(result))
        
    except Exception as e:
        print(f"❌ API Error - seasonal patterns: {str(e)}")
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
        
        print(f"🔍 API: Loading volatility alerts with threshold: {threshold}")
        
        result = commodity_service.get_alert_commodities(threshold)
        
        print(f"📊 Alerts result: success={result.get('success')}")
        if result.get('success'):
            alerts_count = len(result.get('alerts', []))
            print(f"   ⚠️ Found {alerts_count} alerts")
        
        return jsonify(clean_for_json(result))
    except Exception as e:
        print(f"❌ API Error - commodity alerts: {str(e)}")
        return jsonify(clean_for_json({
            'success': False, 
            'error': str(e),
            'message': 'Failed to load commodity alerts'
        }))

@app.route('/api/commodity/upload', methods=['POST'])
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
                print(f"📂 Processing commodity file: {filename}")
                
                if filename.lower().endswith('.csv'):
                    df = None
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            df = pd.read_csv(temp_path, encoding=encoding)
                            print(f"✅ CSV loaded successfully with {encoding} encoding")
                            break
                        except UnicodeDecodeError:
                            print(f"⚠️ Failed to load with {encoding} encoding, trying next...")
                            continue
                    
                    if df is None:
                        return jsonify({
                            'success': False, 
                            'message': 'Unable to read CSV file with any encoding. Please save as UTF-8 CSV.'
                        })
                else:
                    df = pd.read_excel(temp_path)
                    print("✅ Excel file loaded successfully")
                
                print(f"📊 Loaded {len(df)} rows, {len(df.columns)} columns")
                print(f"📋 Original columns: {list(df.columns)}")
                
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
                
                print(f"✅ Column mapping successful: {column_mapping}")
                
                df = df.dropna(how='all')
                
                commodity_path = commodity_service.commodity_data_path
                if request.form.get('backup_existing') == 'true':
                    if os.path.exists(commodity_path):
                        backup_path = commodity_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                        try:
                            import shutil
                            shutil.copy2(commodity_path, backup_path)
                            print(f"📦 Existing data backed up to: {backup_path}")
                        except Exception as backup_error:
                            print(f"⚠️ Backup failed: {backup_error}")
                
                os.makedirs(os.path.dirname(commodity_path), exist_ok=True)
                df.to_csv(commodity_path, index=False)
                
                commodity_service.commodity_cache = None
                commodity_service.last_cache_time = None
                
                print(f"✅ Commodity data saved to: {commodity_path}")
                
                try:
                    test_df = commodity_service.load_commodity_data()
                    if test_df.empty:
                        print("⚠️ Warning: Saved data appears to be empty after processing")
                except Exception as validation_error:
                    print(f"⚠️ Data validation warning: {validation_error}")
                
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
                print(f"❌ Processing error: {str(processing_error)}")
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
                    print(f"🗑️ Cleaned up temp file: {temp_path}")
                except:
                    pass
        
        return jsonify({
            'success': False, 
            'message': 'Invalid file format. Please upload CSV or Excel file.',
            'allowed_formats': ['.csv', '.xlsx']
        })
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
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
        print(f"❌ Commodity data status error: {str(e)}")
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
def export_data():
    """Export current data to CSV"""
    try:
        data_type = request.args.get('type', 'historical')
        
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

# UTILITY FUNCTIONS & CONTEXT PROCESSORS

@app.context_processor
def inject_datetime():
    """Inject datetime functions into templates"""
    return {
        'datetime': datetime,
        'now': datetime.now()
    }

# Legacy URL rule

app.add_url_rule('/upload', 'data_control', data_control)

# APPLICATION STARTUP
if __name__ == '__main__':
    print("🚀 Starting IPH Forecasting Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5000")
    print("📁 Data will be stored in: data/historical_data.csv")
    print("🤖 Models will be saved in: data/models/")
    app.run(debug=True, host='0.0.0.0', port=5000)