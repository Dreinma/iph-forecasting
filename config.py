import os
from datetime import timedelta
import logging

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'iph-forecasting-secret-key-2024'
    DEBUG = True
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)  # Session timeout 5 menit jika tidak ada aktivitas
    
    # Kredensial database Laragon Anda
    DB_USER = "root"
    DB_PASS = ""  # Passwordnya kosong
    DB_HOST = "127.0.0.1" # Ini adalah localhost
    DB_PORT = "3306"
    DB_NAME = "prisma_db" # <-- GANTI INI dengan nama DB yang Anda impor


    #  Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                            f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True for SQL query debugging
    
    #  Database Connection Pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # File Upload Configuration - Use absolute paths for production
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    
    # Data Storage Configuration - Use absolute paths for production
    DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    HISTORICAL_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'historical_data.csv'))  # Legacy backup
    COMMODITY_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'IPH-Kota-Batu.csv'))     # Legacy backup
    MODELS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'models'))
    BACKUPS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'backups'))
    
    #  Database Backup Configuration
    DB_BACKUP_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'db_backups'))
    DB_BACKUP_RETENTION_DAYS = 30
    AUTO_BACKUP_ENABLED = True
    
    # Model Configuration
    FORECAST_MIN_WEEKS = 4
    FORECAST_MAX_WEEKS = 12
    DEFAULT_FORECAST_WEEKS = 8
    
    # Performance Configuration
    MODEL_PERFORMANCE_THRESHOLD = 0.1  # 10% improvement threshold
    AUTO_RETRAIN_THRESHOLD = 50  # Retrain when new data > 50 records
    
    #  Performance History Configuration
    MAX_PERFORMANCE_HISTORY_PER_MODEL = 50  # Keep last 50 training records
    PERFORMANCE_CLEANUP_ENABLED = True
    
    # Dashboard Configuration
    CHART_HEIGHT = 500
    COMPARISON_CHART_HEIGHT = 400
    MAX_HISTORICAL_DISPLAY = 60
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()  # DEBUG, INFO, WARNING, ERROR
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    VERBOSE_LOGGING = os.environ.get('VERBOSE_LOGGING', 'false').lower() == 'true'  # Show last 60 periods in chart
    
    #  Cache Configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    #  Migration Configuration
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
        
        print(" Application directories initialized")
        
        #  Initialize database
        from database import init_db
        init_db(app)
        
        print(" Database initialized")

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Show SQL queries in development

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_urlsafe(32)
    SQLALCHEMY_ECHO = False
    
    # Production database - Use environment variable or fallback to SQLite
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    else:
        # Fallback to SQLite with absolute path
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "prisma.db"))}'
    
    # Security settings for production
    # Set SESSION_COOKIE_SECURE = False via env var if not using HTTPS
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)  # 1 hour session timeout
    
    # Logging for production - default to WARNING to reduce noise
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()

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