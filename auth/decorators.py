"""
Decorators untuk proteksi route admin
"""

from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user

def login_required(f):
    """Decorator untuk memastikan user sudah login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator untuk memastikan user adalah admin yang aktif"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('admin.login', next=request.url))
        
        if not current_user.is_active:
            flash('Akun Anda tidak aktif. Hubungi administrator.', 'danger')
            return redirect(url_for('admin.login'))
        
        return f(*args, **kwargs)
    return decorated_function

