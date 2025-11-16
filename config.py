import os
import tempfile
from datetime import timedelta

class Config:
    """Base configuration - shared across all environments"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'iph-forecasting-secret-key-2024'
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ✅ Database Configuration - PostgreSQL Supabase
    # Same untuk development & production!
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Database Connection Pool
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    
    # Base paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    MODELS_PATH = os.path.abspath(os.path.join(BASE_DIR, 'data', 'models'))
    
    # Model Configuration
    FORECAST_MIN_WEEKS = 4
    FORECAST_MAX_WEEKS = 12
    DEFAULT_FORECAST_WEEKS = 8
    
    # Performance Configuration
    MODEL_PERFORMANCE_THRESHOLD = 0.1
    AUTO_RETRAIN_THRESHOLD = 50
    MAX_PERFORMANCE_HISTORY_PER_MODEL = 50
    PERFORMANCE_CLEANUP_ENABLED = True
    
    # Dashboard Configuration
    CHART_HEIGHT = 500
    COMPARISON_CHART_HEIGHT = 400
    MAX_HISTORICAL_DISPLAY = 60
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    VERBOSE_LOGGING = os.environ.get('VERBOSE_LOGGING', 'false').lower() == 'true'
    
    # Cache Configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        directories_to_create = []
        
        if app.config.get('UPLOAD_FOLDER'):
            directories_to_create.append(app.config['UPLOAD_FOLDER'])
        
        if app.config.get('FLASK_ENV') != 'production':
            if app.config.get('DATA_FOLDER'):
                directories_to_create.append(app.config['DATA_FOLDER'])
            if app.config.get('BACKUPS_PATH'):
                directories_to_create.append(app.config['BACKUPS_PATH'])
        
        for directory in directories_to_create:
            try:
                os.makedirs(directory, exist_ok=True)
            except OSError:
                pass
        
        # Initialize database
        from database import init_db
        init_db(app)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'
    SQLALCHEMY_ECHO = True  # Show SQL queries
    
    # Session - allow HTTP in development
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = False
    
    # ✅ File paths - Local development (writable)
    UPLOAD_FOLDER = os.path.abspath(os.path.join(Config.BASE_DIR, 'static', 'uploads'))
    DATA_FOLDER = os.path.abspath(os.path.join(Config.BASE_DIR, 'data'))
    BACKUPS_PATH = os.path.abspath(os.path.join(Config.BASE_DIR, 'data', 'backups'))

class ProductionConfig(Config):
    """Production configuration - Vercel"""
    DEBUG = False
    FLASK_ENV = 'production'
    SQLALCHEMY_ECHO = False
    
    # Session - HTTPS required
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = True
    
    # ✅ File paths - Vercel serverless
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'iph_uploads')
    DATA_FOLDER = os.path.abspath(os.path.join(Config.BASE_DIR, 'data'))
    BACKUPS_PATH = None  # Disabled in production
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()
    
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        
        # Production logging
        import logging
        from logging import StreamHandler
        
        stream_handler = StreamHandler()
        stream_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        # Create /tmp upload folder
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    FLASK_ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/test_prisma.db'
    UPLOAD_FOLDER = os.path.abspath(os.path.join(Config.BASE_DIR, 'static', 'uploads'))
    DATA_FOLDER = os.path.abspath(os.path.join(Config.BASE_DIR, 'data'))


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}