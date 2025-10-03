# 🎯 IPH Forecasting Dashboard
Sistem Forecasting Indikator Perubahan Harga (IPH) dengan Machine Learning dan Dashboard Interaktif

📖 Deskripsi
Sistem forecasting IPH yang menggunakan 4 algoritma machine learning dengan ensemble learning untuk memprediksi perubahan harga hingga 12 minggu ke depan. Dilengkapi dashboard interaktif untuk monitoring, analisis komoditas, dan sistem peringatan otomatis.

🎯 Keunggulan Utama
- Auto Model Selection - Sistem otomatis memilih model terbaik.
- Ensemble Learning - Kombinasi 3 model terbaik untuk akurasi optimal.
- Real-time Analytics - Dashboard responsif dengan update otomatis.
- Commodity Intelligence - Analisis dampak komoditas per kategori.
- Statistical Alerts - Deteksi anomali dan threshold otomatis.

🏗️ Arsitektur Sistem
🧠 Machine Learning Engine
```
📊 Data Input → 🔧 Feature Engineering → 🤖 Model Training → 🏆 Best Model Selection → 🔮 Forecasting
```

Models yang Digunakan:
- 🔍 K-Nearest Neighbors (KNN) - Pattern matching untuk data serupa.
- 🌳 Random Forest - Ensemble decision trees dengan optimasi hyperparameter.
- ⚡ LightGBM - Gradient boosting cepat dan efisien.
- 🚀 XGBoost Advanced - Gradient boosting dengan regularisasi tinggi.

Feature Engineering:
- Lag Features: Lag_1, Lag_2, Lag_3, Lag_4 (nilai historis).
- Moving Averages: MA_3, MA_7 (rata-rata bergerak).
- Time-based Features: Quarter, Week, Month untuk seasonality.

📊 Data Pipeline
# Automated Pipeline Flow
```
Upload Data → Validate Format → Clean & Merge → Feature Engineering → 
Model Training → Performance Evaluation → Best Model Selection → 
Multi-step Forecasting → Confidence Intervals → Dashboard Update
```

🖥️ Frontend Architecture
- 📱 Responsive Design - Bootstrap 5 + Custom CSS.
- 📊 Interactive Charts - Plotly.js untuk visualisasi dinamis.
- ⚡ Real-time Updates - JavaScript dengan auto-refresh.
- 🎨 Modern UI/UX - Gradient design dengan smooth animations.

📁 Struktur Project
```
iph-forecasting/
├──  app.py                 # Flask application utama
├──  config.py              # Konfigurasi aplikasi
├──  requirements.txt        # Dependencies Python
├──  test_fixes.py          # Testing ML fixes
│
├──  models/                 # Machine Learning Models
│   ├── __init__.py
│   ├──  forecasting_engine.py    # Core ML engine & algorithms
│   └──  model_manager.py        # Model management & comparison
│
├──  services/                # Business Logic Services
│   ├── __init__.py
│   ├──  data_handler.py          # Data processing & validation
│   ├──  forecast_service.py      # Forecasting orchestration
│   ├──  visualization_service.py  # Advanced data visualization
│   └──  commodity_insight_service.py # Commodity analysis engine
│
├──  static/                  # Frontend Assets
│   ├── css/
│   │   └──  style.css            # Custom styling & animations
│   └── js/
│       └──  dashboard.js         # Interactive dashboard logic
│
├──  templates/                # HTML Templates
│   ├──  base.html               # Base template dengan sidebar
│   ├──  dashboard.html          # Main dashboard
│   ├──  data_control.html      # Data management
│   ├──  visualization.html      # Advanced charts
│   ├──  commodity_insights.html  # Commodity analysis
│   ├──  alerts.html            # Alert system
│   └──  upload.html            # Data upload interface
│
└──  data/                    # Data Storage
    ├──  historical_data.csv       # Time series data
    ├──  IPH-Kota-Batu.csv       # Commodity data
    ├──  models/                  # Trained ML models
    │   ├──  performance_history.json
    │   └──  model_metadata.json
    └──  backups/                 # Auto backups
```

