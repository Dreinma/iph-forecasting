# models/model_manager.py - Database-Enabled Model Manager
import os
import json
import pandas as pd
import numpy as np  
from datetime import datetime
from database import db, ModelPerformance
from sqlalchemy import and_, func
from .forecasting_engine import ForecastingEngine

class ModelDriftDetector:
    """Detect when models need retraining (same as before)"""
    
    def __init__(self, drift_threshold=0.05):
        self.drift_threshold = drift_threshold
        self.reference_data = None
        self.reference_performance = None
    
    def set_reference(self, X_reference, model_performance):
        """Set reference data and performance"""
        self.reference_data = {
            'mean': np.mean(X_reference, axis=0),
            'std': np.std(X_reference, axis=0),
            'min': np.min(X_reference, axis=0),
            'max': np.max(X_reference, axis=0)
        }
        self.reference_performance = model_performance
    
    def detect_drift(self, X_new, current_performance):
        """Detect data drift and performance degradation"""
        if self.reference_data is None:
            return {'drift_detected': False, 'reason': 'No reference data'}
        
        drift_signals = []
        
        # Statistical drift detection
        new_stats = {
            'mean': np.mean(X_new, axis=0),
            'std': np.std(X_new, axis=0)
        }
        
        mean_shift = np.abs(new_stats['mean'] - self.reference_data['mean'])
        mean_threshold = self.reference_data['std'] * 2
        
        if np.any(mean_shift > mean_threshold):
            drift_signals.append('mean_shift')
        
        std_ratio = new_stats['std'] / (self.reference_data['std'] + 1e-8)
        if np.any((std_ratio > 2) | (std_ratio < 0.5)):
            drift_signals.append('variance_change')
        
        # Performance degradation
        if self.reference_performance and current_performance:
            current_mae = current_performance.get('mae', float('inf'))
            reference_mae = self.reference_performance.get('mae', 0)
            
            performance_degradation = (current_mae - reference_mae) / (reference_mae + 1e-8)
            
            if performance_degradation > 0.2:
                drift_signals.append('performance_degradation')
        
        drift_detected = len(drift_signals) > 0
        
        return {
            'drift_detected': drift_detected,
            'drift_signals': drift_signals,
            'drift_score': len(drift_signals) / 3,
            'recommendation': 'retrain' if drift_detected else 'monitor'
        }


