# 🎯 PRISMA - Price Indicator Smart Monitoring & Analytics

**Sistem Forecasting Indikator Perubahan Harga (IPH) dengan Machine Learning, Database Terintegrasi, dan Dashboard Interaktif**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue.svg)](https://sqlite.org)

---

## 📝 Deskripsi Singkat

**PRISMA** adalah platform forecasting IPH terpadu yang mengintegrasikan:
- ✅ **4 Algoritma ML** (KNN, Random Forest, LightGBM, XGBoost) dengan Ensemble Learning
- ✅ **Database SQLite** dengan 6 tabel terintegrasi (IPH, Commodity, Performance, Alerts)
- ✅ **Dashboard Real-time** dengan visualisasi interaktif dan alert system
- ✅ **Commodity Analysis** dengan parsing otomatis dan kategori impact
- ✅ **Admin Panel** untuk manajemen alert rules dan riwayat peringatan

Didesain untuk **monitoring harga komoditas**, **deteksi anomali**, dan **peramalan trend** dengan akurasi tinggi.

---

## 🚀 Fitur Utama

### 🤖 Machine Learning Engine
- **4 Model Terintegrasi**: KNN, Random Forest, LightGBM, XGBoost Advanced
- **Auto Model Selection**: Sistem otomatis memilih model terbaik berdasarkan MAE terendah
- **Ensemble Learning**: Weighted average dari top 3 models untuk akurasi optimal
- **Time Series CV**: Walk-forward validation untuk temporal data
- **Hyperparameter Optimization**: Grid search otomatis untuk RF & LightGBM
- **Model Drift Detection**: Monitoring degradasi performa real-time

### 📊 Data Management
- **Database Integration**: SQLite dengan 6 tabel (IPHData, CommodityData, ModelPerformance, AlertHistory, AlertRule, AdminUser)
- **Unified Data Upload**: CSV/Excel upload + input manual dalam satu interface
- **Commodity Database**: Parsing otomatis komoditas dengan format `KOMODITAS(nilai);...`
- **Auto Backup**: Backup CSV sebelum setiap operasi database
- **Data Validation**: Comprehensive validation dengan error handling

### 📈 Forecasting & Analytics
- **Multi-step Forecasting**: Deterministic predictions dengan 95% confidence interval
- **Recursive Features**: Update Lag_1-4, MA_3, MA_7 setiap step
- **Economic Alerts**: Real-time alerts berdasarkan statistical boundaries (2σ, 3σ)
- **Commodity Insights**: Analisis dampak komoditas per kategori dengan kategori breakdown
- **Seasonal Patterns**: Analisis pola seasonal bulanan dengan trend detection
- **Volatility Analysis**: Ranking komoditas paling volatile dengan multi-level threshold

### 🎨 Dashboard & UI
- **Responsive Design**: Bootstrap 5 + custom CSS dengan gradient themes
- **Interactive Charts**: Plotly.js untuk visualisasi dinamis
- **Real-time Updates**: Auto-refresh dengan error handling
- **Indonesian Localization**: Interface lengkap dalam bahasa Indonesia (semua teks, kecuali judul PRISMA)
- **Public Access**: Semua pengunjung dapat mengakses dashboard, visualisasi, commodity insights, dan alerts
- **Generate Forecast**: Tersedia untuk semua pengunjung (fitur utama - read-only operation)

### 🔔 Alert System
- **Statistical Alerts**: 2-sigma (95%) & 3-sigma (99.7%) boundary detection
- **Volatility Alerts**: Multi-level threshold (5%, 8%, 10%)
- **Trend Detection**: Automatic trend change alerts
- **Custom Rules**: Admin-defined alert rules dengan condition & threshold
- **Alert History**: Unlimited history dengan pagination, filter, export CSV
- **Real-time Notifications**: Priority-based alert system

---

## 🏗️ Arsitektur Sistem

### Database Schema
```

SQLite Database (data/prisma.db)
├── IPHData (Tabel utama data IPH)
│   ├── id (PK)
│   ├── tanggal (Date, Unique Index)
│   ├── indikator_harga (Float)
│   ├── bulan, minggu, tahun (Metadata)
│   └── lag_1-4, ma_3, ma_7 (Features)
│
├── CommodityData (Data komoditas terintegrasi)
│   ├── id (PK)
│   ├── iph_id (FK → IPHData)
│   ├── komoditas_andil (Text - parsed format)
│   ├── komoditas_fluktuasi (String - most volatile)
│   └── nilai_fluktuasi (Float - volatility value)
│
├── ModelPerformance (Performance history tracking)
│   ├── model_name, mae, rmse, r2_score, mape
│   ├── trained_at (Index)
│   └── feature_importance (JSON)
│
├── AlertHistory (Alert records - unlimited)
│   ├── alert_type, severity, title, message
│   ├── acknowledged, is_active (Enhanced status)
│   ├── admin_notes (Admin management)
│   └── created_at (Index)
│
├── AlertRule (Custom alert rules)
│   ├── rule_name, rule_type, threshold_value
│   ├── comparison_operator (>, <, >=, <=, ==)
│   └── severity_level, check_period_days
│
└── AdminUser (User management)
    ├── username (Unique)
    ├── password_hash
    └── last_login

```
---
### ML Pipeline
```
Data Upload → Validation → Feature Engineering → Time Series CV
    ↓
Train 4 Models (KNN, RF, LightGBM, XGBoost) → Evaluate Performance
    ↓
Select Best Model (Lowest MAE) → Create Ensemble (Top 3)
    ↓
Save Models + Performance to Database → Generate Forecast
    ↓
Create Confidence Intervals → Detect Alerts → Dashboard Update

```
---
### Service Architecture
```
app.py (Flask Routes)
├── ForecastService (Orchestration)
│   ├── ModelManager (Model training & comparison)
│   │   └── ForecastingEngine (ML algorithms)
│   ├── DataHandler (Data operations)
│   │   └── Database (SQLite ORM)
│   ├── VisualizationService (Chart data)
│   └── CommodityInsightService (Commodity analysis)
└── Database Models (SQLAlchemy)

```
---

## 📁 Struktur Project
```
iph-forecasting-app/
├── 📱 app.py                          # Flask application (1362 lines)
├── ⚙️ config.py                       # Konfigurasi aplikasi
├── 🗄️ database.py                     # Database models & ORM (SQLAlchemy)
├── 📋 requirements.txt                # Dependencies Python
│
├── 🤖 models/
│   ├── forecasting_engine.py         # ML algorithms & forecasting
│   │   ├── XGBoostAdvanced (Custom)
│   │   ├── ForecastingEngine (Main engine)
│   │   ├── EnsembleModel (Weighted average)
│   │   ├── TimeSeriesValidator (Walk-forward CV)
│   │   └── ModelOptimizer (Hyperparameter tuning)
│   └── model_manager.py              # Model management & database integration
│       ├── ModelManager (Database-enabled)
│       ├── ModelDriftDetector (Performance monitoring)
│       └── EnsembleModel (Wrapper)
│
├── 🔧 services/
│   ├── data_handler.py               # Data operations (Database-first)
│   │   ├── load_historical_data()
│   │   ├── merge_and_save_data()
│   │   ├── backup_database_to_csv()
│   │   └── get_data_summary()
│   ├── forecast_service.py           # Forecasting orchestration
│   │   ├── process_new_data_and_forecast()
│   │   ├── get_current_forecast()
│   │   ├── get_dashboard_data()
│   │   └── get_real_economic_alerts()
│   ├── visualization_service.py      # Chart data generation
│   ├── commodity_insight_service.py  # Commodity analysis
│   │   ├── parse_commodity_impacts()
│   │   ├── get_current_week_insights()
│   │   ├── get_monthly_analysis()
│   │   ├── get_seasonal_patterns()
│   │   └── get_alert_commodities()
│   └── debugger.py                   # Centralized logging
│
├── 🎨 static/
│   ├── css/style.css                 # Custom styling
│   ├── js/dashboard.js               # Interactive logic
│   └── uploads/                      # File upload storage
│
├── 📄 templates/
│   ├── base.html                     # Base layout dengan sidebar navigasi
│   ├── dashboard.html                # Main dashboard (forecast chart, model performance, alerts)
│   ├── data_control.html             # Data management (upload, manual input, retrain)
│   ├── visualization.html             # Advanced charts (moving averages, volatility, model performance)
│   ├── commodity_insights.html       # Commodity analysis (weekly, monthly, trends, seasonal)
│   ├── alerts.html                   # Alert system (real-time alerts & history)
│   └── admin/                        # Admin templates (dalam pengembangan)
│       ├── dashboard.html            # Admin dashboard
│       └── login.html                # Admin login
│
├── 💾 data/
│   ├── prisma.db                     # SQLite database
│   ├── models/
│   │   ├── KNN.pkl
│   │   ├── Random_Forest.pkl
│   │   ├── LightGBM.pkl
│   │   ├── XGBoost_Advanced.pkl
│   │   ├── Ensemble.pkl
│   │   ├── model_metadata.json
│   │   └── performance_history.json
│   ├── backups/                      # Auto backups
│   └── db_backups/                   # Database CSV backups
│
└── 📚 docs/
    ├── README.md
    ├── CHANGELOG.md
    └── API_DOCUMENTATION.md

```
---

## 🚀 Instalasi & Setup

### 1️⃣ Prerequisites
```bash
- Python 3.8+ (tested 3.8-3.11)
- 4GB RAM minimum (8GB recommended)
- 2GB disk space
- Conda atau pip
```

### 2️⃣ Installation

```bash
# Clone repository
git clone <repository-url>
cd iph-forecasting-app

# Setup conda environment (recommended)
conda create -n prisma python=3.10
conda activate prisma

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/models data/backups data/db_backups static/uploads
```

### 3️⃣ Database Setup

```bash
# Initialize database (otomatis saat first run)
python app.py

# Database akan dibuat di: data/prisma.db
# Tables akan di-create otomatis via SQLAlchemy
```

### 4️⃣ Run Application

```bash
# Start the application
python app.py

# Dashboard akan tersedia di: http://localhost:5001
```

### 5️⃣ Access Points

#### 🟢 **Halaman Publik (Tidak Perlu Login)**
| Halaman | URL | Deskripsi |
| --- | --- | --- |
| Dashboard Utama | `http://localhost:5001` | Dashboard peramalan IPH dengan forecast chart, model performance, dan alerts |
| Visualisasi | `http://localhost:5001/visualization` | Chart lanjutan: moving averages, volatilitas, dan performa model |
| Commodity Insights | `http://localhost:5001/commodity-insights` | Analisis dampak komoditas: weekly, monthly, trends, dan seasonal patterns |
| Alert System | `http://localhost:5001/alerts` | Sistem peringatan real-time dengan history |
| Kontrol Data | `http://localhost:5001/data-control` | Upload data dan manajemen (Admin only - dalam rencana) |

#### 🔐 **Halaman Admin (Perlu Login)**
| Halaman | URL | Deskripsi | Status |
| --- | --- | --- | --- |
| Admin Login | `http://localhost:5001/admin/login` | Login admin | ✅ Tersedia |
| Admin Dashboard | `http://localhost:5001/admin/dashboard` | Dashboard admin dengan statistik | ✅ Tersedia |

**Catatan**: Sistem visitor/admin sedang dalam pengembangan. Saat ini semua halaman dapat diakses oleh publik, dengan rencana implementasi proteksi admin untuk halaman data control dan fungsi administratif lainnya.

***

## 📊 Fitur Dashboard

### 🏠 Dashboard Utama

- **📈 Interactive Forecast Chart** - Historis + prediksi dengan 95% CI
- **🏆 Model Performance Grid** - Real-time comparison MAE, RMSE, R², MAPE
- **🚨 Economic Alerts Panel** - Notifikasi real-time (2σ, 3σ boundaries)
- **📋 Forecast Data Table** - Detail dengan confidence intervals
- **🔮 Forecasting Modal** - Custom forecast generation

### 📁 Kontrol Data

- **📤 Upload File Massal** - Drag & drop CSV/Excel dengan validasi otomatis
- **✏️ Input Manual** - Tambah data IPH dan komoditas per minggu
- **📊 Historical Data Table** - Tampilan data historis dengan pagination
- **🔄 Model Retraining** - Retrain semua model dengan data terbaru
- **📥 Template Download** - Download template CSV untuk format yang benar
- **✅ Data Validation** - Validasi komprehensif dengan error handling

### 📊 Visualisasi Data

- **📈 Moving Averages** - MA 3, 7, 14, 30 hari
- **📊 Volatility Analysis** - Rolling std dengan risk assessment
- **🤖 Model Performance** - Trend akurasi, forecast vs actual

### 🌾 Commodity Insights

- **📅 Current Week Insights** - Dampak komoditas minggu ini dengan kategori breakdown
- **📊 Analisis Bulanan** - Analisis detail per bulan dengan filter tahun, top komoditas, dan statistik IPH
- **📈 Commodity Trends** - Trend analisis untuk 1 bulan, 3 bulan, 6 bulan, dan 1 tahun
- **🏆 Volatility Ranking** - Ranking komoditas paling volatile dengan threshold multi-level
- **⚠️ Volatility Alerts** - Peringatan volatilitas dengan threshold yang dapat disesuaikan
- **🌍 Seasonal Patterns** - Pola musiman per bulan dengan kategori dominan
- **📊 Impact Ranking** - Ranking komoditas berdasarkan total impact dan frekuensi muncul

### 🔔 Alert System

- **📊 Statistical Alerts** - 2σ & 3σ boundary detection
- **⚙️ Custom Rules** - Admin-defined rules (admin only)
- **📜 Alert History** - Unlimited dengan pagination & filter
- **🔍 Recent Alerts** - Real-time alerts dengan priority

***

## 🤖 Machine Learning Details

### Model Specifications

| Model | Type | Parameters | Use Case |
| --- | --- | --- | --- |
| **KNN** | Instance-based | n_neighbors=5, weights='distance' | Pattern matching |
| **Random Forest** | Ensemble | n_estimators=100, max_depth=4, min_samples_leaf=3 | Robust predictions |
| **LightGBM** | Gradient Boosting | learning_rate=0.05, max_depth=3, num_leaves=15 | Fast training |
| **XGBoost Advanced** | Gradient Boosting | learning_rate=0.08, max_depth=3, early_stopping=10 | High accuracy |
| **Ensemble** | Weighted Average | weights=inverse_mae | Best accuracy |

### Feature Engineering

```python
Features = [
    'Lag_1', 'Lag_2', 'Lag_3', 'Lag_4',  
    'MA_3', 'MA_7'                        
]
```

### Performance Metrics

- **MAE** - Primary selection criteria (lower is better)
- **RMSE** - Secondary metric dengan penalty untuk error besar
- **R²** - Goodness of fit (0-1 range)
- **MAPE** - Relative error dalam persentase
- **CV Score** - Cross-validation score

### Forecasting Method

```javascript
Method: Deterministic Recursive Multi-step
- Seed: Fixed (42) untuk reproducibility
- Confidence Interval: 95% (multiplier 1.96)
- Feature Update: Exponential weighting untuk MA
- Uncertainty: Historical volatility-based
```

### Training Validation

```javascript
Time Series Cross-Validation (Walk-forward):
- Split 1: Train [0:70%], Test [70%:80%]
- Split 2: Train [0:80%], Test [80%:90%]
- Split 3: Train [0:90%], Test [90%:100%]
```

***

## 🛠️ Technical Stack

### Backend

- **Framework**: Flask 2.3.3
- **Database**: SQLite 3 (SQLAlchemy ORM)
- **ML**: scikit-learn 1.3.0, LightGBM 4.0.0, XGBoost 1.7.6
- **Data**: Pandas 2.0.3, NumPy 1.24.3
- **Utilities**: python-dateutil 2.8.2, openpyxl 3.1.2

### Frontend

- **UI Framework**: Bootstrap 5
- **Charts**: Plotly.js 5.15.0
- **Icons**: Font Awesome 6.4.0
- **JavaScript**: ES6+ dengan async/await

### Infrastructure

- **Database**: SQLite (file-based)
- **Server**: Flask development server (production: use Gunicorn)
- **Port**: 5001

***

## 📊 Data Requirements

### IPH Data (Required)

```javascript
Columns: Tanggal, Indikator_Harga
Format:  Date (YYYY-MM-DD), Float (%)

Minimum: 10 records (recommended: 50+)
Frequency: Weekly
```

### Commodity Data (Optional)

```javascript
Columns:
- Bulan: Month name (e.g., "Januari '24")
- Minggu ke-: Week (e.g., "M1", "M2")
- Indikator Perubahan Harga (%): IPH value
- Komoditas Andil Perubahan Harga: "KOMODITAS(nilai);..." format
- Komoditas Fluktuasi Harga Tertinggi: Most volatile commodity
- Fluktuasi Harga: Volatility value (0-1)
```

***

## 🔌 API Endpoints

### Core APIs

```javascript
POST   /api/upload-data                    # Upload & process data
POST   /api/add-manual-record              # Add single IPH record
POST   /api/add-manual-record              # Add IPH + commodity
POST   /api/retrain-models                 # Retrain all models
GET    /api/forecast-chart-data            # Get chart data
POST   /api/generate-forecast              # Custom forecast
GET    /api/available-models               # List available models
GET    /api/model-comparison-chart         # Model performance
```

### Visualization APIs

```javascript
GET    /api/visualization/moving-averages  # MA analysis
GET    /api/visualization/volatility       # Volatility analysis
GET    /api/visualization/model-performance # Model performance
```

### Commodity APIs

```javascript
GET    /api/commodity/current-week         # Current week insights
GET    /api/commodity/monthly-analysis     # Monthly analysis
GET    /api/commodity/trends               # Commodity trends
GET    /api/commodity/seasonal             # Seasonal patterns
GET    /api/commodity/alerts               # Volatility alerts
POST   /api/commodity/upload               # Upload commodity data
GET    /api/commodity/data-status          # Data availability
```

### Alert APIs

```javascript
GET    /api/economic-alerts                # Real-time alerts
GET    /api/alerts/statistical             # Statistical alerts
GET    /api/alerts/recent                  # Recent alert history
```

### Admin APIs

```javascript
GET    /api/admin/stats                    # Dashboard statistics
GET    /api/admin/recent-alerts            # Recent alerts
GET    /api/admin/alert-stats              # Alert statistics
GET    /api/admin/alert-rules              # List alert rules
POST   /api/admin/alert-rules              # Create alert rule
PUT    /api/admin/alert-rules/<id>         # Update alert rule
DELETE /api/admin/alert-rules/<id>         # Delete alert rule
GET    /api/admin/alert-history            # Alert history (paginated)
GET    /api/admin/alert-history/export     # Export alerts to CSV
```

***

## ⚙️ Configuration

### Environment Variables (Recommended)

```bash
# Create .env file
DATABASE_URL=sqlite:///data/prisma.db
SECRET_KEY=your-secret-key-here
DEBUG=False
ENVIRONMENT=production
```

### Config File (config.py)

```python
# Flask Configuration
SECRET_KEY = 'iph-forecasting-secret-key-2024'
DEBUG = True

# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/prisma.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# File Upload
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Forecasting
FORECAST_MIN_WEEKS = 4
FORECAST_MAX_WEEKS = 12
DEFAULT_FORECAST_WEEKS = 8

# Performance
MODEL_PERFORMANCE_THRESHOLD = 0.1  # 10%
AUTO_RETRAIN_THRESHOLD = 50  # records
```

***

## 🐛 Troubleshooting

### Database Issues

```javascript
Error: "The current Flask app is not registered with this 'SQLAlchemy' instance"
Solution: Ensure db.init_app(app) is called in app.py
```

### Data Upload Fails

- ✅ Supported: `.csv`, `.xlsx` (max 16MB)
- ✅ Required: `Tanggal`, `Indikator_Harga` columns
- ✅ Encoding: UTF-8, Latin-1, CP1252 auto-detected
- ❌ Not supported: `.xls`, `.txt`

### Model Training Issues

- Minimum data: 10 records (recommended: 50+)
- Check: Date format (YYYY-MM-DD), numeric values
- Outliers: Extreme values (>50%, <-50%) will be flagged

### Charts Not Loading

1. Check browser console (F12)
2. Clear cache (Ctrl+F5 hard refresh)
3. Verify API endpoints responding (Network tab)
4. Check data availability in database

### Port Already in Use

```bash
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=5002)
```

***

## 📈 Performance Benchmarks

### Model Accuracy (Typical)

- **XGBoost Advanced**: MAE ~0.09-0.12, R² ~0.87-0.92
- **LightGBM**: MAE ~0.10-0.14, R² ~0.82-0.90
- **Random Forest**: MAE ~0.12-0.16, R² ~0.78-0.88
- **KNN**: MAE ~0.15-0.20, R² ~0.70-0.85
- **Ensemble**: MAE ~0.08-0.11, R² ~0.88-0.93

### System Performance

- **Training Time**: 1-5 seconds per model
- **Forecast Generation**: <1 second untuk 8 weeks
- **Dashboard Load**: 2-3 seconds dengan caching
- **Memory Usage**: 200-500MB (depends on data size)
- **Database Queries**: <100ms untuk most operations

***

## 🔐 Security & Backup

### Auto Backup System

```javascript
Backup Location: data/db_backups/
Retention: 30 days
Trigger: Before any data modification
Format: CSV + metadata JSON
```

### Data Validation

- Format validation dengan multiple encoding support
- Numeric conversion dengan outlier detection
- Date parsing dengan comprehensive error handling
- Data quality scoring

### Database Security

- SQLite file-based dengan proper permissions
- SQLAlchemy ORM untuk SQL injection prevention
- Admin system untuk sensitive operations
- Operation logging untuk audit trail

***

## 🚨 Known Limitations & Future Work

### Current Limitations

- ❌ Single-threaded (ML models use n_jobs=1)
- ❌ Admin authentication system belum sepenuhnya diimplementasi (rancangan sudah ada)
- ❌ Debug mode enabled di default (production: set DEBUG=False)
- ❌ No rate limiting untuk API endpoints
- ❌ Visitor/admin access control masih dalam tahap pengembangan

### Planned Improvements (v2.1+)

- ✅ **Visitor/Admin System** - Implementasi lengkap akses pengunjung dan admin
  - Public pages: Dashboard, Visualization, Commodity Insights, Alerts (read-only)
  - Admin pages: Data Control, Model Management, Alert Rules Management
  - Generate Forecast tersedia untuk semua pengunjung (fitur utama)
- ✅ Production-ready WSGI deployment (Gunicorn)
- ✅ API authentication & rate limiting
- ✅ Docker containerization
- ✅ Redis caching layer
- ✅ Advanced logging & monitoring
- ✅ Unit & integration tests
- ✅ API documentation (Swagger/OpenAPI)

***

## 📞 Support & Documentation

### Getting Help

- 📖 **README**: Dokumentasi lengkap (file ini)
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Tanya-jawab di GitHub Discussions
- 📧 **Email**: Contact project maintainer

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python**: 3.8+ (3.10 recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+

***

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

***

## 🙏 Acknowledgments

- **scikit-learn** - Machine learning algorithms
- **Plotly** - Interactive visualizations
- **Bootstrap** - UI framework
- **Flask** - Web framework
- **Pandas** - Data manipulation
- **LightGBM & XGBoost** - Advanced gradient boosting

***

## 📊 Version History

### v2.0.0 (Current) - Database Integration & Enhanced Features

- ✅ SQLite database integration (6 tables: IPHData, CommodityData, ModelPerformance, AlertHistory, AlertRule, AdminUser)
- ✅ Database-first data operations dengan auto-backup
- ✅ Commodity database integration dengan parsing otomatis
- ✅ Enhanced forecasting engine dengan recursive features
- ✅ Real-time economic alerts (2σ, 3σ boundaries)
- ✅ Commodity insights lengkap (weekly, monthly, trends, seasonal)
- ✅ Admin dashboard & login system (dasar)
- ✅ **Indonesian Localization** - Semua interface dalam bahasa Indonesia
- ✅ **Data Quality Improvements** - Filter tahun/bulan yang lebih ketat untuk menghindari pencampuran data
- ✅ **Commodity Data Fix** - Perbaikan parsing dan matching data komoditas dengan IPH data

### v1.0.0 - Initial Release

- Basic forecasting functionality
- 4 ML models
- CSV data upload
- Interactive dashboard
- Basic visualization

***

**🎯 PRISMA v2.0** - Platform forecasting IPH terpadu dengan database, ML engine, dan dashboard interaktif.

### ✨ Highlights

- **🤖 4 Model ML** dengan Ensemble Learning untuk akurasi optimal
- **📊 Database Terintegrasi** dengan 6 tabel untuk data, model, dan alerts
- **🌾 Analisis Komoditas** lengkap dengan parsing otomatis dan kategori impact
- **📈 Dashboard Interaktif** dengan visualisasi real-time menggunakan Plotly.js
- **🇮🇩 Bahasa Indonesia** - Semua interface dalam bahasa Indonesia (kecuali judul PRISMA)
- **👥 Akses Publik** - Semua pengunjung dapat mengakses fitur utama termasuk Generate Forecast

*Dibangun untuk akurasi tinggi, kemudahan penggunaan, dan pengalaman pengguna yang optimal.*
