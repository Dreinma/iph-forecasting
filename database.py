from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class IPHData(db.Model):
    """Model untuk data IPH historis - Terintegrasi dengan data komoditas"""
    __tablename__ = 'iph_data'
    
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False, unique=True, index=True)
    indikator_harga = db.Column(db.Float, nullable=False)
    
    # Metadata columns - Sesuai format CSV
    bulan = db.Column(db.String(50), nullable=False, index=True)
    minggu = db.Column(db.String(10), nullable=True, index=True)  # M1, M2, M3, M4, M5
    tahun = db.Column(db.Integer, index=True)
    bulan_numerik = db.Column(db.Integer)
    kab_kota = db.Column(db.String(100), default='BATU')
    
    # Feature columns untuk ML
    lag_1 = db.Column(db.Float)
    lag_2 = db.Column(db.Float)
    lag_3 = db.Column(db.Float)
    lag_4 = db.Column(db.Float)
    ma_3 = db.Column(db.Float)
    ma_7 = db.Column(db.Float)
    
    # Audit columns
    data_source = db.Column(db.String(50), default='uploaded')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<IPHData {self.tanggal}: {self.indikator_harga}%>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'indikator_harga': float(self.indikator_harga) if self.indikator_harga else None,
            'bulan': self.bulan,
            'minggu': self.minggu,
            'tahun': self.tahun,
            'bulan_numerik': self.bulan_numerik,
            'kab_kota': self.kab_kota,
            'lag_1': float(self.lag_1) if self.lag_1 else None,
            'lag_2': float(self.lag_2) if self.lag_2 else None,
            'lag_3': float(self.lag_3) if self.lag_3 else None,
            'lag_4': float(self.lag_4) if self.lag_4 else None,
            'ma_3': float(self.ma_3) if self.ma_3 else None,
            'ma_7': float(self.ma_7) if self.ma_7 else None,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }



class CommodityData(db.Model):
    """Model untuk data komoditas - Terintegrasi dengan IPH"""
    __tablename__ = 'commodity_data'
    
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False, index=True)
    
    # Period info - Sesuai format CSV
    bulan = db.Column(db.String(50), nullable=False, index=True)
    minggu = db.Column(db.String(10), nullable=False, index=True)
    tahun = db.Column(db.Integer, index=True)
    kab_kota = db.Column(db.String(100), default='BATU')
    
    # IPH info (reference ke IPHData)
    iph_id = db.Column(db.Integer, db.ForeignKey('iph_data.id'), nullable=True)
    iph_value = db.Column(db.Float)  # Denormalized untuk performa
    
    # Commodity info - Sesuai format CSV
    komoditas_andil = db.Column(db.Text)  # Format: "KOMODITAS(nilai);KOMODITAS(nilai)"
    komoditas_fluktuasi = db.Column(db.String(200))  # Komoditas paling volatile
    nilai_fluktuasi = db.Column(db.Float)  # Nilai volatilitas
    
    # Audit columns
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes untuk query performance
    __table_args__ = (
        db.Index('idx_commodity_date_bulan', 'tanggal', 'bulan'),
        db.Index('idx_commodity_tahun_bulan', 'tahun', 'bulan'),
        db.Index('idx_commodity_minggu', 'minggu'),
    )
    
    def __repr__(self):
        return f'<CommodityData {self.bulan} {self.minggu}: IPH {self.iph}%>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tanggal': self.tanggal.strftime('%Y-%m-%d') if self.tanggal else None,
            'bulan': self.bulan,
            'minggu': self.minggu,
            'tahun': self.tahun,
            'kab_kota': self.kab_kota,
            'iph_id': self.iph_id,
            'iph_value': float(self.iph_value) if self.iph_value else None,
            'komoditas_andil': self.komoditas_andil,
            'komoditas_fluktuasi': self.komoditas_fluktuasi,
            'nilai_fluktuasi': float(self.nilai_fluktuasi) if self.nilai_fluktuasi else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }



