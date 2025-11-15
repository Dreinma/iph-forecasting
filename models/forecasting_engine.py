# models/forecasting_engine.py (Versi DEPLOY/INFERENCE-ONLY)
import random
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import warnings
import logging
import onnxruntime as rt

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

class ForecastingEngine:
    """
    Mesin forecasting yang dimodifikasi untuk HANYA menjalankan
    inference menggunakan model ONNX yang sudah dilatih.
    """
    
    def __init__(self, data_path=None, models_path=None):
        np.random.seed(42)
        random.seed(42)
        
        logger.debug(f"Initializing ForecastingEngine with data_path={data_path}, models_path={models_path}")
        
        # Handle None data_path - use default or skip
        if data_path is None:
            logger.debug("data_path is None, using default or skipping data folder creation")
            self.data_path = None  # Will handle later
        else:
            self.data_path = data_path
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        # Set models path
        if models_path is None:
            self.models_path = 'data/models'
            logger.debug(f"models_path is None, using default: {self.models_path}")
        else:
            self.models_path = models_path
        
        os.makedirs(self.models_path, exist_ok=True)
        
        # Initialize other attributes
        self.feature_cols = None
        self.scaler = None
        logger.debug("[OK] ForecastingEngine initialized")
        
    def _load_model_session(self, model_name):
        """Memuat atau mengambil sesi inference ONNX dari cache."""
        if model_name in self.model_sessions:
            return self.model_sessions[model_name]
        
        # Ganti .pkl dengan .onnx
        safe_name = model_name.replace(' ', '_').replace('/', '_')
        filepath = os.path.join(self.models_path, f"{safe_name}.onnx")
        
        if not os.path.exists(filepath):
            logger.error(f"Model file ONNX tidak ditemukan: {filepath}")
            raise FileNotFoundError(f"Model file ONNX tidak ditemukan: {filepath}. Harap latih model secara lokal, konversi ke .onnx, dan unggah ke data/models/.")
            
        try:
            # Muat sesi inference
            # Paksa penggunaan CPUExecutionProvider agar ringan
            logger.info(f"Mencoba memuat model ONNX: {filepath}")
            sess = rt.InferenceSession(filepath, providers=['CPUExecutionProvider'])
            self.model_sessions[model_name] = sess
            logger.info(f"Model ONNX berhasil dimuat: {filepath}")
            return sess
        except Exception as e:
            logger.error(f"Gagal memuat model ONNX {model_name}: {e}")
            raise

    def prepare_features(self, df):
        """Mempersiapkan fitur (HARUS SAMA DENGAN VERSI TRAINING)"""
        logger.debug("Preparing features...")
        df_copy = df.copy()
        
        if 'Tanggal' in df_copy.columns:
            df_copy['Tanggal'] = pd.to_datetime(df_copy['Tanggal'])
        
        df_copy = df_copy.sort_values('Tanggal').reset_index(drop=True)
        
        for lag in [1, 2, 3, 4]:
            df_copy[f'Lag_{lag}'] = df_copy['Indikator_Harga'].shift(lag)
        
        df_copy['MA_3'] = df_copy['Indikator_Harga'].rolling(window=3, min_periods=1).mean()
        df_copy['MA_7'] = df_copy['Indikator_Harga'].rolling(window=7, min_periods=1).mean()
        
        self.feature_cols = ['Lag_1', 'Lag_2', 'Lag_3', 'Lag_4', 'MA_3', 'MA_7']

        df_clean = df_copy.dropna(subset=self.feature_cols)
        
        logger.debug(f"Features prepared: {len(df_clean)} samples ready.")
        return df_clean

    def _update_features_deterministic(self, current_features, new_pred, all_predictions, step):
        """Update fitur secara deterministik (6 FITUR) - (Harus sama dengan versi training)"""
        
        expected_features = 6  # Lag_1, Lag_2, Lag_3, Lag_4, MA_3, MA_7
        
        # Pastikan tipe data adalah float32 untuk ONNX
        new_features = np.zeros(expected_features, dtype=np.float32) 
        
        new_features[0] = float(new_pred)  # Lag_1
        
        for i in range(1, 4):  # Lag_2, Lag_3, Lag_4
            if i < len(current_features):
                new_features[i] = float(current_features[i-1])
            else:
                new_features[i] = 0.0
        
        # Update Moving Averages (indices 4-5)
        if step == 0:
            ma3_values = [
                float(new_pred),
                float(current_features[0]) if len(current_features) > 0 else 0.0,
                float(current_features[1]) if len(current_features) > 1 else 0.0
            ]
            new_features[4] = float(np.mean(ma3_values))  # MA_3
            
            ma7_values = [float(f) for f in current_features[:4]]
            new_features[5] = float(np.mean(ma7_values)) if ma7_values else 0.0  # MA_7
        else:
            recent_preds_3 = all_predictions[-min(3, len(all_predictions)):]
            new_features[4] = float(np.mean(recent_preds_3))
            
            recent_preds_7 = all_predictions[-min(7, len(all_predictions)):]
            new_features[5] = float(np.mean(recent_preds_7))
        
        return new_features

    def forecast_multistep_deterministic(self, model_session, last_features, n_steps):
        """Menjalankan forecast multistep menggunakan sesi ONNX."""
        logger.debug(f"Generating {n_steps}-step DETERMINISTIC forecast (ONNX)...")
        
        try:
            input_name = model_session.get_inputs()[0].name
            output_name = model_session.get_outputs()[0].name
        except IndexError:
            logger.error("Model ONNX tidak memiliki input/output. Model korup?")
            raise ValueError("Model ONNX tidak valid.")
        
        # Pastikan tipe data adalah float32 dan 6 fitur
        expected_features = len(self.feature_cols)
        if len(last_features) != expected_features:
            if len(last_features) > expected_features:
                current_features = last_features[:expected_features].astype(np.float32)
            else:
                current_features = np.pad(last_features, (0, expected_features - len(last_features)), 'constant').astype(np.float32)
        else:
            current_features = last_features.astype(np.float32)

        predictions = []
        historical_volatility = np.std(current_features[:4])
        
        for step in range(n_steps):
            X_pred = current_features.reshape(1, -1)
            
            # Jalankan inference ONNX
            pred_result = model_session.run([output_name], {input_name: X_pred})
            
            if isinstance(pred_result[0], (list, np.ndarray)):
                pred = pred_result[0][0]
                if isinstance(pred, (list, np.ndarray)):
                     pred = pred[0]
            else:
                pred = pred_result[0]

            pred = float(pred) 
            predictions.append(pred)
            
            current_features = self._update_features_deterministic(
                current_features, pred, predictions, step
            )
        
        predictions_array = np.array(predictions)
        
        # (Logika confidence interval tetap sama)
        confidence_widths = []
        for step in range(n_steps):
            base_uncertainty = historical_volatility * 0.1
            step_multiplier = np.sqrt(step + 1) * 0.05
            confidence_width = base_uncertainty + step_multiplier
            confidence_widths.append(confidence_width)
        
        confidence_widths = np.array(confidence_widths)
        confidence_multiplier = 1.96
        lower_bounds = predictions_array - (confidence_widths * confidence_multiplier)
        upper_bounds = predictions_array + (confidence_widths * confidence_multiplier)
        
        return {
            'predictions': predictions_array,
            'lower_bound': lower_bounds,
            'upper_bound': upper_bounds,
            'confidence_width': float(np.mean(upper_bounds - lower_bounds)),
        }

    def generate_forecast(self, model_name, forecast_weeks=8):
        """Generate forecast menggunakan model ONNX yang dimuat."""
        logger.debug(f"Forecasting engine (ONNX) - Generate forecast: model='{model_name}'")
        
        if not (4 <= forecast_weeks <= 12):
            raise ValueError("Forecast weeks must be between 4 and 12")
        
        # Load data historis untuk fitur
        # Di Vercel, kita asumsikan data_handler akan memuat dari DB
        from services.data_handler import DataHandler
        df = DataHandler().load_historical_data() 
        
        if df.empty:
             raise ValueError("No historical data found. Please upload data first.")
        
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        df = df.sort_values('Tanggal').reset_index(drop=True)
        
        df_features = self.prepare_features(df)
        if df_features.empty:
            raise ValueError("Tidak ada data valid untuk forecasting (setelah prepare_features)")
        
        # Muat sesi model ONNX
        try:
            model_session = self._load_model_session(model_name)
        except FileNotFoundError:
            logger.error(f"Model {model_name}.onnx tidak ditemukan. Latih dan unggah model terlebih dahulu.")
            raise
        except Exception as e:
            logger.error(f"Gagal memuat model {model_name}.onnx: {e}")
            raise

        last_features = df_features[self.feature_cols].iloc[-1].values
        
        forecast_result = self.forecast_multistep_deterministic(
            model_session, last_features, forecast_weeks
        )
        
        last_date = df_features['Tanggal'].max()
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=7), 
            periods=forecast_weeks, 
            freq='W'
        )
        
        forecast_df = pd.DataFrame({
            'Tanggal': [date.strftime('%Y-%m-%d') for date in forecast_dates],
            'Prediksi': [float(pred) for pred in forecast_result['predictions']],
            'Batas_Bawah': [float(lower) for lower in forecast_result['lower_bound']],
            'Batas_Atas': [float(upper) for upper in forecast_result['upper_bound']],
            'Model': model_name,
            'Confidence_Width': float(forecast_result['confidence_width']),
            'Generated_At': datetime.now().isoformat()
        })
        
        forecast_summary = {
            'avg_prediction': float(forecast_result['predictions'].mean()),
            'trend': 'Naik' if forecast_result['predictions'][-1] > forecast_result['predictions'][0] else 'Turun',
            'volatility': float(np.std(forecast_result['predictions'])),
            'confidence_avg': float(forecast_result['confidence_width']),
            'min_prediction': float(forecast_result['predictions'].min()),
            'max_prediction': float(forecast_result['predictions'].max())
        }
        
        # 'model_performance' sekarang adalah dummy
        model_performance = {
            'mae': 0.0, 'rmse': 0.0, 'r2_score': 0.0, 'training_time': 0.0
        }
        
        return forecast_df, model_performance, forecast_summary

    def get_available_models(self):
        """Mencari file .onnx di folder models."""
        if not os.path.exists(self.models_path):
            return []
        
        model_files = [f for f in os.listdir(self.models_path) if f.endswith('.onnx')]
        available_models = []
        
        for file in model_files:
            # Ambil nama model dari nama file .onnx
            model_name = os.path.splitext(file)[0].replace('_', ' ')
            filepath = os.path.join(self.models_path, file)
            stat = os.stat(filepath)
            available_models.append({
                'name': model_name,
                'filename': file,
                'size_mb': stat.st_size / (1024 * 1024),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return available_models