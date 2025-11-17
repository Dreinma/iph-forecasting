import os
import logging
from models.model_manager import ModelManager  # Perbaikan: import dari models, bukan services
from .data_handler import DataHandler
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import json
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

def clean_data_for_json(obj):
    """Clean data untuk JSON serialization dengan handling NaN/Inf dan pandas NA"""
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            cleaned[key] = clean_data_for_json(value)
        return cleaned
    elif isinstance(obj, list):
        return [clean_data_for_json(item) for item in obj]
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None  # Replace NaN/Inf with null
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif pd.isna(obj):  # This handles pandas NA, NaT, None, etc.
        return None
    elif hasattr(obj, 'dtype') and pd.api.types.is_numeric_dtype(obj.dtype):
        # Handle pandas numeric types
        if pd.isna(obj):
            return None
        return float(obj) if isinstance(obj, (np.floating, float)) else int(obj)
    elif str(type(obj)).startswith('<class \'pandas.'):
        # Generic pandas type handling
        if pd.isna(obj):
            return None
        return str(obj)
    else:
        return obj

class ForecastService:
    """Main service for handling forecasting operations"""
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.data_handler = DataHandler()
        self._latest_forecast = None
        self._alerts_cache = None
        self._alerts_cache_time = None
    
    def _save_forecast_to_database(self, forecast_df, model_name, summary, forecast_weeks, model_performance=None):
        """Save forecast to ForecastHistory database untuk persistensi"""
        try:
            from database import db, ForecastHistory
            from flask_login import current_user
            
            # Prepare forecast data as JSON
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
            
            # Calculate trend
            predictions = [f['prediction'] for f in forecast_data_list]
            if len(predictions) >= 2:
                if predictions[-1] > predictions[0]:
                    trend = 'up'
                elif predictions[-1] < predictions[0]:
                    trend = 'down'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'

            perf = model_performance or {}
            
            # Create ForecastHistory record
            forecast_history = ForecastHistory(
                model_name=str(model_name),
                forecast_weeks=int(forecast_weeks), 
                forecast_data=forecast_data_list,
                confidence_intervals=confidence_intervals_list,
                avg_prediction=float(summary['avg_prediction']),
                trend=str(trend),
                min_value=float(summary['min_prediction']),
                max_value=float(summary['max_prediction']),
                validation_mae=float(perf.get('mae', 0)),
                validation_rmse=float(perf.get('rmse', 0)),
                data_points_used=len(forecast_df),
                created_by=current_user.username if hasattr(current_user, 'username') and current_user.is_authenticated else 'system'
            )
            
            db.session.add(forecast_history)
            db.session.commit()
            
            logger.debug(f"Forecast saved to database (ID: {forecast_history.id})")
            
        except ImportError:
            # Database not available (testing or standalone mode)
            logger.debug("Database not available, skipping database save")
        except Exception as e:
            logger.error(f"Error saving forecast to database: {e}")
            # Don't fail the whole process if DB save fails

    def get_current_forecast(self, model_name=None, forecast_weeks=8):
        """Get forecast using current best model or specified model"""
        logger.debug(f"Getting current forecast: model={model_name}, weeks={forecast_weeks}")
        
        try:
            original_model_name = model_name  # Store original request
            
            # Determine which model to use
            if not model_name or model_name.strip() == '':
                best_model = self.model_manager.get_current_best_model()
                if not best_model:
                    return {
                        'success': False, 
                        'error': 'No trained models available. Please upload data first.'
                    }
                model_name = best_model['model_name']
                logger.debug(f"Using best model: '{model_name}'")
            else:
                logger.debug(f"Using specified model: '{model_name}'")
                
                # Validate that the specified model exists
                available_models = self.model_manager.engine.get_available_models()
                model_names = [m['name'].replace(' ', '_') for m in available_models]
                
                logger.debug(f"Available models: {model_names}")
                
                if model_name not in model_names:
                    logger.warning(f"Model '{model_name}' not found in available models")
                    return {
                        'success': False,
                        'error': f'Model "{model_name}" not found. Available models: {", ".join(model_names)}'
                    }
                else:
                    logger.debug(f"Model '{model_name}' found in available models")
            
            # Validate forecast weeks
            if not (4 <= forecast_weeks <= 12):
                return {
                    'success': False,
                    'error': 'Forecast weeks must be between 4 and 12'
                }
            
            logger.debug(f"Calling engine.generate_forecast: model='{model_name}', weeks={forecast_weeks}")
            
            # Generate forecast
            forecast_df, model_performance, forecast_summary = self.model_manager.engine.generate_forecast(
                model_name, forecast_weeks
            )
            
            logger.debug(f"Forecast generated: shape={forecast_df.shape}")
            
            self._save_forecast_to_database(forecast_df, model_name, forecast_summary, forecast_weeks, model_performance)

            # Clean forecast data for JSON serialization
            forecast_data_clean = []
            for record in forecast_df.to_dict('records'):
                clean_record = {}
                for key, value in record.items():
                    if key == 'Tanggal':
                        # Ensure Tanggal is string
                        if isinstance(value, pd.Timestamp):
                            clean_record[key] = value.strftime('%Y-%m-%d')
                        else:
                            clean_record[key] = str(value)
                    elif isinstance(value, (np.floating, float)):
                        if np.isnan(value) or np.isinf(value):
                            clean_record[key] = None
                        else:
                            clean_record[key] = float(value)
                    elif isinstance(value, (np.integer, int)):
                        clean_record[key] = int(value)
                    elif isinstance(value, np.bool_):
                        clean_record[key] = bool(value)
                    else:
                        clean_record[key] = value
                forecast_data_clean.append(clean_record)
            
            logger.debug(f"Cleaned forecast: {len(forecast_data_clean)} records")
            
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'forecast': {
                    'data': forecast_data_clean,
                    'model_name': str(model_name),  # Ensure this is the actual model used
                    'model_performance': {
                        'mae': float(model_performance['mae']) if not np.isnan(model_performance['mae']) else 0.0,
                        'rmse': float(model_performance['rmse']) if not np.isnan(model_performance['rmse']) else 0.0,
                        'r2_score': float(model_performance['r2_score']) if not np.isnan(model_performance['r2_score']) else 0.0,
                        'training_time': float(model_performance['training_time'])
                    },
                    'summary': {
                        'avg_prediction': float(forecast_summary['avg_prediction']) if not np.isnan(forecast_summary['avg_prediction']) else 0.0,
                        'trend': str(forecast_summary['trend']),
                        'volatility': float(forecast_summary['volatility']) if not np.isnan(forecast_summary['volatility']) else 0.0,
                        'min_prediction': float(forecast_summary['min_prediction']) if not np.isnan(forecast_summary['min_prediction']) else 0.0,
                        'max_prediction': float(forecast_summary['max_prediction']) if not np.isnan(forecast_summary['max_prediction']) else 0.0
                    },
                    'weeks_forecasted': int(forecast_weeks)
                }
            }
            
            #  PERBAIKAN UTAMA: Simpan forecast terbaru di memory
            self._latest_forecast = result['forecast'].copy()
            logger.debug(f"Latest forecast saved in memory: {self._latest_forecast['model_name']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error generating forecast: {str(e)}"
            logger.error(f"Exception in get_current_forecast: {error_msg}")
            
            import traceback
            traceback.print_exc()
            
            return {
                'success': False, 
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
            
    def get_dashboard_data(self):
        """Get all data needed for dashboard display"""
        logger.debug("Collecting dashboard data")
        
        try:
            # Get data summary
            data_summary = self.data_handler.get_data_summary()
            
            # Get model performance summary
            model_summary = self.model_manager.get_model_performance_summary()
            
            # Get current best model
            best_model = self.model_manager.get_current_best_model()
            
            #  PERBAIKAN UTAMA: Prioritaskan latest forecast dari memory
            current_forecast = None
            if self._latest_forecast:
                logger.debug(f"Using latest forecast from memory: {self._latest_forecast['model_name']}")
                current_forecast = self._latest_forecast
            elif best_model:
                logger.debug("No latest forecast, using best model forecast")
                forecast_result = self.get_current_forecast(best_model['model_name'], 8)
                if forecast_result['success']:
                    current_forecast = forecast_result['forecast']
            
            # Get training history for charts
            training_history = self.model_manager.get_training_history_chart_data()
                        
            dashboard_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data_summary': data_summary,
                'model_summary': model_summary,
                'best_model': best_model,
                'current_forecast': current_forecast,
                'training_history': training_history,
                'recent_backups': [],
                'system_status': self._get_system_status()
            }
            
            logger.debug("Dashboard data collected successfully")
            return dashboard_data
            
        except Exception as e:
            error_msg = f"Error collecting dashboard data: {str(e)}"
            logger.error(f"Pipeline error: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'data_summary': {'total_records': 0}
            }
    
    def _get_system_status(self):
        """Get current system status"""
        try:
            # Check data availability
            data_summary = self.data_handler.get_data_summary()
            has_data = data_summary['total_records'] > 0
            
            # Check model availability
            best_model = self.model_manager.get_current_best_model()
            has_models = best_model is not None
            
            # Check forecast availability
            has_forecast = False
            if has_models:
                available_models = self.model_manager.engine.get_available_models()
                has_forecast = len(available_models) > 0
            
            status = {
                'has_data': has_data,
                'has_models': has_models,
                'has_forecast': has_forecast,
                'data_records': data_summary['total_records'],
                'ready_for_use': has_data and has_models and has_forecast
            }
            
            if status['ready_for_use']:
                status['status_message'] = "System ready for forecasting"
                status['status_level'] = "success"
            elif has_data and has_models:
                status['status_message'] = "System ready, forecast can be generated"
                status['status_level'] = "info"
            elif has_data:
                status['status_message'] = "Data available, models need training"
                status['status_level'] = "warning"
            else:
                status['status_message'] = "Please upload data to begin"
                status['status_level'] = "danger"
            
            return status
            
        except Exception as e:
            return {
                'has_data': False,
                'has_models': False,
                'has_forecast': False,
                'ready_for_use': False,
                'status_message': f"System error: {str(e)}",
                'status_level': "danger"
            }
    
    def get_model_comparison_data(self):
        """Get data for model comparison visualization"""
        try:
            model_summary = self.model_manager.get_model_performance_summary()
            training_history = self.model_manager.get_training_history_chart_data()
            
            return {
                'success': True,
                'model_summary': model_summary,
                'training_history': training_history,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error getting comparison data: {str(e)}"
            }

    def clear_latest_forecast(self):
        """Clear latest forecast from memory (useful for testing or reset)"""
        self._latest_forecast = None
        logger.debug("Latest forecast cleared from memory")
        
    def get_latest_forecast_info(self):
        """Get info about latest forecast in memory (for debugging)"""
        if self._latest_forecast:
            return {
                'has_latest': True,
                'model_name': self._latest_forecast.get('model_name'),
                'weeks_forecasted': self._latest_forecast.get('weeks_forecasted'),
                'data_points': len(self._latest_forecast.get('data', [])),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'has_latest': False,
                'message': 'No latest forecast in memory'
            }
        
    def get_statistical_alerts(self):
        """Generate alerts based on statistical boundaries"""
        try:
            df = self.data_handler.load_historical_data()
            if df.empty or len(df) < 10:
                return {'success': False, 'alerts': []}
            
            # Calculate statistical boundaries
            recent_data = df.tail(30)  # Last 30 records
            mean_val = recent_data['Indikator_Harga'].mean()
            std_val = recent_data['Indikator_Harga'].std()
            
            # Statistical thresholds
            upper_2sigma = mean_val + 2 * std_val  # 95% confidence
            lower_2sigma = mean_val - 2 * std_val
            upper_3sigma = mean_val + 3 * std_val  # 99.7% confidence  
            lower_3sigma = mean_val - 3 * std_val
            
            # Latest value
            latest_value = df['Indikator_Harga'].iloc[-1]
            latest_date = df['Tanggal'].iloc[-1]
            
            alerts = []
            
            # Critical alerts (3-sigma rule)
            if latest_value > upper_3sigma:
                alerts.append({
                    'type': 'critical',
                    'title': 'IPH Melampaui Batas Kritis Atas',
                    'message': f'IPH {latest_value:.2f}% melampaui batas 3-sigma ({upper_3sigma:.2f}%)',
                    'value': latest_value,
                    'threshold': upper_3sigma,
                    'date': latest_date.strftime('%Y-%m-%d'),
                    'severity': 'critical'
                })
            elif latest_value < lower_3sigma:
                alerts.append({
                    'type': 'critical', 
                    'title': 'IPH Melampaui Batas Kritis Bawah',
                    'message': f'IPH {latest_value:.2f}% melampaui batas 3-sigma ({lower_3sigma:.2f}%)',
                    'value': latest_value,
                    'threshold': lower_3sigma,
                    'date': latest_date.strftime('%Y-%m-%d'),
                    'severity': 'critical'
                })
            
            # Warning alerts (2-sigma rule)
            elif latest_value > upper_2sigma:
                alerts.append({
                    'type': 'warning',
                    'title': 'IPH Mendekati Batas Atas',
                    'message': f'IPH {latest_value:.2f}% mendekati batas 2-sigma ({upper_2sigma:.2f}%)',
                    'value': latest_value,
                    'threshold': upper_2sigma,
                    'date': latest_date.strftime('%Y-%m-%d'),
                    'severity': 'warning'
                })
            elif latest_value < lower_2sigma:
                alerts.append({
                    'type': 'warning',
                    'title': 'IPH Mendekati Batas Bawah', 
                    'message': f'IPH {latest_value:.2f}% mendekati batas 2-sigma ({lower_2sigma:.2f}%)',
                    'value': latest_value,
                    'threshold': lower_2sigma,
                    'date': latest_date.strftime('%Y-%m-%d'),
                    'severity': 'warning'
                })
            
            # Volatility check
            recent_volatility = recent_data['Indikator_Harga'].rolling(7).std().iloc[-1]
            avg_volatility = df['Indikator_Harga'].rolling(7).std().mean()
            
            if recent_volatility > avg_volatility * 1.5:
                alerts.append({
                    'type': 'info',
                    'title': 'Volatilitas Meningkat',
                    'message': f'Volatilitas 7-hari ({recent_volatility:.3f}%) meningkat 50% dari rata-rata',
                    'value': recent_volatility,
                    'threshold': avg_volatility * 1.5,
                    'date': latest_date.strftime('%Y-%m-%d'),
                    'severity': 'info'
                })
            
            # Trend change detection
            if len(df) >= 5:
                recent_trend = df['Indikator_Harga'].tail(5).diff().mean()
                if abs(recent_trend) > std_val * 0.5:
                    trend_direction = "naik" if recent_trend > 0 else "turun"
                    alerts.append({
                        'type': 'info',
                        'title': f'Deteksi Perubahan Trend',
                        'message': f'Trend {trend_direction} signifikan terdeteksi dalam 5 periode terakhir',
                        'value': recent_trend,
                        'threshold': std_val * 0.5,
                        'date': latest_date.strftime('%Y-%m-%d'),
                        'severity': 'info'
                    })
            
            return {
                'success': True,
                'alerts': alerts,
                'statistics': {
                    'mean': float(mean_val),
                    'std': float(std_val),
                    'upper_2sigma': float(upper_2sigma),
                    'lower_2sigma': float(lower_2sigma),
                    'upper_3sigma': float(upper_3sigma),
                    'lower_3sigma': float(lower_3sigma),
                    'latest_value': float(latest_value),
                    'volatility': float(recent_volatility)
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'alerts': []}
        
    def get_historical_alerts(self, days=7):
        """Get historical alerts (past alert records)"""
        try:
            # Simulate historical alerts based on data analysis
            df = self.data_handler.load_historical_data()
            if df.empty:
                return {'success': False, 'alerts': []}
            
            # Get recent data for analysis
            recent_df = df.tail(days * 2)  # More data for better analysis
            
            # Calculate statistical boundaries
            mean_val = df['Indikator_Harga'].mean()
            std_val = df['Indikator_Harga'].std()
            upper_2sigma = mean_val + 2 * std_val
            lower_2sigma = mean_val - 2 * std_val
            upper_3sigma = mean_val + 3 * std_val
            lower_3sigma = mean_val - 3 * std_val
            
            historical_alerts = []
            
            # Analyze each data point for historical alerts
            for _, row in recent_df.iterrows():
                date = row['Tanggal']
                value = row['Indikator_Harga']
                
                # Skip if too old
                days_ago = (datetime.now() - pd.to_datetime(date)).days
                if days_ago > days:
                    continue
                
                alert_type = None
                severity = None
                title = None
                message = None
                
                # Determine alert based on statistical boundaries
                if value > upper_3sigma:
                    alert_type = 'threshold'
                    severity = 'critical'
                    title = 'IPH Melampaui Batas Kritis Atas'
                    message = f'IPH mencapai {value:.2f}%, melampaui batas 3-sigma ({upper_3sigma:.2f}%)'
                elif value < lower_3sigma:
                    alert_type = 'threshold'
                    severity = 'critical'
                    title = 'IPH Melampaui Batas Kritis Bawah'
                    message = f'IPH turun ke {value:.2f}%, melampaui batas 3-sigma ({lower_3sigma:.2f}%)'
                elif value > upper_2sigma:
                    alert_type = 'threshold'
                    severity = 'warning'
                    title = 'IPH Mendekati Batas Atas'
                    message = f'IPH mencapai {value:.2f}%, mendekati batas 2-sigma ({upper_2sigma:.2f}%)'
                elif value < lower_2sigma:
                    alert_type = 'threshold'
                    severity = 'warning'
                    title = 'IPH Mendekati Batas Bawah'
                    message = f'IPH turun ke {value:.2f}%, mendekati batas 2-sigma ({lower_2sigma:.2f}%)'
                
                if alert_type:
                    historical_alerts.append({
                        'id': len(historical_alerts) + 1,
                        'type': alert_type,
                        'severity': severity,
                        'title': title,
                        'message': message,
                        'timestamp': date.isoformat() if hasattr(date, 'isoformat') else str(date),
                        'value': float(value),
                        'days_ago': days_ago,
                        'acknowledged': days_ago > 1  # Auto-acknowledge old alerts
                    })
            
            # Sort by timestamp (newest first)
            historical_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'alerts': historical_alerts[:20],  # Limit to 20 most recent
                'total_alerts': len(historical_alerts)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'alerts': []}
            
    def get_real_economic_alerts(self):
        """
        MODIFIED: Generate real-time economic alerts, statistics, and dynamic recommendations.
        """
        try:
            current_time = datetime.now()
            # Cek cache
            if (self._alerts_cache and self._alerts_cache_time and 
                (current_time - self._alerts_cache_time).seconds < 300): # Cache 5 menit
                logger.debug("Using cached alerts and recommendations")
                return self._alerts_cache
            
            logger.debug("Generating fresh alerts and recommendations")
            alerts = []
            recommendations = [] # List baru untuk rekomendasi
            
            # 1. Load Data
            df = self.data_handler.load_historical_data()
            if df.empty or len(df) < 10:
                return {'success': False, 'alerts': [], 'recommendations': [], 'statistics': {}, 'message': 'Insufficient data'}
            
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])
            df = df.sort_values('Tanggal').reset_index(drop=True)
            
            latest_iph = df['Indikator_Harga'].iloc[-1]
            latest_date = df['Tanggal'].iloc[-1]
            
            # 2. Analisis Statistik & Volatilitas
            mean_iph = df['Indikator_Harga'].mean()
            std_iph = df['Indikator_Harga'].std()
            upper_2sigma = mean_iph + 2 * std_iph
            lower_2sigma = mean_iph - 2 * std_iph
            
            # Statistik untuk card atas
            recent_volatility = df['Indikator_Harga'].tail(14).std()
            historical_volatility = df['Indikator_Harga'].std()
            trend_4_minggu = df['Indikator_Harga'].tail(4).mean()

            statistics = {
                'latest_value': float(latest_iph),
                'std': float(recent_volatility),
                'mean': float(trend_4_minggu)
            }

            # 3. Get Forecast Data (untuk rekomendasi)
            forecast_data = None
            forecast_summary = None
            try:
                forecast_result = self.get_current_forecast()
                if forecast_result['success']:
                    forecast_data = forecast_result['forecast']['data']
                    forecast_summary = forecast_result['forecast']['summary']
            except Exception as e:
                logger.warning(f"Could not load forecast data for alerts: {e}")

            # 4. Get Commodity Data (untuk rekomendasi)
            comm_insights = None
            try:
                # Kita panggil commodity service untuk data minggu ini
                from services.commodity_insight_service import CommodityInsightService
                comm_service = CommodityInsightService() # Asumsi path default
                comm_insights = comm_service.get_current_week_insights()
            except Exception as e:
                logger.warning(f"Could not load commodity insights for alerts: {e}")

            # BUAT ALERTS (Logika lama Anda, bisa dipertahankan)
            #             
            # (Alert 1: Statistical Boundary)
            if latest_iph > upper_2sigma:
                alerts.append({
                    'type': 'boundary_warning',
                    'severity': 'warning',
                    'icon': 'fa-arrow-up',
                    'color': 'warning',
                    'title': 'IPH Mendekati Batas Atas Statistik (2-Sigma)',
                    'message': f'IPH saat ini ({latest_iph:.3f}%) berada di atas batas wajar ({upper_2sigma:.3f}%).',
                    'date': latest_date.strftime('%d/%m/%Y'),
                    'priority': 'medium'
                })
            elif latest_iph < lower_2sigma:
                 alerts.append({
                    'type': 'boundary_warning',
                    'severity': 'warning',
                    'icon': 'fa-arrow-down',
                    'color': 'info',
                    'title': 'IPH Mendekati Batas Bawah Statistik (2-Sigma)',
                    'message': f'IPH saat ini ({latest_iph:.3f}%) berada di bawah batas wajar ({lower_2sigma:.3f}%).',
                    'date': latest_date.strftime('%d/%m/%Y'),
                    'priority': 'medium'
                })
            
            # (Alert 2: Menambahkan alert dari commodity insights jika ada)
            if comm_insights and comm_insights['success']:
                 # Ambil 2 komoditas teratas
                top_pos = comm_insights['commodity_impacts'].get('significant_positive', [])
                top_neg = comm_insights['commodity_impacts'].get('significant_negative', [])
                
                if top_pos:
                    c = top_pos[0]
                    alerts.append({
                        'type': 'commodity', 'severity': 'info', 'icon': 'fa-seedling', 'color': 'danger',
                        'title': f"Pendorong Inflasi: {c['name'].replace('_', ' ').title()}",
                        'message': f"Komoditas {c['name'].replace('_', ' ').title()} berkontribusi signifikan ({c['impact']:.2f}%) terhadap IPH minggu ini.",
                        'date': latest_date.strftime('%d/%m/%Y'), 'priority': 'medium'
                    })
                if top_neg:
                    c = top_neg[0]
                    alerts.append({
                        'type': 'commodity', 'severity': 'info', 'icon': 'fa-leaf', 'color': 'success',
                        'title': f"Pendorong Deflasi: {c['name'].replace('_', ' ').title()}",
                        'message': f"Komoditas {c['name'].replace('_', ' ').title()} menahan IPH minggu ini ({c['impact']:.2f}%).",
                        'date': latest_date.strftime('%d/%m/%Y'), 'priority': 'medium'
                    })

            # BUAT REKOMENDASI 

            # Rekomendasi 1: Berdasarkan Tren Prediksi
            if forecast_data and forecast_summary:
                if forecast_summary['trend'] == 'Naik' and forecast_summary['avg_prediction'] > 0.5:
                    recommendations.append({
                        'icon': 'fa-arrow-trend-up', 'color': 'danger',
                        'title': 'Antisipasi Tren Inflasi',
                        'text': f"Model memprediksi tren IPH akan **naik** dalam {len(forecast_data)} minggu ke depan (rata-rata {forecast_summary['avg_prediction']:.2f}%). Pertimbangkan langkah-langkah stabilisasi harga."
                    })
                elif forecast_summary['trend'] == 'Turun' and forecast_summary['avg_prediction'] < -0.5:
                    recommendations.append({
                        'icon': 'fa-arrow-trend-down', 'color': 'success',
                        'title': 'Tren Deflasi Terprediksi',
                        'text': f"Model memprediksi tren IPH akan **turun** dalam {len(forecast_data)} minggu ke depan (rata-rata {forecast_summary['avg_prediction']:.2f}%). Awasi agar deflasi tidak terlalu dalam."
                    })
                else:
                    recommendations.append({
                        'icon': 'fa-arrows-left-right', 'color': 'primary',
                        'title': 'Kondisi Harga Diprediksi Stabil',
                        'text': f"Model memprediksi IPH akan relatif stabil ({forecast_summary['avg_prediction']:.2f}%). Lanjutkan monitoring rutin."
                    })

            # Rekomendasi 2: Berdasarkan Volatilitas
            if recent_volatility > historical_volatility * 1.5:
                recommendations.append({
                    'icon': 'fa-wave-square', 'color': 'warning',
                    'title': 'Waspada Volatilitas Tinggi',
                    'text': f"Volatilitas harga 14 hari terakhir ({recent_volatility:.2f}) **lebih tinggi {((recent_volatility/historical_volatility)-1)*100:.0f}%** dibanding rata-rata historis ({historical_volatility:.2f}). Pasar sedang tidak stabil."
                })
                
            # Rekomendasi 3: Berdasarkan Komoditas (Jika ada)
            if comm_insights and comm_insights['success']:
                top_inflasi = comm_insights['commodity_impacts'].get('significant_positive', [])
                if top_inflasi:
                    top_comm = top_inflasi[0]
                    recommendations.append({
                        'icon': 'fa-seedling', 'color': 'danger',
                        'title': 'Fokus pada Komoditas Pendorong Inflasi',
                        'text': f"**{top_comm['name'].replace('_', ' ').title()}** menjadi pendorong inflasi utama minggu ini dengan dampak **{top_comm['impact']:.2f}%**. Perlu monitoring khusus pada pasokan dan distribusi komoditas ini."
                    })

                top_deflasi = comm_insights['commodity_impacts'].get('significant_negative', [])
                if top_deflasi:
                    top_comm = top_deflasi[0]
                    recommendations.append({
                        'icon': 'fa-leaf', 'color': 'success',
                        'title': 'Komoditas Pendorong Deflasi',
                        'text': f"**{top_comm['name'].replace('_', ' ').title()}** menjadi pendorong deflasi utama minggu ini dengan dampak **{top_comm['impact']:.2f}%**. Pastikan harga di tingkat petani tetap wajar."
                    })

            # Rekomendasi 4: Rekomendasi Umum
            if not recommendations:
                recommendations.append({
                    'icon': 'fa-check-circle', 'color': 'success',
                    'title': 'Kondisi Terkendali',
                    'text': 'Semua indikator (tren, volatilitas, dan dampak komoditas) berada dalam batas wajar. Lanjutkan monitoring rutin.'
                })

            # Simpan ke Cache
            result = {
                'success': True,
                'alerts': alerts[:5], # Batasi 5 alert teratas
                'recommendations': recommendations, # Kirim semua rekomendasi
                'statistics': statistics, # Kirim statistik untuk card atas
                'total_alerts': len(alerts),
                'generated_at': datetime.now().isoformat(),
                'cache_info': {'cached': False, 'generated_fresh': True},
                'data_period': {
                    'start': df['Tanggal'].min().strftime('%d/%m/%Y'),
                    'end': df['Tanggal'].max().strftime('%d/%m/%Y'),
                    'records': len(df)
                }
            }
            
            self._alerts_cache = result
            self._alerts_cache_time = current_time

            return result

        except Exception as e:
            logger.error(f"Error generating economic alerts: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'alerts': [],
                'recommendations': [],
                'statistics': {},
                'error': str(e)
            }