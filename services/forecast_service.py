from models.model_manager import ModelManager  # Perbaikan: import dari models, bukan services
from .data_handler import DataHandler
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

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

        print("🚀 ForecastService initialized")
        print("   🤖 Model manager ready")
        print("   📊 Data handler ready")
    
    def process_new_data_and_forecast(self, new_data_df, forecast_weeks=8):
        """ENHANCED pipeline with all ML improvements"""
        print("=" * 60)
        print("🔄 STARTING ENHANCED ML PIPELINE")
        print("=" * 60)
        
        pipeline_start_time = datetime.now()
        
        try:
            # Step 1: Process and merge new data
            print("\n📥 STEP 1: Processing new data...")
            combined_df, merge_info = self.data_handler.merge_and_save_data(new_data_df)
            
            # ✅ NEW: Check for model drift
            print("\n🔍 STEP 1.5: Checking for model drift...")
            try:
                drift_result = self.model_manager.check_model_health(new_data_df)
            except Exception as drift_error:
                print(f"⚠️ Drift detection failed: {str(drift_error)}")
                drift_result = {'drift_detected': False, 'reason': f'Drift check error: {str(drift_error)}'}
            
            force_retrain = drift_result.get('drift_detected', False)
            
            if force_retrain:
                print(f"🚨 Drift detected: {drift_result.get('drift_signals', [])}")
                print("🔄 Forcing model retraining due to drift...")
            
            # Step 2: Train and compare models
            print("\n🤖 STEP 2: Training and comparing models...")
            current_best = self.model_manager.get_current_best_model()
            
            if force_retrain or not current_best:
                training_result = self.model_manager.train_and_compare_models(combined_df)
            else:
                print("✅ Using existing models (no drift detected)")
                training_result = {
                    'training_results': {},
                    'comparison': {'is_improvement': False, 'new_best_model': current_best},
                    'summary': {'total_models_trained': 0}
                }
            
            # Step 3: Generate forecast with best model
            print("\n🔮 STEP 3: Generating forecast...")
            best_model = self.model_manager.get_current_best_model()
            
            if not best_model:
                raise ValueError("No trained models available")
            
            best_model_name = best_model['model_name']
            
            forecast_df, model_performance, forecast_summary = self.model_manager.engine.generate_forecast(
                best_model_name, forecast_weeks
            )
            
            # Calculate pipeline duration
            pipeline_duration = (datetime.now() - pipeline_start_time).total_seconds()
            
            # Prepare comprehensive result with proper JSON serialization
            result = {
                'success': True,
                'pipeline_duration': float(pipeline_duration),
                'timestamp': datetime.now().isoformat(),
                
                # ✅ NEW: Enhanced features
                'enhanced_features': {
                    'drift_detection': drift_result,
                    'model_optimization': force_retrain,
                    'ensemble_used': best_model_name == 'Ensemble'
                },
                
                # Data processing results
                'data_processing': {
                    'merge_info': {
                        'existing_records': int(merge_info['existing_records']),
                        'new_records': int(merge_info['new_records']),
                        'total_records': int(merge_info['total_records']),
                        'duplicates_removed': int(merge_info['duplicates_removed']),
                        'date_overlap': bool(merge_info['date_overlap'])
                    },
                    'data_summary': clean_data_for_json(self.data_handler.get_data_summary())
                },
                
                # Model training results
                'model_training': training_result,
                
                # Best model information
                'best_model': {
                    'name': best_model_name,
                    'performance': {
                        'mae': float(model_performance.get('mae', 0)) if not np.isnan(model_performance.get('mae', 0)) else 0.0,
                        'rmse': float(model_performance.get('rmse', 0)) if not np.isnan(model_performance.get('rmse', 0)) else 0.0,
                        'r2_score': float(model_performance.get('r2_score', 0)) if not np.isnan(model_performance.get('r2_score', 0)) else 0.0,
                        'training_time': float(model_performance.get('training_time', 0))
                    },
                    'is_improvement': training_result.get('comparison', {}).get('is_improvement', False)
                },
                
                # Forecast results
                'forecast': {
                    'data': clean_data_for_json(forecast_df.to_dict('records')),
                    'summary': clean_data_for_json(forecast_summary),
                    'model_used': best_model_name,
                    'weeks_forecasted': int(forecast_weeks)
                }
            }

            # Final cleaning
            result = clean_data_for_json(result)
            
            print("\n" + "=" * 60)
            print("✅ ENHANCED PIPELINE COMPLETED!")
            print(f"   ⏱️ Total time: {pipeline_duration:.2f} seconds")
            print(f"   📊 Data records: {merge_info['total_records']}")
            print(f"   🏆 Best model: {best_model_name}")
            print(f"   📈 Forecast weeks: {forecast_weeks}")
            print(f"   🎯 Avg prediction: {forecast_summary['avg_prediction']:.3f}%")
            print("=" * 60)
            
            return result
            
        except Exception as e:
            error_msg = f"Enhanced pipeline failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'pipeline_duration': float((datetime.now() - pipeline_start_time).total_seconds())
            }
        
    def get_current_forecast(self, model_name=None, forecast_weeks=8):
        """Get forecast using current best model or specified model"""
        print("=" * 80)
        print("🎯 GET CURRENT FORECAST DEBUG:")
        print(f"   🤖 Requested model: '{model_name}'")
        print(f"   📊 Requested weeks: {forecast_weeks}")
        
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
                print(f"   🏆 Using best model: '{model_name}'")
            else:
                print(f"   🎯 Using specified model: '{model_name}'")
                
                # Validate that the specified model exists
                available_models = self.model_manager.engine.get_available_models()
                model_names = [m['name'].replace(' ', '_') for m in available_models]
                
                print(f"   📋 Available models: {model_names}")
                
                if model_name not in model_names:
                    print(f"   ❌ Model '{model_name}' not found in available models")
                    return {
                        'success': False,
                        'error': f'Model "{model_name}" not found. Available models: {", ".join(model_names)}'
                    }
                else:
                    print(f"   ✅ Model '{model_name}' found in available models")
            
            # Validate forecast weeks
            if not (4 <= forecast_weeks <= 12):
                return {
                    'success': False,
                    'error': 'Forecast weeks must be between 4 and 12'
                }
            
            print(f"   🔄 Calling engine.generate_forecast with model: '{model_name}', weeks: {forecast_weeks}")
            
            # Generate forecast
            forecast_df, model_performance, forecast_summary = self.model_manager.engine.generate_forecast(
                model_name, forecast_weeks
            )
            
            print(f"   📊 Forecast generated:")
            print(f"      - DataFrame shape: {forecast_df.shape}")
            print(f"      - Model performance keys: {model_performance.keys() if model_performance else 'None'}")
            print(f"      - Summary keys: {forecast_summary.keys() if forecast_summary else 'None'}")
            
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
            
            print(f"   🧹 Cleaned forecast data: {len(forecast_data_clean)} records")
            
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
            
            # 🚨 PERBAIKAN UTAMA: Simpan forecast terbaru di memory
            self._latest_forecast = result['forecast'].copy()
            print(f"   💾 Latest forecast saved in memory: {self._latest_forecast['model_name']}")
            
            print(f"   ✅ Final result prepared:")
            print(f"      - Original request: '{original_model_name}'")
            print(f"      - Model name in result: '{result['forecast']['model_name']}'")
            print(f"      - Weeks in result: {result['forecast']['weeks_forecasted']}")
            print(f"      - Success: {result['success']}")
            print("=" * 80)
            
            return result
            
        except Exception as e:
            error_msg = f"Error generating forecast: {str(e)}"
            print(f"   ❌ Exception occurred: {error_msg}")
            print("=" * 80)
            
            import traceback
            traceback.print_exc()
            
            return {
                'success': False, 
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
            
    def initialize_from_csv(self, csv_file_path):
        """Initialize system with CSV data (for first-time setup)"""
        print("🚀 INITIALIZING SYSTEM WITH CSV DATA")
        print("=" * 50)
        
        try:
            # Load CSV data
            print(f"📂 Loading data from: {csv_file_path}")
            df = pd.read_csv(csv_file_path)
            
            print(f"📊 Loaded {len(df)} records from CSV")
            print(f"   📋 Columns: {list(df.columns)}")
            
            # Process as new data (this will become historical data)
            result = self.process_new_data_and_forecast(df, forecast_weeks=8)
            
            if result['success']:
                print("\n🎉 SYSTEM INITIALIZATION COMPLETED!")
                print("   ✅ Data processed and stored")
                print("   ✅ Models trained and saved")
                print("   ✅ Initial forecast generated")
                print("   ✅ Dashboard ready for use")
            else:
                print(f"\n❌ INITIALIZATION FAILED: {result['error']}")
            
            return result
                
        except Exception as e:
            error_msg = f"Error initializing from CSV: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                'success': False, 
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_dashboard_data(self):
        """Get all data needed for dashboard display"""
        print("📊 Collecting dashboard data...")
        
        try:
            # Get data summary
            data_summary = self.data_handler.get_data_summary()
            
            # Get model performance summary
            model_summary = self.model_manager.get_model_performance_summary()
            
            # Get current best model
            best_model = self.model_manager.get_current_best_model()
            
            # 🚨 PERBAIKAN UTAMA: Prioritaskan latest forecast dari memory
            current_forecast = None
            if self._latest_forecast:
                print(f"   💾 Using latest forecast from memory: {self._latest_forecast['model_name']}")
                current_forecast = self._latest_forecast
            elif best_model:
                print(f"   🏆 No latest forecast, using best model forecast")
                forecast_result = self.get_current_forecast(best_model['model_name'], 8)
                if forecast_result['success']:
                    current_forecast = forecast_result['forecast']
            
            # Get training history for charts
            training_history = self.model_manager.get_training_history_chart_data()
            
            # Get recent backups info
            recent_backups = self.data_handler.get_recent_backups(5)
            
            dashboard_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data_summary': data_summary,
                'model_summary': model_summary,
                'best_model': best_model,
                'current_forecast': current_forecast,
                'training_history': training_history,
                'recent_backups': recent_backups,
                'system_status': self._get_system_status()
            }
            
            print("✅ Dashboard data collected successfully")
            return dashboard_data
            
        except Exception as e:
            error_msg = f"Error collecting dashboard data: {str(e)}"
            print(f"❌ {error_msg}")
            
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
    
    def retrain_models_only(self):
        """Retrain models with existing data without new data upload"""
        print("🔄 Retraining models with existing data...")
        
        try:
            # Load existing data
            df = self.data_handler.load_historical_data()
            
            if df.empty:
                return {
                    'success': False,
                    'error': 'No historical data available for retraining'
                }
            
            # Train models
            training_result = self.model_manager.train_and_compare_models(df)
            
            # Generate new forecast with best model
            best_model_name = training_result['comparison']['new_best_model']['model_name']
            forecast_df, model_performance, forecast_summary = self.model_manager.engine.generate_forecast(
                best_model_name, 8
            )
            
            # 🚨 PERBAIKAN: Clear latest forecast agar tidak conflict
            self._latest_forecast = None
            print("   🗑️ Cleared latest forecast from memory (will use retrained best model)")
            
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'training_results': training_result['training_results'],
                'comparison': training_result['comparison'],
                'best_model': {
                    'name': best_model_name,
                    'performance': model_performance
                },
                'new_forecast': {
                    'data': forecast_df.to_dict('records'),
                    'summary': forecast_summary
                }
            }
            
            print(f"✅ Models retrained successfully!")
            print(f"   🏆 Best model: {best_model_name}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error retraining models: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
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
        print("🗑️ Latest forecast cleared from memory")
        
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
        """Generate real-time economic alerts based on historical data and forecasting"""
        try:

            current_time = datetime.now()
            if (self._alerts_cache and self._alerts_cache_time and 
                (current_time - self._alerts_cache_time).seconds < 300):
                print("🔄 Using cached alerts")
                return self._alerts_cache
            
            print("🔄 Generating fresh alerts")

            alerts = []
            
            # Load historical data
            df = self.data_handler.load_historical_data()
            if df.empty or len(df) < 10:
                return {
                    'success': False,
                    'alerts': [],
                    'message': 'Insufficient data for alert generation'
                }
            
            # Get current forecast
            forecast_result = self.get_current_forecast()
            forecast_data = None
            if forecast_result['success']:
                forecast_data = forecast_result['forecast']['data']
            
            # Sort data by date
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])
            df = df.sort_values('Tanggal').reset_index(drop=True)  

            np.random.seed(42)

            # Calculate statistical thresholds
            recent_data = df.tail(30)  
            mean_iph = df['Indikator_Harga'].mean()
            std_iph = df['Indikator_Harga'].std()
            latest_iph = df['Indikator_Harga'].iloc[-1]
            latest_date = df['Tanggal'].iloc[-1]
            
            # 1. PRICE SPIKE ALERT
            if len(df) >= 7:
                week_ago_iph = df['Indikator_Harga'].iloc[-7]
                weekly_change = ((latest_iph - week_ago_iph) / week_ago_iph) * 100
                
                if abs(weekly_change) > 2.0:  # More than 2% change
                    alert_type = 'spike' if weekly_change > 0 else 'drop'
                    icon = 'fa-arrow-up' if weekly_change > 0 else 'fa-arrow-down'
                    color = 'warning' if weekly_change > 0 else 'info'
                    
                    alerts.append({
                        'type': alert_type,
                        'severity': 'warning' if abs(weekly_change) < 5 else 'critical',
                        'icon': icon,
                        'color': color,
                        'title': f"{'Lonjakan' if weekly_change > 0 else 'Penurunan'} Harga Signifikan",
                        'message': f"IPH {'naik' if weekly_change > 0 else 'turun'} {abs(weekly_change):.1f}% dalam 7 hari terakhir",
                        'detail': f"Dari {week_ago_iph:.3f} menjadi {latest_iph:.3f}",
                        'date': latest_date.strftime('%d/%m/%Y'),
                        'priority': 'high' if abs(weekly_change) > 5 else 'medium'
                    })
            
            # 2. STATISTICAL BOUNDARY ALERT
            upper_2sigma = mean_iph + 2 * std_iph
            lower_2sigma = mean_iph - 2 * std_iph
            upper_3sigma = mean_iph + 3 * std_iph
            lower_3sigma = mean_iph - 3 * std_iph
            
            if latest_iph > upper_3sigma:
                alerts.append({
                    'type': 'boundary_critical',
                    'severity': 'critical',
                    'icon': 'fa-exclamation-triangle',
                    'color': 'danger',
                    'title': 'IPH Melampaui Batas Kritis Atas',
                    'message': f'IPH {latest_iph:.3f}% melampaui batas 3-sigma ({upper_3sigma:.3f}%)',
                    'detail': f'Probabilitas kejadian: < 0.3%',
                    'date': latest_date.strftime('%d/%m/%Y'),
                    'priority': 'critical'
                })
            elif latest_iph < lower_3sigma:
                alerts.append({
                    'type': 'boundary_critical',
                    'severity': 'critical',
                    'icon': 'fa-exclamation-triangle',
                    'color': 'danger',
                    'title': 'IPH Melampaui Batas Kritis Bawah',
                    'message': f'IPH {latest_iph:.3f}% di bawah batas 3-sigma ({lower_3sigma:.3f}%)',
                    'detail': f'Probabilitas kejadian: < 0.3%',
                    'date': latest_date.strftime('%d/%m/%Y'),
                    'priority': 'critical'
                })
            elif latest_iph > upper_2sigma:
                alerts.append({
                    'type': 'boundary_warning',
                    'severity': 'warning',
                    'icon': 'fa-arrow-up',
                    'color': 'warning',
                    'title': 'IPH Mendekati Batas Atas',
                    'message': f'IPH {latest_iph:.3f}% mendekati batas 2-sigma ({upper_2sigma:.3f}%)',
                    'detail': f'Perlu monitoring ketat',
                    'date': latest_date.strftime('%d/%m/%Y'),
                    'priority': 'medium'
                })
            elif latest_iph < lower_2sigma:
                alerts.append({
                    'type': 'boundary_warning',
                    'severity': 'warning',
                    'icon': 'fa-arrow-down',
                    'color': 'warning',
                    'title': 'IPH Mendekati Batas Bawah',
                    'message': f'IPH {latest_iph:.3f}% mendekati batas 2-sigma ({lower_2sigma:.3f}%)',
                    'detail': f'Perlu monitoring ketat',
                    'date': latest_date.strftime('%d/%m/%Y'),
                    'priority': 'medium'
                })
            
            # 3. VOLATILITY ALERT
            if len(df) >= 14:
                recent_volatility = df['Indikator_Harga'].tail(14).std()
                historical_volatility = df['Indikator_Harga'].std()
                
                if recent_volatility > historical_volatility * 1.5:
                    alerts.append({
                        'type': 'volatility',
                        'severity': 'warning',
                        'icon': 'fa-chart-line',
                        'color': 'info',
                        'title': 'Volatilitas Tinggi Terdeteksi',
                        'message': f'Volatilitas 2 minggu terakhir meningkat {((recent_volatility/historical_volatility-1)*100):.0f}%',
                        'detail': f'Volatilitas: {recent_volatility:.3f}% vs rata-rata {historical_volatility:.3f}%',
                        'date': latest_date.strftime('%d/%m/%Y'),
                        'priority': 'medium'
                    })
            
            # 4. TREND CHANGE ALERT
            if len(df) >= 10:
                recent_trend = df['Indikator_Harga'].tail(5).diff().mean()
                if abs(recent_trend) > std_iph * 0.3:
                    trend_direction = "naik" if recent_trend > 0 else "turun"
                    alerts.append({
                        'type': 'trend_change',
                        'severity': 'info',
                        'icon': 'fa-exchange-alt',
                        'color': 'info',
                        'title': 'Perubahan Tren Terdeteksi',
                        'message': f'Tren {trend_direction} konsisten dalam 5 periode terakhir',
                        'detail': f'Rata-rata perubahan: {recent_trend:.3f}',
                        'date': latest_date.strftime('%d/%m/%Y'),
                        'priority': 'low'
                    })
            
            # 5. FORECAST-BASED ALERTS
            if forecast_data and len(forecast_data) > 0:
                # Get forecast trend
                first_forecast = forecast_data[0]['Prediksi']
                last_forecast = forecast_data[-1]['Prediksi']
                forecast_change = ((last_forecast - first_forecast) / first_forecast) * 100
                
                # Forecast vs Current Alert
                current_vs_forecast = ((first_forecast - latest_iph) / latest_iph) * 100
                
                if abs(current_vs_forecast) > 3:
                    direction = "naik" if current_vs_forecast > 0 else "turun"
                    alerts.append({
                        'type': 'forecast_divergence',
                        'severity': 'info',
                        'icon': 'fa-crystal-ball',
                        'color': 'primary',
                        'title': f'Prediksi Menunjukkan Perubahan',
                        'message': f'Model memprediksi IPH akan {direction} {abs(current_vs_forecast):.1f}% minggu depan',
                        'detail': f'Dari {latest_iph:.3f} ke {first_forecast:.3f}',
                        'date': pd.to_datetime(forecast_data[0]['Tanggal']).strftime('%d/%m/%Y'),
                        'priority': 'medium'
                    })
                
                # Long-term forecast trend
                if abs(forecast_change) > 5:
                    trend_dir = "naik" if forecast_change > 0 else "turun"
                    alerts.append({
                        'type': 'forecast_trend',
                        'severity': 'info',
                        'icon': 'fa-chart-line',
                        'color': 'primary',
                        'title': f'Tren Jangka Menengah: {trend_dir.title()}',
                        'message': f'Peramalan menunjukkan tren {trend_dir} {abs(forecast_change):.1f}% dalam 8 minggu',
                        'detail': f'Dari {first_forecast:.3f} ke {last_forecast:.3f}',
                        'date': pd.to_datetime(forecast_data[-1]['Tanggal']).strftime('%d/%m/%Y'),
                        'priority': 'low'
                    })
            
            # 6. MODEL CONFIDENCE ALERT
            best_model = self.model_manager.get_current_best_model()
            if best_model and best_model.get('mae', 0) > 1.0:
                alerts.append({
                    'type': 'model_confidence',
                    'severity': 'warning',
                    'icon': 'fa-robot',
                    'color': 'warning',
                    'title': 'Akurasi Model Menurun',
                    'message': f'Model {best_model["model_name"]} memiliki error tinggi (MAE: {best_model["mae"]:.3f})',
                    'detail': 'Disarankan untuk melakukan retraining model',
                    'date': datetime.now().strftime('%d/%m/%Y'),
                    'priority': 'medium'
                })
            
            # Sort alerts by priority
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))
            
            result = {
                'success': True,
                'alerts': alerts[:5],  # Limit to 5 most important alerts
                'total_alerts': len(alerts),
                'generated_at': datetime.now().isoformat(),
                'cache_info': {
                    'cached': False,
                    'generated_fresh': True
                },
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
            print(f"❌ Error generating economic alerts: {str(e)}")
            return {
                'success': False,
                'alerts': [],
                'error': str(e)
            }