## 🚀 Quick Start
1️⃣ Installation
```
# Clone repository
git clone <repository-url>
cd iph-forecasting

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/models data/backups static/uploads
```

2️⃣ Run Application
```
python app.py
```

📱 Dashboard: ```http://localhost:5000```

3️⃣ First Time Setup
1. Upload Data - Drag & drop CSV dengan kolom Tanggal dan Indikator_Harga.
2. Auto Training - Sistem otomatis train 4 model ML.
3. View Results - Dashboard menampilkan forecast dan performance.

## 📊 Fitur Dashboard
### 🏠 Dashboard Utama
- Interactive Forecast Chart - Menampilkan data historis, prediksi dengan interval kepercayaan, dan info model aktif.
- Model Performance Grid - Perbandingan real-time metrik kinerja (MAE, RMSE, R², dll.) untuk semua model dengan indikator status visual.
- Economic Alerts & Notifications - Panel peringatan yang menampilkan notifikasi ekonomi berdasarkan tingkat prioritas dan keparahan.
- Forecast Data Table - Tabel rinci yang menampilkan nilai-nilai hasil peramalan, termasuk batas atas dan bawah.

### 📁 Data Control
- Drag & Drop Upload - CSV/Excel dengan preview.
- Historical Data Table - Pagination + search.
- Manual Record Entry - Tambah data point individual.
- Model Retraining - Retrain semua model dengan data terbaru.

### 📊 Advanced Visualization
- Moving Averages - SMA, EMA, WMA dengan toggle.
- Volatility Analysis - Rolling standard deviation.
- Model Performance - Trend, MAE Visualized, Model Drift

### 🌾 Commodity Insights
- Current Week Analysis - Dampak komoditas real-time.
- Monthly Deep Dive - Analisis bulanan komprehensif.
- Commodity Trends - Tracking 4-24 periode dengan trend coefficient.
- Volatility Alerts - Multi-level threshold system.
- Seasonal Patterns - Heatmap bulanan dengan kategori breakdown.

### 🔔 Alert System
- Statistical Alerts - 2-sigma & 3-sigma boundary detection.
- Threshold Monitoring - Custom threshold dengan severity levels.
- Trend Change Detection - Automatic trend reversal alerts.
- Volatility Spikes - Real-time volatility monitoring.

## 🤖 Machine Learning Details
Model Pipeline

```
# 1. Feature Engineering
Lag_1, Lag_2, Lag_3, Lag_4   # Historical values
MA_3, MA_7                   # Moving averages

# 2. Model Training dengan Time Series CV
for model in [KNN, RandomForest, LightGBM, XGBoost]:
    train_with_walk_forward_validation()
    evaluate_performance()

# 3. Best Model Selection
best_model = min(models, key=lambda x: x.mae)

# 4. Ensemble Creation (Top 3 models)
ensemble = weighted_average(top_3_models, weights=inverse_mae)

# 5. Multi-step Forecasting
forecast = monte_carlo_simulation(best_model, n_steps=weeks)
```

Performance Metrics
- MAE (Mean Absolute Error) - Primary selection criteria.
- RMSE (Root Mean Square Error) - Secondary metric.
- R² (Coefficient of Determination) - Goodness of fit.
- MAPE (Mean Absolute Percentage Error) - Relative error.

Advanced Features
- 🎯 Hyperparameter Optimization - Grid search untuk RF & LightGBM.
- 🔄 Time Series Cross-Validation - Walk-forward validation.
- 🎲 Monte Carlo Forecasting - Uncertainty quantification.
- 📊 Feature Selection - Automatic selection untuk dataset besar.
- 🚨 Model Drift Detection - Auto-retrain trigger.

### 🛠️ Technical Stack

Backend Framework
- 🐍 Flask - Web framework
- 📊 Pandas - Data manipulation
- 🤖 Scikit-learn - ML algorithms
- ⚡ LightGBM - Gradient boosting
- 🚀 XGBoost - Advanced gradient boosting
- 📈 Plotly - Interactive visualization

