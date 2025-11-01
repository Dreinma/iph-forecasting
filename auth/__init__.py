"""
Authentication module untuk IPH Forecasting Platform
Mengelola autentikasi admin dan session management
"""

from flask_login import LoginManager

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message = 'Silakan login untuk mengakses halaman admin.'
login_manager.login_message_category = 'info'

def init_auth(app):
    """Initialize authentication with Flask app"""
    login_manager.init_app(app)
    
    # Import user loader
    from auth.utils import load_user
    login_manager.user_loader(load_user)

