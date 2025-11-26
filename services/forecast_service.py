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
        Logic Peringatan Cerdas & Dinamis
        Menangani: Inflasi Tinggi, Deflasi, Volatilitas, Lonjakan Tiba-tiba, & Dominasi Komoditas.
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
                        'title': 'Menunggu Data', 
                        'description': 'Belum ada data yang cukup untuk analisis.',
                        'volatility_status': '-', 'volatility_desc': '-'
                    }
                }

            # 2. Preprocessing Data
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])
            df = df.sort_values('Tanggal').reset_index(drop=True)
            
            # Ambil data terbaru & sebelumnya
            latest_record = df.iloc[-1]
            latest_val = float(latest_record['Indikator_Harga'])
            latest_date = latest_record['Tanggal']
            
            prev_val = 0.0
            if len(df) >= 2:
                prev_val = float(df['Indikator_Harga'].iloc[-2])
            
            change = latest_val - prev_val
            
            # Statistik Window (30 Hari / 4 Minggu terakhir)
            recent_df = df.tail(4) 
            std_dev = recent_df['Indikator_Harga'].std() if len(recent_df) > 1 else 0.0
            avg_val = recent_df['Indikator_Harga'].mean()

            # -----------------------------------------
            # 3. LOGIC GENERATOR (The "Brain")
            # -----------------------------------------
            alerts = []
            recommendations = []
            
            # A. Analisis Level IPH (Thresholds)
            if latest_val > 3.0:
                alerts.append({
                    'title': 'Bahaya: Inflasi Sangat Tinggi',
                    'message': f'IPH mencapai **{latest_val:.2f}%**. Daya beli masyarakat terancam.',
                    'color': 'danger', 'icon': 'fa-fire-flame-curved'
                })
                recommendations.append({'icon': 'fa-shop', 'color': 'danger', 'title': 'Operasi Pasar Masif', 'text': 'Lakukan operasi pasar segera untuk menekan harga.'})
            
            elif latest_val > 1.5:
                alerts.append({
                    'title': 'Peringatan: Inflasi Meningkat',
                    'message': f'IPH di level **{latest_val:.2f}%**. Tren harga naik di atas wajar.',
                    'color': 'warning', 'icon': 'fa-arrow-trend-up'
                })
                recommendations.append({'icon': 'fa-truck-field', 'color': 'warning', 'title': 'Cek Distribusi', 'text': 'Pastikan tidak ada penimbunan atau hambatan distribusi.'})
            
            elif latest_val < -2.0:
                alerts.append({
                    'title': 'Peringatan: Deflasi Dalam',
                    'message': f'IPH turun ke **{latest_val:.2f}%**. Indikasi penurunan daya beli atau panen raya berlebih.',
                    'color': 'info', 'icon': 'fa-snowflake'
                })
                recommendations.append({'icon': 'fa-hand-holding-dollar', 'color': 'info', 'title': 'Serap Produk Petani', 'text': 'Bantu penyerapan hasil panen agar harga tidak anjlok.'})
            
            # B. Analisis Perubahan Cepat (Shock)
            if abs(change) > 1.0:
                direction = "Lonjakan" if change > 0 else "Kejatuhan"
                alerts.append({
                    'title': f'{direction} Harga Tiba-tiba',
                    'message': f'Perubahan drastis **{change:+.2f}%** dari minggu lalu. Cek faktor eksternal (cuaca/bencana).',
                    'color': 'warning', 'icon': 'fa-bolt'
                })

            # C. Analisis Volatilitas
            vol_status = "Rendah"
            vol_desc = "Pasar stabil."
            
            if std_dev > 1.5:
                vol_status = "Tinggi"
                vol_desc = f"Fluktuasi tajam (Std: {std_dev:.2f}). Harga tidak stabil."
                recommendations.append({'icon': 'fa-eye', 'color': 'danger', 'title': 'Monitoring Harian', 'text': 'Tingkatkan frekuensi pemantauan ke pasar.'})
            elif std_dev > 0.8:
                vol_status = "Sedang"
                vol_desc = f"Ada dinamika harga (Std: {std_dev:.2f})."
            
            # D. Analisis Komoditas (Integrasi Commodity Service)
            try:
                from services.commodity_insight_service import CommodityInsightService
                comm_service = CommodityInsightService()
                                
                # Gunakan metode get_full_commodity_insights dengan key bulan/tahun
                key = f"{latest_date.year}-{latest_date.month:02d}"
                comm_data = comm_service.get_full_commodity_insights(start_key=key, end_key=key)
                
                top_comm_name = "Tidak Ada Data"
                
                if comm_data['success'] and comm_data.get('trend_sparkline_data'):
                    # Ambil yang frekuensinya tertinggi atau impact terbesar (jika ada logic impact)
                    # Di sini kita pakai data pertama dari trend_sparkline_data (biasanya top freq)
                    top_item = comm_data['trend_sparkline_data'][0]
                    top_comm_name = top_item['name'].replace('_', ' ').title()
                    
                    alerts.append({
                        'title': 'Komoditas Pemicu Utama', 
                        'message': f'**{top_comm_name}** menjadi kontributor utama gejolak harga periode ini.', 
                        'color': 'primary', 
                        'icon': 'fa-basket-shopping'
                    })
                    
                    recommendations.insert(0, { # Taruh di paling atas
                        'icon': 'fa-magnifying-glass', 
                        'color': 'primary', 
                        'title': f'Fokus: {top_comm_name}', 
                        'text': f'Prioritaskan pemantauan stok dan harga **{top_comm_name}** di pasar.'
                    })
            except Exception as e:
                logger.warning(f"Commodity alert skip: {e}")

            # E. Status Aman (Jika tidak ada alert)
            if not alerts:
                alerts.append({
                    'title': 'Kondisi Pasar Stabil',
                    'message': f'IPH {latest_val:.2f}% berada dalam rentang wajar. Tidak ada gejolak berarti.',
                    'color': 'success', 'icon': 'fa-circle-check'
                })
                recommendations.append({
                    'icon': 'fa-clipboard-check', 'color': 'success', 
                    'title': 'Pertahankan Monitoring', 
                    'text': 'Lanjutkan pemantauan rutin mingguan.'
                })

            # 4. Konstruksi Narasi Utama (Blue Card)
            narrative = {}
            narrative['volatility_status'] = vol_status
            narrative['volatility_desc'] = vol_desc
            
            if latest_val > 0:
                narrative['title'] = "Tren Kenaikan Harga (Inflasi)"
                narrative['description'] = f"IPH saat ini **{latest_val:.2f}%**. Terjadi kenaikan sebesar **{abs(change):.2f}%** dibanding periode lalu."
            elif latest_val < 0:
                narrative['title'] = "Tren Penurunan Harga (Deflasi)"
                narrative['description'] = f"IPH saat ini **{latest_val:.2f}%**. Terjadi penurunan sebesar **{abs(change):.2f}%** dibanding periode lalu."
            else:
                narrative['title'] = "Harga Stabil"
                narrative['description'] = "Tidak ada perubahan harga (0%) dibanding periode dasar."

            return {
                'success': True,
                'alerts': alerts,
                'recommendations': recommendations,
                'statistics': {
                    'latest_value': latest_val,
                    'std': std_dev,
                    'mean': avg_val
                },
                'insight_narrative': narrative,
                'data_period': latest_date.strftime('%d %B %Y')
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