Frontend Technologies
- 🎨 Bootstrap - Responsive UI framework
- ⚡ JavaScript - Interactive functionality
- 📊 Plotly.js - Chart rendering
- 🎭 Font Awesome - Icons

Data Processing
- 📊 NumPy - Numerical computing
- 📈 SciPy - Statistical functions
- 📅 python-dateutil - Date parsing
- 📋 openpyxl - Excel file support

## 🔧 Installation & Setup
📋 Prerequisites
- Python 3.7 atau lebih tinggi
- 4GB RAM minimum (8GB recommended)
- 2GB disk space untuk data dan models

⚡ Quick Installation
```
# 1. Clone repository
git clone <repository-url>
cd iph-forecasting

# 2. Create virtual environment
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create required directories
mkdir -p data/models data/backups static/uploads

# 5. Run application
python app.py
```

🌐 Access Dashboard
- URL: http://localhost:5000
- Default Port: 5000 (configurable)

## 📈 Usage Guide

1️⃣ First Time Setup
1. Upload Historical Data
    - Format: CSV dengan kolom Tanggal dan Indikator_Harga.
    - Minimum: 15 data points untuk training.
    - Recommended: 50+ data points untuk akurasi optimal.

2. Automatic Processing
    - Sistem otomatis validate dan clean data.
    - Train 4 ML models dengan cross-validation.
    - Generate initial forecast.

2️⃣ Regular Operations
- Upload New Data - Sistem merge dengan data existing.
- Monitor Dashboard - Real-time metrics dan alerts.
- Generate Forecasts - Pilih model dan periode forecast.
- Analyze Commodities - Upload data komoditas untuk insights.

3️⃣ Advanced Features
- Model Comparison - Compare performance semua model.
- Data Visualization - Advanced time series analysis.
- Alert Configuration - Setup custom threshold monitoring.
- Export Data - Download historical/forecast data.

📊 Data Requirements
📈 Historical IPH Data (Mandatory)
| Column            | Type  | Description         | Example      |
|-------------------|-------|---------------------|--------------|
| `Tanggal`         | Date  | Tanggal observasi   | `2024-01-07` |
| `Indikator_Harga` | Float | Nilai IPH dalam persen | `1.25`       |

🌾 Commodity Data (Optional)
| Column                                | Type  | Description                |
|---------------------------------------|-------|----------------------------|
| `Bulan`                               | String| Bulan periode              |
| `Minggu ke-`                          | String| Minggu dalam bulan         |
| `Indikator Perubahan Harga (%)`       | Float | Nilai IPH                  |
| `Komoditas Andil Perubahan Harga`     | String| Dampak komoditas           |
| `Komoditas Fluktuasi Harga Tertinggi` | String| Komoditas paling volatile  |
| `Fluktuasi Harga`                     | Float | Nilai volatilitas          |

## 🚨 Troubleshooting

❌ Common Issues
- Data Upload Fails
    - Check file format: Didukung .csv, .xlsx. Tidak didukung .xls, .txt.
    - Check file size: Ukuran maks 16MB.
    - Check required columns: Wajib ada Tanggal, Indikator_Harga.
- Model Training Fails
    - Check data quantity: Minimum 15 records.
    - Check data quality: Pastikan tidak ada nilai yang hilang di kolom wajib.
    - Check date format: Didukung YYYY-MM-DD, DD/MM/YYYY.
- Charts Not Loading
    - Check browser console: Tekan F12 → tab Console.
    - Clear browser cache: Tekan Ctrl+F5 (hard refresh).
    - Check network: Pastikan koneksi internet stabil.

## 🤝 Contributing
🛠️ Development Setup
```
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code quality checks
flake8 .
black .
```

📝 Code Standards
- Kepatuhan PEP 8 untuk kode Python.
- Komentar JSDoc untuk fungsi JavaScript.
- Type hints untuk fungsi Python.
- Error handling untuk semua endpoint API.

🎯 Dibangun untuk peramalan IPH yang akurat dengan keandalan tingkat enterprise dan antarmuka yang ramah pengguna.