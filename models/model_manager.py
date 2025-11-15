# models/model_manager.py (Versi DEPLOY/INFERENCE-ONLY)
import os
import json
import pandas as pd
import numpy as np  
import pickle
from datetime import datetime
from database import db, ModelPerformance
from sqlalchemy import and_, func
from .forecasting_engine import ForecastingEngine # Import engine baru (inference-only)
import onnxruntime as rt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelManager:
    """ 
    Model manager yang dimodifikasi untuk HANYA menjalankan inference.
    Training dinonaktifkan, tetapi performance history (dari DB) tetap bisa dibaca.
    """

    def __init__(self, models_path='data/models/'):
            self.models_path = models_path
            self.loaded_models = {}  # {model_name: onnx_session}
            self.model_metadata = {}  # {model_name: {scaler, features}}
            
            os.makedirs(models_path, exist_ok=True)
            logger.info("ModelManager initialized (Inference-Only Mode)")
            
            # Load ONNX models saat init
            self._load_onnx_models()

    def _load_onnx_models(self):
        """
        Load .onnx models dari disk menggunakan ONNX Runtime.
        ONNX Runtime adalah runtime kecil (~30MB), bukan sklearn.
        """
        logger.debug(f"Loading .onnx models from {self.models_path}")
        
        try:
            if not os.path.exists(self.models_path):
                logger.warning(f"Models path not found: {self.models_path}")
                return
            
            # Cari semua .onnx files
            onnx_files = [f for f in os.listdir(self.models_path) if f.endswith('.onnx')]
            
            if not onnx_files:
                logger.warning("No .onnx model files found")
                return
            
            for onnx_file in onnx_files:
                try:
                    onnx_path = os.path.join(self.models_path, onnx_file)
                    model_name = onnx_file.replace('.onnx', '')
                    
                    # Load ONNX session (TIDAK perlu sklearn!)
                    logger.debug(f"  Loading {model_name}...")
                    session = rt.InferenceSession(
                        onnx_path, 
                        providers=['CPUExecutionProvider']
                    )
                    
                    self.loaded_models[model_name] = session
                    logger.info(f"  [OK] Loaded {model_name} (ONNX)")
                    
                    # Coba load metadata (scaler, features) dari .pkl.meta
                    meta_path = onnx_path.replace('.onnx', '.pkl.meta')
                    if os.path.exists(meta_path):
                        with open(meta_path, 'rb') as f:
                            self.model_metadata[model_name] = pickle.load(f)
                        logger.debug(f"  [OK] Loaded metadata for {model_name}")
                    
                except Exception as e:
                    logger.error(f"  [ERROR] Load {onnx_file}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"[ERROR] Failed to load ONNX models: {e}", exc_info=True)

    def predict(self, X):
        """
        Make prediction dengan ONNX Runtime.
        
        Args:
            X: numpy array dengan shape (n_samples, n_features)
            
        Returns:
            predictions: numpy array
        """
        try:
            model_name, session = self.get_best_model()
            
            if session is None:
                raise Exception("No model loaded")
            
            # Scale input jika ada metadata
            if model_name in self.model_metadata:
                scaler = self.model_metadata[model_name]['scaler']
                X_scaled = scaler.transform(X).astype(np.float32)
            else:
                X_scaled = X.astype(np.float32)
            
            # Get input/output names dari session
            input_name = session.get_inputs()[0].name
            output_name = session.get_outputs()[0].name
            
            # Run inference
            predictions = session.run([output_name], {input_name: X_scaled})
            
            return predictions[0]
            
        except Exception as e:
            logger.error(f"[ERROR] Prediction failed: {e}", exc_info=True)
            raise

    def load_performance_history(self):
        """ Load performance history from database (TETAP SAMA)"""
        try:
            records = ModelPerformance.query.order_by(
                ModelPerformance.trained_at.asc()
            ).all()
            history = [record.to_dict() for record in records]
            return history
        except Exception as e:
            print(f"Error loading performance history: {str(e)}")
            return []
    
    def get_current_best_model(self):
        """ 
        Get current best model from database.
        Ini akan membaca data performa yang di-upload dari lokal.
        (TETAP SAMA, DENGAN FALLBACK)
        """
        try:
            # 1. Coba baca dari Database (diisi oleh skrip lokal)
            subquery = db.session.query(
                ModelPerformance.model_name,
                func.max(ModelPerformance.trained_at).label('max_trained_at')
            ).group_by(ModelPerformance.model_name).subquery()
            
            latest_models = db.session.query(ModelPerformance).join(
                subquery,
                and_(
                    ModelPerformance.model_name == subquery.c.model_name,
                    ModelPerformance.trained_at == subquery.c.max_trained_at
                )
            ).all()
            
            if latest_models:
                valid_models = [m for m in latest_models if m.mae is not None and not np.isnan(m.mae)]
                if valid_models:
                    best_model = min(valid_models, key=lambda x: x.mae)
                    print(f"Current best model (from DB): {best_model.model_name} (MAE: {best_model.mae:.4f})")
                    return best_model.to_dict()

            # 2. Fallback: Jika DB kosong, baca dari file .onnx
            print("No performance data in DB, falling back to .onnx files...")
            onnx_models = self.engine.get_available_models()
            if not onnx_models:
                print("No .onnx model files found.")
                return None
            
            # Ambil model pertama yang ditemukan
            best_onnx = onnx_models[0]
            print(f"Using fallback .onnx model: {best_onnx['name']}")
            # Kembalikan dict dummy
            return {'model_name': best_onnx['name'], 'mae': 0, 'rmse': 0, 'r2_score': 0}
            
        except Exception as e:
            print(f"Error getting best model: {str(e)}")
            return None
    
    def get_model_performance_summary(self):
        """ Get performance summary from database (TETAP SAMA, DENGAN FALLBACK)"""
        try:
            model_names_db = db.session.query(ModelPerformance.model_name).distinct().all()
            model_summary = {}
            
            for (model_name,) in model_names_db:
                performances = ModelPerformance.query.filter_by(
                    model_name=model_name
                ).order_by(ModelPerformance.trained_at.asc()).all()
                
                if not performances: continue
                
                latest = performances[-1]
                
                model_summary[model_name] = {
                    'name': model_name,
                    'performances': [p.to_dict() for p in performances],
                    'best_mae': min(p.mae for p in performances if p.mae is not None),
                    'latest_mae': latest.mae,
                    'latest_r2': latest.r2_score,
                    'training_count': len(performances),
                    'avg_training_time': np.mean([p.training_time for p in performances if p.training_time is not None]),
                    'latest_perf_obj': latest.to_dict() # Untuk admin/models
                }
                
                recent_maes = [p.mae for p in performances[-5:] if p.mae is not None]
                if len(recent_maes) > 1:
                    trend = np.polyfit(range(len(recent_maes)), recent_maes, 1)[0]
                    model_summary[model_name]['trend_direction'] = 'improving' if trend < 0 else 'declining'
                else:
                    model_summary[model_name]['trend_direction'] = 'stable'
            
            # Jika DB kosong, isi dari file .onnx
            if not model_summary:
                print("No performance data in DB, reading .onnx files for summary.")
                onnx_models = self.engine.get_available_models()
                for model_info in onnx_models:
                    model_name = model_info['name']
                    model_summary[model_name] = {
                        'name': model_name,
                        'performances': [], 'best_mae': 0, 'latest_mae': 0, 'latest_r2': 0,
                        'training_count': 1, 'avg_training_time': 0, 'trend_direction': 'stable',
                        'latest_perf_obj': { # Buat dummy object
                            'name': model_name, 'mae': 0, 'rmse': 0, 'r2_score': 0, 'mape': 0,
                            'trained_at': model_info['modified'], 'data_size': 0, 'is_best': False
                        }
                    }
                # Tandai yang pertama sebagai 'best' (fallback)
                if model_summary:
                    first_key = list(model_summary.keys())[0]
                    model_summary[first_key]['latest_perf_obj']['is_best'] = True

            # Pastikan ada 'is_best'
            if model_summary and not any(v['latest_perf_obj'].get('is_best') for v in model_summary.values()):
                 best_model_name = min(model_summary.keys(), key=lambda k: model_summary[k]['latest_mae'] or float('inf'))
                 if best_model_name in model_summary:
                     model_summary[best_model_name]['latest_perf_obj']['is_best'] = True

            return model_summary
            
        except Exception as e:
            print(f"Error getting model summary: {str(e)}")
            return {}
    
    def get_training_history_chart_data(self):
        """ Get training history from database (TETAP SAMA)"""
        try:
            history = self.load_performance_history()
            chart_data = {}
            for entry in history:
                model_name = entry['model_name']
                if model_name not in chart_data:
                    chart_data[model_name] = {
                        'timestamps': [],
                        'mae_values': [],
                        'r2_values': []
                    }
                chart_data[model_name]['timestamps'].append(entry['trained_at'])
                chart_data[model_name]['mae_values'].append(entry['mae'])
                chart_data[model_name]['r2_values'].append(entry['r2_score'])
            return chart_data
        except Exception as e:
            print(f"Error getting training history: {str(e)}")
            return {}