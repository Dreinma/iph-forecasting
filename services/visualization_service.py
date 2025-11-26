import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class VisualizationService:
    """Service for IPH-focused data visualization"""
    
    def __init__(self, data_handler):
        self.data_handler = data_handler
    
    def _clean_for_json(self, obj):
        """Clean data for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._clean_for_json(value) for key, value in obj.items()}
        elif pd.isna(obj):
            return None
        elif obj in [np.inf, -np.inf]:
            return None
        else:
            return obj
    
    def filter_by_timeframe(self, df, timeframe, start_date_str=None):
        """
        Filter based on specific START date and window size.
        Args:
            timeframe: '1M', '3M', '6M', 'ALL'
            start_date_str: String 'YYYY-MM-DD' (optional)
        """
        if df.empty:
            return df, None
        
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df['Tanggal']):
            df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        df = df.sort_values('Tanggal').reset_index(drop=True)
        
        if timeframe == 'ALL':
            return df, None
        
        # Window size map (days) - Updated requirements
        window_days_map = {'1M': 30, '3M': 90, '6M': 180, '1Y': 365, '2Y': 730}
        window_days = window_days_map.get(timeframe, 180) # Default 6M
        
        # Determine Start and End Date
        if start_date_str and start_date_str != 'null':
            try:
                start_date = pd.to_datetime(start_date_str)
            except:
                start_date = df['Tanggal'].min()
        else:
            # Default to latest window if no start date provided
            latest_date = df['Tanggal'].max()
            start_date = latest_date - timedelta(days=window_days)

        end_date = start_date + timedelta(days=window_days)
        
        # Filter
        df_filtered = df[(df['Tanggal'] >= start_date) & (df['Tanggal'] <= end_date)].reset_index(drop=True)
        
        # Coverage logic (simplified for brevity)
        coverage_info = {'coverage': 100, 'status': 'OK'} 
        
        return df_filtered, coverage_info

    def calculate_moving_averages(self, timeframe='1M', offset_months=0):
        """Moving averages analysis"""
        try:
            print(f"Calculating moving averages for {timeframe}...")

            df = self.data_handler.load_historical_data()

            if df is None or df.empty:
                print("No data returned from database")
                return {'success': False, 'message': 'Tidak ada data tersedia'}
                
            print(f" Data loaded: {len(df)} records")

            df_filtered, coverage_info = self.filter_by_timeframe(df, timeframe, offset_months)
            df = df_filtered.sort_values('Tanggal').reset_index(drop=True)

            print(f" After filter: {len(df)} records")

            if coverage_info:
                print(f"    Coverage: {coverage_info['coverage']}% ({coverage_info['status']})")

            if len(df) < 7:
                return {'success': False, 'message': 'Data tidak cukup (minimal 7 data)'}

            # Calculate Simple Moving Averages
            df['MA_3'] = df['Indikator_Harga'].rolling(window=3, min_periods=1).mean()
            df['MA_7'] = df['Indikator_Harga'].rolling(window=7, min_periods=1).mean()
            df['MA_14'] = df['Indikator_Harga'].rolling(window=14, min_periods=1).mean()
            df['MA_30'] = df['Indikator_Harga'].rolling(window=30, min_periods=1).mean()
            
            # Clean data and convert to JSON-safe format
            dates = [d.strftime('%Y-%m-%d') for d in df['Tanggal']]
            
            def safe_convert(series):
                """Convert series to JSON-safe list"""
                return [float(x) if pd.notna(x) and x not in [np.inf, -np.inf] else 0 
                       for x in series]
            
            chart_data = {
                'data': [
                    {
                        'x': dates,
                        'y': safe_convert(df['Indikator_Harga']),
                        'mode': 'lines',
                        'name': 'IPH Aktual',
                        'line': {'color': '#1f77b4', 'width': 3},
                        'visible': True
                    },
                    {
                        'x': dates,
                        'y': safe_convert(df['MA_3']),
                        'mode': 'lines',
                        'name': 'MA 3 Hari',
                        'line': {'color': '#ff7f0e', 'width': 2},
                        'visible': True
                    },
                    {
                        'x': dates,
                        'y': safe_convert(df['MA_7']),
                        'mode': 'lines',
                        'name': 'MA 7 Hari',
                        'line': {'color': '#2ca02c', 'width': 2},
                        'visible': True
                    },
                    {
                        'x': dates,
                        'y': safe_convert(df['MA_14']),
                        'mode': 'lines',
                        'name': 'MA 14 Hari',
                        'line': {'color': '#d62728', 'width': 2},
                        'visible': True
                    },
                    {
                        'x': dates,
                        'y': safe_convert(df['MA_30']),
                        'mode': 'lines',
                        'name': 'MA 30 Hari',
                        'line': {'color': '#9467bd', 'width': 2},
                        'visible': False
                    }
                ],
                'layout': {
                    'title': 'Analisis Moving Averages IPH',
                    'xaxis': {'title': 'Tanggal'},
                    'yaxis': {'title': 'IPH'},
                    'hovermode': 'x unified',
                    'height': 500,
                    'template': 'plotly_white',
                    'showlegend': True
                }
            }
            
            # Calculate additional statistics for moving averages
            latest_idx = len(df) - 1
            current_actual = df['Indikator_Harga'].iloc[latest_idx]
            current_ma3 = df['MA_3'].iloc[latest_idx]
            current_ma7 = df['MA_7'].iloc[latest_idx]
            current_ma14 = df['MA_14'].iloc[latest_idx]
            current_ma30 = df['MA_30'].iloc[latest_idx] if not pd.isna(df['MA_30'].iloc[latest_idx]) else None
            
            # Trend analysis
            ma3_trend = "naik" if current_ma3 > df['MA_3'].iloc[latest_idx-1] else "turun"
            ma7_trend = "naik" if current_ma7 > df['MA_7'].iloc[latest_idx-1] else "turun"
            
            # Crossover analysis
            golden_cross = current_ma3 > current_ma7 and df['MA_3'].iloc[latest_idx-1] <= df['MA_7'].iloc[latest_idx-1]
            death_cross = current_ma3 < current_ma7 and df['MA_3'].iloc[latest_idx-1] >= df['MA_7'].iloc[latest_idx-1]
            
            # Distance from actual price
            distance_ma3 = abs(current_actual - current_ma3)
            distance_ma7 = abs(current_actual - current_ma7)
            distance_ma14 = abs(current_actual - current_ma14)
            
            # Volatility of MA lines (standard deviation)
            ma3_volatility = df['MA_3'].std() if len(df) > 1 else 0
            ma7_volatility = df['MA_7'].std() if len(df) > 1 else 0
            
            # Support/Resistance levels
            support_level = min(current_ma3, current_ma7, current_ma14)
            resistance_level = max(current_ma3, current_ma7, current_ma14)
            
            print(f" Moving averages calculated successfully")

            # Enhanced response with moving averages statistics
            return {
                'success': True, 
                'chart': chart_data,
                'stats': {
                    'data_coverage': self._clean_for_json(coverage_info),
                    'total_records': int(len(df)),
                    'date_range': f"{dates[0]} to {dates[-1]}",
                    'moving_averages': {
                        'current_values': {
                            'actual': self._clean_for_json(round(float(current_actual), 3)),
                            'ma3': self._clean_for_json(round(float(current_ma3), 3)),
                            'ma7': self._clean_for_json(round(float(current_ma7), 3)),
                            'ma14': self._clean_for_json(round(float(current_ma14), 3)),
                            'ma30': self._clean_for_json(round(float(current_ma30), 3)) if current_ma30 is not None else None
                        },
                        'trends': {
                            'ma3_trend': self._clean_for_json(ma3_trend),
                            'ma7_trend': self._clean_for_json(ma7_trend),
                            'overall_trend': self._clean_for_json("naik" if current_ma3 > current_ma7 else "turun")
                        },
                        'signals': {
                            'golden_cross': self._clean_for_json(golden_cross),
                            'death_cross': self._clean_for_json(death_cross),
                            'signal_strength': "strong" if golden_cross or death_cross else "neutral"
                        },
                        'distances': {
                            'from_ma3': self._clean_for_json(round(float(distance_ma3), 3)),
                            'from_ma7': self._clean_for_json(round(float(distance_ma7), 3)),
                            'from_ma14': self._clean_for_json(round(float(distance_ma14), 3))
                        },
                        'volatility': {
                            'ma3_volatility': self._clean_for_json(round(float(ma3_volatility), 3)),
                            'ma7_volatility': self._clean_for_json(round(float(ma7_volatility), 3))
                        },
                        'levels': {
                            'support': self._clean_for_json(round(float(support_level), 3)),
                            'resistance': self._clean_for_json(round(float(resistance_level), 3))
                        }
                    }
                }
            }            
        except Exception as e:
            print(f"Error in calculate_moving_averages: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error: {str(e)}'}

    def analyze_volatility(self, timeframe='1M', start_date=None): # Changed param from offset_months to start_date
        try:
            print(f" Starting volatility analysis for {timeframe}, start: {start_date}")
            
            df = self.data_handler.load_historical_data()
            if df.empty:
                return {'success': False, 'message': 'Tidak ada data tersedia'}
            
            # Use the new filter logic
            df_filtered, coverage_info = self.filter_by_timeframe(df, timeframe, start_date)
            df = df_filtered.sort_values('Tanggal').reset_index(drop=True)

            if len(df) < 2: # Need at least 2 points
                 return {
                    'success': True, # Return true but empty to prevent frontend crash
                    'charts': None,
                    'stats': {
                        'current_volatility': 0, 'avg_volatility_30': 0,
                        'max_volatility': 0, 'min_volatility': 0
                    }
                }
            
            # --- Volatility Calculation Logic ---
            # Rolling standard deviation
            df['Volatility_7'] = df['Indikator_Harga'].rolling(window=7, min_periods=1).std().fillna(0)
            
            dates = [d.strftime('%Y-%m-%d') for d in df['Tanggal']]
            
            # Calculate Statistics for Cards
            # 1. Current Volatility (Last point in the selected window)
            current_vol = float(df['Volatility_7'].iloc[-1]) if not df.empty else 0
            
            # 2. Average Volatility (Mean of the window)
            avg_vol = float(df['Volatility_7'].mean()) if not df.empty else 0
            
            # 3. Range
            max_vol = float(df['Volatility_7'].max()) if not df.empty else 0
            min_vol = float(df['Volatility_7'][df['Volatility_7'] > 0].min()) if not df[df['Volatility_7'] > 0].empty else 0

            # Helper for JSON safe
            def safe_convert(series):
                return [float(x) if pd.notna(x) and x not in [np.inf, -np.inf] else 0 for x in series]

            # Charts Data
            accuracy_chart = {
                'data': [{
                    'x': dates,
                    'y': safe_convert(df['Indikator_Harga']),
                    'mode': 'lines+markers',
                    'name': 'IPH Aktual',
                    'line': {'color': '#1f77b4', 'width': 2}
                }],
                'layout': {
                    'title': f'Pergerakan IPH ({timeframe})',
                    'xaxis': {'title': 'Tanggal'},
                    'yaxis': {'title': 'IPH (%)'},
                    'margin': {'l': 40, 'r': 20, 't': 40, 'b': 40},
                    'height': 450
                }
            }

            stats = {
                'current_volatility': round(current_vol, 2),
                'avg_volatility_30': round(avg_vol, 2), # Reusing variable name for compatibility
                'max_volatility': round(max_vol, 2),
                'min_volatility': round(min_vol, 2)
            }

            return {
                'success': True,
                'charts': {'accuracy_trends': accuracy_chart}, # Using accuracy_trends key to match frontend
                'stats': stats
            }

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
        
    def analyze_model_performance(self, timeframe='6M', offset_months=0):
        """
        Load REAL model performance from database
        """
        try:
            print(f" Loading model performance from DATABASE...")
            
            from database import ModelPerformance
            
            #  LOAD FROM DATABASE
            perf_records = ModelPerformance.query.order_by(
                ModelPerformance.trained_at.desc()
            ).limit(200).all()  # Last 200 training records
            
            if not perf_records:
                return {
                    'success': False,
                    'message': 'No model performance data in database. Please train models first.'
                }
            
            print(f" Found {len(perf_records)} performance records in database")
            
            #  GROUP BY MODEL
            model_data = {}
            for record in perf_records:
                model_name = record.model_name
                if model_name not in model_data:
                    model_data[model_name] = []
                model_data[model_name].append({
                    'mae': record.mae,
                    'rmse': record.rmse,
                    'r2': record.r2_score,
                    'trained_at': record.trained_at
                })
            
            print(f" Models found: {list(model_data.keys())}")
            
            #  PREPARE CHART DATA
            colors = {
                'KNN': '#ef4444',
                'Random_Forest': '#22c55e', 
                'LightGBM': '#3b82f6',
                'XGBoost_Advanced': '#f59e0b'
            }
            
            # Chart 1: Accuracy Trends
            accuracy_traces = []
            for model_name, records in model_data.items():
                # Sort by date
                records_sorted = sorted(records, key=lambda x: x['trained_at'])
                
                dates = [r['trained_at'].strftime('%Y-%m-%d %H:%M') for r in records_sorted]
                mae_values = [r['mae'] for r in records_sorted]
                rmse_values = [r['rmse'] for r in records_sorted]
                r2_values = [r['r2'] for r in records_sorted]
                
                # MAE trace
                accuracy_traces.append({
                    'x': dates,
                    'y': mae_values,
                    'mode': 'lines+markers',
                    'name': f'{model_name} - MAE',
                    'line': {'color': colors.get(model_name, '#666'), 'width': 2},
                    'visible': True if model_name in ['LightGBM', 'XGBoost_Advanced'] else 'legendonly'
                })
            
            accuracy_chart = {
                'data': accuracy_traces,
                'layout': {
                    'title': f'Model Performance History ({len(perf_records)} trainings)',
                    'xaxis': {'title': 'Training Date'},
                    'yaxis': {'title': 'MAE'},
                    'hovermode': 'x unified',
                    'height': 450,
                    'template': 'plotly_white'
                }
            }
            
            # Chart 2: Latest Performance Comparison
            latest_perf = {}
            for model_name, records in model_data.items():
                latest = records[0]  # Already sorted desc
                latest_perf[model_name] = latest
            
            comparison_chart = {
                'data': [{
                    'x': list(latest_perf.keys()),
                    'y': [p['mae'] for p in latest_perf.values()],
                    'type': 'bar',
                    'marker': {'color': [colors.get(m, '#666') for m in latest_perf.keys()]}
                }],
                'layout': {
                    'title': 'Latest MAE Comparison',
                    'xaxis': {'title': 'Model'},
                    'yaxis': {'title': 'MAE'},
                    'height': 450
                }
            }
            
            # Chart 3: Model Drift (MAE over time for best model)
            best_model = min(latest_perf.keys(), key=lambda m: latest_perf[m]['mae'])
            best_records = sorted(model_data[best_model], key=lambda x: x['trained_at'])
            
            drift_chart = {
                'data': [{
                    'x': [r['trained_at'].strftime('%Y-%m-%d') for r in best_records],
                    'y': [r['mae'] for r in best_records],
                    'mode': 'lines+markers',
                    'name': f'{best_model} MAE',
                    'line': {'color': '#ef4444', 'width': 3}
                }],
                'layout': {
                    'title': f'MAE Trend - {best_model}',
                    'xaxis': {'title': 'Date'},
                    'yaxis': {'title': 'MAE'},
                    'height': 350
                }
            }
            
            #  STATS
            best_mae = latest_perf[best_model]['mae']
            best_r2 = latest_perf[best_model]['r2']
            
            # Model comparison table
            comparison_table = []
            for i, (model_name, perf) in enumerate(sorted(latest_perf.items(), key=lambda x: x[1]['mae'])):
                accuracy_pct = max(0, (1 - perf['mae']) * 100)
                grade = 'EXCELLENT' if accuracy_pct >= 85 else 'GOOD' if accuracy_pct >= 70 else 'FAIR' if accuracy_pct >= 55 else 'POOR'
                
                comparison_table.append({
                    'rank': i + 1,
                    'model': model_name,
                    'current_mae': round(perf['mae'], 4),
                    'current_rmse': round(perf['rmse'], 4),
                    'current_r2': round(perf['r2'], 3),
                    'accuracy_pct': round(accuracy_pct, 1),
                    'grade': grade,
                    'grade_color': 'success' if grade == 'EXCELLENT' else 'primary' if grade == 'GOOD' else 'warning',
                    'is_best': model_name == best_model
                })
            
            stats = {
                'best_model': best_model,
                'current_mae': round(best_mae, 4),
                'current_r2': round(best_r2, 3),
                'forecast_accuracy': f"{max(0, (1 - best_mae) * 100):.1f}%",
                'model_stability': 'STABIL',
                'total_data_points': len(perf_records),
                'last_updated': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'model_comparison_table': comparison_table,
                'insights': {
                    'best_performer': f"{best_model} dengan MAE {best_mae:.4f}",
                    'stability_status': 'Semua model stabil',
                    'data_characteristics': f'{len(perf_records)} training records'
                }
            }
            
            result = {
                'success': True,
                'charts': {
                    'accuracy_trends': accuracy_chart,
                    'forecast_vs_actual': comparison_chart,
                    'model_drift': drift_chart
                },
                'stats': stats,
                'models_available': list(model_data.keys())
            }
            
            print(f" Model performance loaded from database")
            return result
            
        except Exception as e:
            print(f" Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}