class ModelPerformance(db.Model):
    """Model untuk tracking model performance history"""
    __tablename__ = 'model_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Model info
    model_name = db.Column(db.String(100), nullable=False, index=True)
    batch_id = db.Column(db.String(200))
    
    # Performance metrics
    mae = db.Column(db.Float, nullable=False)
    rmse = db.Column(db.Float)
    r2_score = db.Column(db.Float)
    cv_score = db.Column(db.Float)
    mape = db.Column(db.Float)
    
    # Training info
    training_time = db.Column(db.Float)
    data_size = db.Column(db.Integer)
    test_size = db.Column(db.Integer)
    is_best = db.Column(db.Boolean, default=False)
    
    # Feature importance (stored as JSON)
    feature_importance = db.Column(db.Text)  # JSON array
    
    # Timestamps
    trained_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index untuk performance queries
    __table_args__ = (
        db.Index('idx_model_performance', 'model_name', 'trained_at'),
        db.Index('idx_best_models', 'is_best', 'mae'),
    )
    
    def __repr__(self):
        return f'<ModelPerformance {self.model_name}: MAE {self.mae:.4f}>'
    
    def to_dict(self):
        """Convert to dictionary - FIXED JSON PARSING"""
        # Parse feature_importance dengan aman
        feature_imp = None
        if self.feature_importance:
            if isinstance(self.feature_importance, str):
                try:
                    feature_imp = json.loads(self.feature_importance)
                except (json.JSONDecodeError, TypeError):
                    feature_imp = None
            else:
                # Sudah list/dict (PostgreSQL JSONB)
                feature_imp = self.feature_importance
        
        return {
            'id': self.id,
            'model_name': self.model_name,
            'batch_id': self.batch_id,
            'mae': float(self.mae) if self.mae else None,
            'rmse': float(self.rmse) if self.rmse else None,
            'r2_score': float(self.r2_score) if self.r2_score else None,
            'cv_score': float(self.cv_score) if self.cv_score else None,
            'mape': float(self.mape) if self.mape else None,
            'training_time': float(self.training_time) if self.training_time else None,
            'data_size': self.data_size,
            'test_size': self.test_size,
            'is_best': self.is_best,
            'feature_importance': feature_imp,  # ✅ Sudah diparsing
            'trained_at': self.trained_at.isoformat() if self.trained_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AdminUser(db.Model):
    """Model untuk admin users"""
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    reset_token = db.Column(db.String(255), nullable=True)  # Token untuk reset password
    reset_token_expiry = db.Column(db.DateTime, nullable=True)  # Waktu kadaluarsa token
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class AlertHistory(db.Model):
    """Model untuk alert history - Enhanced untuk admin system"""
    __tablename__ = 'alert_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Alert info
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    
    # Alert data
    value = db.Column(db.Float)
    threshold = db.Column(db.Float)
    
    # Status - Enhanced untuk admin
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    acknowledged_by = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)  # Alert masih aktif atau tidak
    
    # Admin management
    created_by_system = db.Column(db.Boolean, default=True)  # True = auto, False = manual
    admin_notes = db.Column(db.Text)  # Catatan admin
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_alert_type_severity', 'alert_type', 'severity'),
        db.Index('idx_alert_created', 'created_at'),
        db.Index('idx_alert_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<AlertHistory {self.alert_type}: {self.severity}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'value': float(self.value) if self.value else None,
            'threshold': float(self.threshold) if self.threshold else None,
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AlertRule(db.Model):
    """Model untuk aturan peringatan yang bisa dikelola admin"""
    __tablename__ = 'alert_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Rule info
    rule_name = db.Column(db.String(100), nullable=False, unique=True)
    rule_type = db.Column(db.String(50), nullable=False)  # 'threshold', 'volatility', 'trend'
    is_active = db.Column(db.Boolean, default=True)
    
    # Rule parameters
    threshold_value = db.Column(db.Float)  # Nilai threshold
    comparison_operator = db.Column(db.String(10))  # '>', '<', '>=', '<=', '=='
    severity_level = db.Column(db.String(20), nullable=False)  # 'info', 'warning', 'critical'
    
    # Rule conditions
    check_period_days = db.Column(db.Integer, default=7)  # Periode pengecekan
    min_data_points = db.Column(db.Integer, default=5)  # Minimum data points
    
    # Admin management
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<AlertRule {self.rule_name}: {self.rule_type}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'is_active': self.is_active,
            'threshold_value': float(self.threshold_value) if self.threshold_value else None,
            'comparison_operator': self.comparison_operator,
            'severity_level': self.severity_level,
            'check_period_days': self.check_period_days,
            'min_data_points': self.min_data_points,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'description': self.description
        }