class ModelManager:
    """ Database-enabled model manager"""
    
    def __init__(self, data_path='data/historical_data.csv', models_path='data/models/'):
        self.engine = ForecastingEngine(data_path, models_path)
        self.models_path = models_path
        
        os.makedirs(models_path, exist_ok=True)
        
        print("ModelManager initialized (Database Mode)")
    
    def save_performance_history(self, results):
        """ Save model performance to database"""
        print("Saving performance history to database...")
        
        try:
            timestamp = datetime.utcnow()
            batch_id = f"training_{timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            saved_count = 0
            
            for model_name, performance in results.items():
                # Prepare feature importance as JSON
                feature_importance_json = None
                if performance.get('feature_importance'):
                    feature_importance_json = json.dumps([
                        float(x) if x is not None else None 
                        for x in performance['feature_importance']
                    ])
                
                # Create new performance record
                perf_record = ModelPerformance(
                    model_name=model_name,
                    batch_id=batch_id,
                    mae=float(performance['mae']),
                    rmse=float(performance.get('rmse', 0.0)),
                    r2_score=float(performance['r2_score']),
                    cv_score=float(performance.get('cv_score', 0.0)),
                    mape=float(performance.get('mape', 0)),
                    training_time=float(performance['training_time']),
                    data_size=int(performance['data_size']),
                    test_size=int(performance.get('test_size', 0)),
                    is_best=bool(performance.get('is_best', False)),
                    feature_importance=feature_importance_json,
                    trained_at=timestamp
                )
                
                db.session.add(perf_record)
                saved_count += 1
            
            # Commit all records
            db.session.commit()
            
            print(f"Saved {saved_count} performance records to database")
            
            # Cleanup old records (keep last 50 per model)
            self._cleanup_old_performance_records()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving performance history: {str(e)}")
    
    def _cleanup_old_performance_records(self):
        """ Keep only last N records per model"""
        try:
            # Get all model names
            model_names = db.session.query(ModelPerformance.model_name).distinct().all()
            
            for (model_name,) in model_names:
                # Get record count for this model
                record_count = ModelPerformance.query.filter_by(model_name=model_name).count()
                
                if record_count > 50:
                    # Get records to delete (keep last 50)
                    records_to_delete = ModelPerformance.query.filter_by(
                        model_name=model_name
                    ).order_by(
                        ModelPerformance.trained_at.desc()
                    ).offset(50).all()
                    
                    for record in records_to_delete:
                        db.session.delete(record)
                    
                    print(f"   Cleaned up {len(records_to_delete)} old records for {model_name}")
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during cleanup: {str(e)}")
    
    def load_performance_history(self):
        """ Load performance history from database"""
        try:
            # Query all performance records ordered by trained_at
            records = ModelPerformance.query.order_by(
                ModelPerformance.trained_at.asc()
            ).all()
            
            # Convert to list of dicts
            history = [record.to_dict() for record in records]
            
            return history
            
        except Exception as e:
            print(f"Error loading performance history: {str(e)}")
            return []
    
    def get_current_best_model(self):
        """ Get current best model from database"""
        try:
            # Get latest best model for each model type
            
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
            
            if not latest_models:
                print("No trained models found in database")
                return None
            
            # Filter valid models
            valid_models = []
            for model in latest_models:
                if (model.mae is not None and 
                    not np.isnan(model.mae) and 
                    not np.isinf(model.mae) and 
                    model.mae < 100.0):
                    valid_models.append(model)
            
            if not valid_models:
                print("No valid model results found")
                return None
            
            # Find best model (lowest MAE)
            best_model = min(valid_models, key=lambda x: x.mae)
            
            print(f"Current best model: {best_model.model_name} (MAE: {best_model.mae:.4f})")
            
            return best_model.to_dict()
            
        except Exception as e:
            print(f"Error getting best model: {str(e)}")
            return None
    
    def compare_with_previous_best(self, new_results):
        """Compare new results with previous best model (same logic as before)"""
        print("Comparing with previous best model...")
        
        current_best = self.get_current_best_model()
        
        best_new_model_name = min(new_results.keys(), key=lambda x: new_results[x]['mae'])
        best_new_model = new_results[best_new_model_name].copy()
        best_new_model['model_name'] = best_new_model_name
        
        if not current_best:
            print("No previous model found. Setting new best model.")
            return {
                'is_improvement': True,
                'new_best_model': best_new_model,
                'previous_best': None,
                'improvement_percentage': None,
                'comparison_metrics': {
                    'mae_change': None,
                    'rmse_change': None,
                    'r2_change': None
                }
            }
        
        def safe_percentage_change(old_val, new_val):
            if old_val == 0 or np.isnan(old_val) or np.isinf(old_val):
                if new_val == 0 or np.isnan(new_val) or np.isinf(new_val):
                    return 0.0
                else:
                    return 100.0 if new_val > 0 else -100.0
            
            change = (old_val - new_val) / abs(old_val) * 100
            return max(-1000.0, min(1000.0, change))
        
        mae_improvement = safe_percentage_change(current_best['mae'], best_new_model['mae'])
        rmse_improvement = safe_percentage_change(current_best['rmse'], best_new_model['rmse'])
        
        if abs(current_best['r2_score']) > 1e-8:
            r2_improvement = (best_new_model['r2_score'] - current_best['r2_score']) / abs(current_best['r2_score']) * 100
            r2_improvement = max(-1000.0, min(1000.0, r2_improvement))
        else:
            r2_improvement = 0.0
        
        is_improvement = best_new_model['mae'] < current_best['mae']
        
        comparison = {
            'is_improvement': is_improvement,
            'new_best_model': best_new_model,
            'previous_best': current_best,
            'improvement_percentage': mae_improvement if is_improvement else -abs(mae_improvement),
            'comparison_metrics': {
                'mae_change': float(mae_improvement),
                'rmse_change': float(rmse_improvement),
                'r2_change': float(r2_improvement),
                'significant_improvement': abs(mae_improvement) > 5
            }
        }
        
        if is_improvement:
            if abs(mae_improvement) > 10:
                print(f" Significant improvement! {best_new_model_name} improved MAE by {mae_improvement:.2f}%")
            else:
                print(f" Modest improvement. {best_new_model_name} improved MAE by {mae_improvement:.2f}%")
        else:
            print(f" Previous model still better. Current best: {current_best['model_name']} (MAE: {current_best['mae']:.4f})")
        
        return comparison
    
    def train_and_compare_models(self, df):
        """Train models and compare with previous best (same as before)"""
        print(" Starting comprehensive model training and comparison...")
        
        try:
            results, trained_models = self.engine.train_and_evaluate_models(df)
            
            comparison = self.compare_with_previous_best(results)
            
            saved_models = self.engine.save_models(trained_models, results)
            
            #  Save to database instead of JSON
            self.save_performance_history(results)
            
            training_summary = {
                'total_models_trained': len(results),
                'best_model': comparison['new_best_model']['model_name'],
                'training_completed_at': datetime.now().isoformat(),
                'data_size': results[list(results.keys())[0]]['data_size'],
                'is_improvement': comparison['is_improvement']
            }
            
            print(f" Training completed successfully!")
            print(f"    Best model: {training_summary['best_model']}")
            print(f"    Models trained: {training_summary['total_models_trained']}")
            print(f"    Improvement: {'Yes' if training_summary['is_improvement'] else 'No'}")
            
            return {
                'training_results': results,
                'comparison': comparison,
                'trained_models': trained_models,
                'saved_models': saved_models,
                'summary': training_summary
            }
            
        except Exception as e:
            print(f"Error in training and comparison: {str(e)}")
            raise
    
    def get_model_performance_summary(self):
        """ Get performance summary from database"""
        try:
            # Get all model names
            model_names = db.session.query(ModelPerformance.model_name).distinct().all()
            
            model_summary = {}
            
            for (model_name,) in model_names:
                # Get all performances for this model
                performances = ModelPerformance.query.filter_by(
                    model_name=model_name
                ).order_by(ModelPerformance.trained_at.asc()).all()
                
                if not performances:
                    continue
                
                latest = performances[-1]
                
                model_summary[model_name] = {
                    'name': model_name,
                    'performances': [p.to_dict() for p in performances],
                    'best_mae': min(p.mae for p in performances),
                    'latest_mae': latest.mae,
                    'latest_r2': latest.r2_score,
                    'training_count': len(performances),
                    'avg_training_time': np.mean([p.training_time for p in performances]),
                    'improvement_trend': []
                }
                
                # Calculate trend
                recent_maes = [p.mae for p in performances[-5:]]
                if len(recent_maes) > 1:
                    trend = np.polyfit(range(len(recent_maes)), recent_maes, 1)[0]
                    model_summary[model_name]['trend_direction'] = 'improving' if trend < 0 else 'declining'
                else:
                    model_summary[model_name]['trend_direction'] = 'stable'
            
            return model_summary
            
        except Exception as e:
            print(f"Error getting model summary: {str(e)}")
            return {}
    
    def get_training_history_chart_data(self):
        """ Get training history from database"""
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
    
    def check_model_health(self, new_data_df):
        """Check if models need retraining (same as before)"""
        if not hasattr(self, 'drift_detector'):
            self.drift_detector = ModelDriftDetector()
        
        try:
            df_features = self.engine.prepare_features(new_data_df)
            
            if df_features.empty:
                return {'drift_detected': False, 'reason': 'No valid features'}
            
            X_new = df_features[self.engine.feature_cols].values
            
            best_model = self.get_current_best_model()
            
            if best_model:
                drift_result = self.drift_detector.detect_drift(X_new, best_model)
                
                if drift_result['drift_detected']:
                    print(f" DRIFT DETECTED: {drift_result['drift_signals']}")
                    print(f" Drift score: {drift_result['drift_score']:.2f}")
                
                return drift_result
            
            return {'drift_detected': False, 'reason': 'No reference model'}
            
        except Exception as e:
            print(f"Error in drift detection: {str(e)}")
            return {'drift_detected': False, 'reason': f'Error: {str(e)}'}


class EnsembleModel:
    """Ensemble model wrapper (same as before)"""
    
    def __init__(self, models, weights, model_names):
        self.models = models
        self.weights = weights
        self.model_names = model_names
    
    def predict(self, X):
        predictions = []
        
        for model in self.models:
            pred = model.predict(X)
            predictions.append(pred)
        
        ensemble_pred = np.average(predictions, weights=self.weights, axis=0)
        return ensemble_pred
    
    def get_feature_importance(self):
        importances = []
        
        for model, weight in zip(self.models, self.weights):
            if hasattr(model, 'feature_importances_'):
                imp = model.feature_importances_ * weight
                importances.append(imp)
        
        if importances:
            return np.sum(importances, axis=0)
        return None