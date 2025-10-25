import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'iph-forecasting-secret-key-2024'
    DEBUG = True
    
    # 🆕 Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///C:/VSCode/iph_forecasting_app/data/prisma.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True for SQL query debugging
    
    # 🆕 Database Connection Pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    
    # Data Storage Configuration (Legacy - for backup/export)
    DATA_FOLDER = 'data'
    HISTORICAL_DATA_PATH = 'data/historical_data.csv'  # Legacy backup
    COMMODITY_DATA_PATH = 'data/IPH-Kota-Batu.csv'     # Legacy backup
    MODELS_PATH = 'data/models/'
    BACKUPS_PATH = 'data/backups/'
    
    # 🆕 Database Backup Configuration
    DB_BACKUP_FOLDER = 'data/db_backups/'
    DB_BACKUP_RETENTION_DAYS = 30
    AUTO_BACKUP_ENABLED = True
    
    # Model Configuration
    FORECAST_MIN_WEEKS = 4
    FORECAST_MAX_WEEKS = 12
    DEFAULT_FORECAST_WEEKS = 8
    
    # Performance Configuration
    MODEL_PERFORMANCE_THRESHOLD = 0.1  # 10% improvement threshold
    AUTO_RETRAIN_THRESHOLD = 50  # Retrain when new data > 50 records
    
    # 🆕 Performance History Configuration
    MAX_PERFORMANCE_HISTORY_PER_MODEL = 50  # Keep last 50 training records
    PERFORMANCE_CLEANUP_ENABLED = True
    
    # Dashboard Configuration
    CHART_HEIGHT = 500
    COMPARISON_CHART_HEIGHT = 400
    MAX_HISTORICAL_DISPLAY = 60  # Show last 60 periods in chart
    
    # 🆕 Cache Configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # 🆕 Migration Configuration
    MIGRATION_BACKUP_ENABLED = True
    KEEP_CSV_AFTER_MIGRATION = True  # Keep CSV files as backup
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        directories = [
            Config.UPLOAD_FOLDER,
            Config.DATA_FOLDER,
            Config.MODELS_PATH,
            Config.BACKUPS_PATH,
            Config.DB_BACKUP_FOLDER
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        print("✅ Application directories initialized")
        
        # 🆕 Initialize database
        from database import init_db
        init_db(app)
        
        print("✅ Database initialized")

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Show SQL queries in development

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-change-this'
    SQLALCHEMY_ECHO = False
    
    # Production database (example: PostgreSQL)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'postgresql://user:password@localhost/prisma_db'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/test_prisma.db'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}