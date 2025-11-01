"""
Utility functions untuk authentication
"""

import bcrypt
from datetime import datetime
from flask_login import UserMixin
from database import db, AdminUser

class User(UserMixin):
    """User class untuk Flask-Login"""
    def __init__(self, user_id, username, email, is_active):
        self.id = user_id
        self.username = username
        self.email = email
        # is_active is a property from UserMixin, use _is_active as internal storage
        self._is_active = is_active
    
    @property
    def is_active(self):
        """Return active status"""
        return getattr(self, '_is_active', True)
    
    @is_active.setter
    def is_active(self, value):
        """Set active status"""
        self._is_active = value

def load_user(user_id):
    """Load user dari database untuk Flask-Login"""
    try:
        admin_user = AdminUser.query.get(int(user_id))
        if admin_user and admin_user.is_active:
            return User(
                user_id=admin_user.id,
                username=admin_user.username,
                email=admin_user.email,
                is_active=admin_user.is_active
            )
    except Exception:
        pass
    return None

def hash_password(password):
    """Hash password menggunakan bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password_hash, password):
    """Verify password dengan hash"""
    try:
        if not password_hash or not password:
            return False
        
        # Check if hash is in bcrypt format
        if not password_hash.startswith('$2b$') and not password_hash.startswith('$2a$') and not password_hash.startswith('$2y$'):
            print(f"WARNING: Password hash is not in bcrypt format: {password_hash[:20]}...")
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        print(f"ERROR in check_password: {e}")
        return False

def update_last_login(user_id):
    """Update last login timestamp"""
    try:
        admin_user = AdminUser.query.get(user_id)
        if admin_user:
            admin_user.last_login = datetime.utcnow()
            db.session.commit()
    except Exception:
        db.session.rollback()

def create_admin_user(username, password, email=None):
    """Create new admin user"""
    try:
        # Check if user exists
        existing = AdminUser.query.filter_by(username=username).first()
        if existing:
            return None, "Username sudah digunakan"
        
        if email:
            existing_email = AdminUser.query.filter_by(email=email).first()
            if existing_email:
                return None, "Email sudah digunakan"
        
        # Create new user
        password_hash = hash_password(password)
        admin_user = AdminUser(
            username=username,
            password_hash=password_hash,
            email=email,
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        return admin_user, "User berhasil dibuat"
    except Exception as e:
        db.session.rollback()
        return None, f"Error: {str(e)}"