class ActivityLog(db.Model):
    """Model untuk activity log / audit trail"""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User info
    user_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    username = db.Column(db.String(100), nullable=False)
    
    # Activity info
    action_type = db.Column(db.String(50), nullable=False, index=True)  # 'train', 'upload', 'delete', 'edit', etc.
    entity_type = db.Column(db.String(50), nullable=False)  # 'model', 'data', 'alert', etc.
    description = db.Column(db.Text)
    
    # Additional metadata (stored as JSON)
    activity_metadata = db.Column(db.Text)  # JSON string for additional info (metadata is reserved in SQLAlchemy)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_activity_user', 'user_id', 'created_at'),
        db.Index('idx_activity_type', 'action_type', 'created_at'),
    )
    
    def __repr__(self):
        return f'<ActivityLog {self.action_type} by {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action_type': self.action_type,
            'entity_type': self.entity_type,
            'description': self.description,
            'metadata': json.loads(self.activity_metadata) if self.activity_metadata else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ForecastHistory(db.Model):
    """Model untuk menyimpan riwayat forecast yang telah dibuat"""
    __tablename__ = 'forecast_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Forecast info
    model_name = db.Column(db.String(100), nullable=False, index=True)
    forecast_weeks = db.Column(db.Integer, nullable=False)  # Jumlah minggu yang di-forecast
    
    # Forecast data (stored as JSON)
    forecast_data = db.Column(db.Text)  # JSON array of forecast values
    confidence_intervals = db.Column(db.Text)  # JSON array of confidence intervals
    
    # Statistics
    avg_prediction = db.Column(db.Float)  # Rata-rata nilai prediksi
    trend = db.Column(db.String(20))  # 'up', 'down', 'stable'
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    
    # Performance info (if validation available)
    validation_mae = db.Column(db.Float)
    validation_rmse = db.Column(db.Float)
    
    # Metadata
    data_points_used = db.Column(db.Integer)  # Jumlah data yang digunakan untuk training
    created_by = db.Column(db.String(100))  # Username atau 'system'
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_forecast_model_date', 'model_name', 'created_at'),
        db.Index('idx_forecast_date', 'created_at'),
    )
    
    def __repr__(self):
        return f'<ForecastHistory {self.model_name}: {self.forecast_weeks} weeks>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_name': self.model_name,
            'forecast_weeks': self.forecast_weeks,
            'forecast_data': json.loads(self.forecast_data) if self.forecast_data else None,
            'confidence_intervals': json.loads(self.confidence_intervals) if self.confidence_intervals else None,
            'avg_prediction': float(self.avg_prediction) if self.avg_prediction else None,
            'trend': self.trend,
            'min_value': float(self.min_value) if self.min_value else None,
            'max_value': float(self.max_value) if self.max_value else None,
            'validation_mae': float(self.validation_mae) if self.validation_mae else None,
            'validation_rmse': float(self.validation_rmse) if self.validation_rmse else None,
            'data_points_used': self.data_points_used,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def init_db(app):
    """Initialize database dengan Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print(" Database tables created successfully!")
        
        # Print table info
        print(f" Tables created:")
        print(f"   - {IPHData.__tablename__}")
        print(f"   - {CommodityData.__tablename__}")
        print(f"   - {ModelPerformance.__tablename__}")
        print(f"   - {AlertHistory.__tablename__}")
        print(f"   - {AdminUser.__tablename__}")
        print(f"   - {AlertRule.__tablename__}")
        print(f"   - {ActivityLog.__tablename__}")
        print(f"   - {ForecastHistory.__tablename__}")


def get_db_stats():
    """Get database statistics"""
    try:
        stats = {
            'iph_records': IPHData.query.count(),
            'commodity_records': CommodityData.query.count(),
            'model_performances': ModelPerformance.query.count(),
            'alert_history': AlertHistory.query.count(),
            'admin_users': AdminUser.query.count(),
            'alert_rules': AlertRule.query.count(),
            'active_alerts': AlertHistory.query.filter_by(is_active=True).count(),
            'latest_iph_date': db.session.query(db.func.max(IPHData.tanggal)).scalar(),
            'earliest_iph_date': db.session.query(db.func.min(IPHData.tanggal)).scalar(),
            'best_models': ModelPerformance.query.filter_by(is_best=True).count()
        }
        return stats
    except Exception as e:
        print(f" Error getting DB stats: {e}")
        return {}