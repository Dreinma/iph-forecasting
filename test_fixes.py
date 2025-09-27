#!/usr/bin/env python3
"""Test the ML fixes"""

import pandas as pd
from models.forecasting_engine import ForecastingEngine
from services.data_handler import DataHandler

def test_fixes():
    print("🧪 Testing ML fixes...")
    
    try:
        # Load test data
        data_handler = DataHandler()
        df = data_handler.load_historical_data()
        
        if df.empty:
            print("❌ No test data available")
            return False
        
        print(f"📊 Test data: {len(df)} records")
        
        # Test forecasting engine
        engine = ForecastingEngine()
        
        # Test feature preparation
        print("🔧 Testing feature preparation...")
        features_df = engine.prepare_features(df)
        print(f"✅ Features: {len(features_df)} samples, {len(engine.feature_cols)} features")
        
        # Test model training
        print("🤖 Testing model training...")
        results, trained_models = engine.train_and_evaluate_models(df)
        
        print(f"✅ Training successful:")
        for name, result in results.items():
            print(f"   {name}: MAE={result['mae']:.4f}")
        
        # Test forecasting
        print("🔮 Testing forecasting...")
        best_model_name = min(results.keys(), key=lambda x: results[x]['mae'])
        
        forecast_df, _, forecast_summary = engine.generate_forecast(best_model_name, 4)
        
        print(f"✅ Forecast successful: {len(forecast_df)} predictions")
        print(f"   Avg prediction: {forecast_summary['avg_prediction']:.3f}%")
        
        print("\n🎉 ALL TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_fixes()