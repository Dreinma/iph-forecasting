import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime, timedelta

# Import service/model modules
from services.data_handler import DataHandler
from models.model_manager import ModelManager

# Configure logging
logger = logging.getLogger(__name__)

class ForecastService:
    """
    Service untuk menangani logika peramalan dan analisis data.
    Disesuaikan untuk Arsitektur Inference-Only (Render/Vercel).
    """
    
    def __init__(self):
        # Inisialisasi handler dan manager
        self.data_handler = DataHandler()
        # ModelManager sekarang hanya membaca dari DB/ONNX (tidak melatih)
        self.model_manager = ModelManager()
        
        self._latest_forecast = None
        self._alerts_cache = None
        self._alerts_cache_time = None
        
        logger.info("ForecastService initialized (Inference Mode)")

    def get_dashboard_data(self):
        """Get all data needed for dashboard display"""
        logger.debug("Collecting dashboard data")
        
        try:
            data_summary = self.data_handler.get_data_summary()
            model_summary = self.model_manager.get_model_performance_summary()
            best_model = self.model_manager.get_current_best_model()
            
            current_forecast = None
            if self._latest_forecast:
                logger.debug(f"Using latest forecast from memory: {self._latest_forecast['model_name']}")
                current_forecast = self._latest_forecast
            elif best_model:
                logger.debug("No latest forecast, using best model forecast")
                forecast_result = self.get_current_forecast(best_model['model_name'], 8)
                if forecast_result['success']:
                    current_forecast = forecast_result['forecast']
            
            training_history = self.model_manager.get_training_history_chart_data()
            
            dashboard_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data_summary': data_summary,
                'model_summary': model_summary,
                'best_model': best_model,
                'current_forecast': current_forecast,
                'training_history': training_history,
                'recent_backups': [], # Kosongkan list backup (Cloud environment)
                'system_status': self._get_system_status()
            }
            
            logger.debug("Dashboard data collected successfully")
            return dashboard_data
            
        except Exception as e:
            error_msg = f"Error collecting dashboard data: {str(e)}"
            logger.error(f"Pipeline error: {error_msg}", exc_info=True)
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'data_summary': {'total_records': 0}
            }

    def get_current_forecast(self, model_name=None, forecast_weeks=8, save_history=False):
        """
        Get forecast, save to DB for persistence (optional), and cache in memory.
        """
        logger.debug(f"Getting current forecast: model={model_name}, weeks={forecast_weeks}")
        
        try:
            if not model_name or model_name.strip() == '':
                best_model = self.model_manager.get_current_best_model()
                if not best_model:
                    return {
                        'success': False, 
                        'error': 'No trained models available. Please upload data first.'
                    }
                model_name = best_model['model_name']
            
            if not (4 <= forecast_weeks <= 12):
                return {'success': False, 'error': 'Forecast weeks must be between 4 and 12'}
            
            # 1. Generate forecast (Menggunakan Engine ONNX)
            forecast_df, model_performance, forecast_summary = self.model_manager.engine.generate_forecast(
                model_name, forecast_weeks
            )
            
            # 2. SIMPAN KE DATABASE (Opsional, hanya jika diminta)
            if save_history:
                logger.info("Saving forecast to database history...")
                self._save_forecast_to_database(forecast_df, model_name, forecast_summary, forecast_weeks, model_performance)

            # 3. Buat hasil JSON
            # Helper function local untuk cleaning data
            def clean(obj):
                if isinstance(obj, (np.integer, np.floating)): return float(obj)
                if isinstance(obj, np.ndarray): return obj.tolist()
                return obj

            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'forecast': {
                    'data': forecast_df.to_dict('records'),
                    'model_name': str(model_name),
                    'model_performance': model_performance,
                    'summary': forecast_summary,
                    'weeks_forecasted': int(forecast_weeks)
                }
            }
            
            # 4. Update Cache
            self._latest_forecast = result['forecast'].copy()
            
            return result
            
        except Exception as e:
            error_msg = f"Error generating forecast: {str(e)}"
            logger.error(f"Exception in get_current_forecast: {error_msg}", exc_info=True)
            return {
                'success': False, 
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

    def _save_forecast_to_database(self, forecast_df, model_name, summary, forecast_weeks, model_performance=None):
        """Save forecast to ForecastHistory database"""
        try:
            from database import db, ForecastHistory
            from flask_login import current_user
            
            forecast_data_list = []
            confidence_intervals_list = []
            
            for _, row in forecast_df.iterrows():
                forecast_data_list.append({
                    'date': str(row['Tanggal']),
                    'prediction': float(row['Prediksi']),
                    'lower_bound': float(row['Batas_Bawah']),
                    'upper_bound': float(row['Batas_Atas']),
                    'confidence_width': float(row.get('Confidence_Width', 0))
                })
                confidence_intervals_list.append({
                    'lower': float(row['Batas_Bawah']),
                    'upper': float(row['Batas_Atas'])
                })
            
            # Hapus argumen invalid (model_mae, dll)
            forecast_history = ForecastHistory(
                model_name=str(model_name),
                forecast_weeks=int(forecast_weeks),
                avg_prediction=float(summary.get('avg_prediction', 0)),
                trend=str(summary.get('trend', 'Stabil')),
                volatility=float(summary.get('volatility', 0)),
                min_prediction=float(summary.get('min_prediction', 0)),
                max_prediction=float(summary.get('max_prediction', 0)),
                forecast_data=json.dumps(forecast_data_list),
                confidence_intervals=json.dumps(confidence_intervals_list),
                data_points_used=len(forecast_df),
                created_by=current_user.username if hasattr(current_user, 'username') and current_user.is_authenticated else 'system'
            )
            
            db.session.add(forecast_history)
            db.session.commit()
            
        except ImportError:
            logger.debug("Database not available, skipping save")
        except Exception as e:
            logger.error(f"Error saving forecast to database: {e}", exc_info=True)
            db.session.rollback()

    def get_real_economic_alerts(self):
        """
        MODIFIED: Generate real alerts based on database data.
        Menangani kasus Inflasi, Deflasi, dan Volatilitas secara dinamis.
        """
        try:
            # 1. Load Data Real dari Database
            df = self.data_handler.load_historical_data()
            
            # Fallback jika data kosong
            if df.empty:
                 return {
                    'success': True, 
                    'alerts': [],
                    'recommendations': [],
                    'statistics': {'latest_value': 0, 'std': 0, 'mean': 0},
                    'insight_narrative': {
                        'title': 'Data Kosong', 'description': 'Silakan upload data di menu Data Management.',
                        'volatility_status': '-', 'volatility_desc': '-'
                    }
                }

            # 2. Proses Data (Pastikan pandas imported!)
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])
            df = df.sort_values('Tanggal').reset_index(drop=True)
            
            latest_val = float(df['Indikator_Harga'].iloc[-1])
            # Handle jika data < 2
            if len(df) >= 2:
                prev_val = float(df['Indikator_Harga'].iloc[-2])
                change = latest_val - prev_val
            else:
                prev_val = latest_val
                change = 0.0
            
            # Statistik
            recent_df = df.tail(14)
            std_dev = recent_df['Indikator_Harga'].std() if len(recent_df) > 1 else 0.0
            avg_val = recent_df['Indikator_Harga'].mean()

            # 3. Logika Insight (Narasi)
            narrative = {}
            if abs(change) < 0.1:
                narrative['title'] = "Kondisi Pasar Stabil"
                narrative['description'] = f"IPH relatif datar di level **{latest_val:.2f}%**. Tidak ada gejolak harga yang signifikan."
            elif change > 0:
                narrative['title'] = "Tren Kenaikan Harga"
                narrative['description'] = f"Terjadi kenaikan IPH sebesar **{abs(change):.2f}%** menjadi **{latest_val:.2f}%**."
            else:
                narrative['title'] = "Tren Penurunan Harga"
                narrative['description'] = f"Terjadi penurunan IPH sebesar **{abs(change):.2f}%** menjadi **{latest_val:.2f}%**."

            # Status Volatilitas
            if std_dev > 1.5:
                narrative['volatility_status'] = "Tinggi"
                narrative['volatility_desc'] = f"Fluktuasi harga sangat tajam (Std Dev: {std_dev:.2f})."
            elif std_dev > 0.5:
                narrative['volatility_status'] = "Sedang"
                narrative['volatility_desc'] = f"Dinamika harga wajar (Std Dev: {std_dev:.2f})."
            else:
                narrative['volatility_status'] = "Rendah"
                narrative['volatility_desc'] = "Pergerakan harga stabil."

            # 4. Generate Alerts
            alerts = []
            if latest_val > 3.0:
                alerts.append({'title': 'Level Inflasi Tinggi', 'message': f'IPH {latest_val:.2f}% melebihi batas wajar.', 'color': 'danger', 'icon': 'fa-fire'})
            elif latest_val < -2.0:
                alerts.append({'title': 'Deflasi Dalam', 'message': f'IPH turun hingga {latest_val:.2f}%.', 'color': 'warning', 'icon': 'fa-snowflake'})

            if change > 0.5:
                alerts.append({'title': 'Lonjakan Harga', 'message': f'Kenaikan {change:.2f}% periode ini.', 'color': 'warning', 'icon': 'fa-arrow-trend-up'})
            
            # Analisis Komoditas (Safe Import & Logic)
            try:
                from services.commodity_insight_service import CommodityInsightService
                comm_service = CommodityInsightService()
                # Gunakan key terbaru yyyy-mm
                latest_date = df['Tanggal'].iloc[-1]
                key = f"{latest_date.year}-{latest_date.month:02d}"
                
                # PANGGIL FUNGSI BARU: get_full_commodity_insights
                comm_data = comm_service.get_full_commodity_insights(start_key=key, end_key=key)
                
                if comm_data['success']:
                     # Cek Frekuensi Chart Data
                     if comm_data.get('frequency_chart_data') and comm_data['frequency_chart_data'].get('x'):
                         # Ambil komoditas pertama (paling sering muncul)
                         top_comm_name = comm_data['frequency_chart_data']['x'][0]
                         # Format nama agar cantik (Title Case)
                         top_comm_title = top_comm_name.replace('_', ' ').title()
                         alerts.append({
                             'title': 'Komoditas Dominan', 
                             'message': f'{top_comm_title} paling sering mempengaruhi pasar periode ini.', 
                             'color': 'info', 
                             'icon': 'fa-basket-shopping'
                         })
            except Exception as e:
                logger.warning(f"Commodity insight skip: {e}")

            if not alerts:
                alerts.append({'title': 'Kondisi Normal', 'message': 'Indikator aman.', 'color': 'success', 'icon': 'fa-check-circle'})

            # 5. Generate Rekomendasi
            recommendations = []
            if latest_val > 0.5:
                recommendations.append({'icon': 'fa-shop', 'color': 'warning', 'title': 'Operasi Pasar', 'text': 'Lakukan **operasi pasar** segera.'})
            elif latest_val < -0.5:
                recommendations.append({'icon': 'fa-users', 'color': 'info', 'title': 'Serap Produk', 'text': 'Bantu penyerapan panen petani.'})
            
            if std_dev > 1.0:
                recommendations.append({'icon': 'fa-eye', 'color': 'danger', 'title': 'Pantau Harian', 'text': 'Tingkatkan frekuensi monitoring.'})
            else:
                recommendations.append({'icon': 'fa-clipboard-check', 'color': 'success', 'title': 'Pantau Berkala', 'text': 'Lanjutkan monitoring rutin.'})
                
            # Tambahkan rekomendasi komoditas jika ada
            if 'top_comm_title' in locals():
                 recommendations.append({
                    'icon': 'fa-magnifying-glass', 
                    'color': 'primary', 
                    'title': f'Fokus: {top_comm_title}', 
                    'text': f'Perhatikan distribusi dan stok **{top_comm_title}**.'
                })

            return {
                'success': True,
                'alerts': alerts,
                'recommendations': recommendations,
                'statistics': {
                    'latest_value': latest_val,
                    'std': std_dev,
                    'mean': avg_val
                },
                'insight_narrative': narrative
            }

        except Exception as e:
            logger.error(f"Alert gen error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _get_system_status(self):
        """Get simple system status"""
        return {
            'status': 'online',
            'database': 'connected',
            'last_check': datetime.now().isoformat()
        }