"""
Forms untuk authentication
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from database import AdminUser

class LoginForm(FlaskForm):
    """Form untuk admin login"""
    username = StringField('Username', validators=[
        DataRequired(message='Username harus diisi'),
        Length(min=3, max=50, message='Username harus 3-50 karakter')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password harus diisi'),
        Length(min=8, message='Password minimal 8 karakter')
    ])
    remember_me = BooleanField('Ingat saya')

class ChangePasswordForm(FlaskForm):
    """Form untuk change password"""
    current_password = PasswordField('Password Saat Ini', validators=[
        DataRequired(message='Password saat ini harus diisi')
    ])
    new_password = PasswordField('Password Baru', validators=[
        DataRequired(message='Password baru harus diisi'),
        Length(min=8, message='Password minimal 8 karakter')
    ])
    confirm_password = PasswordField('Konfirmasi Password Baru', validators=[
        DataRequired(message='Konfirmasi password harus diisi'),
        EqualTo('new_password', message='Password tidak cocok')
    ])

class CreateAdminForm(FlaskForm):
    """Form untuk create admin user"""
    username = StringField('Username', validators=[
        DataRequired(message='Username harus diisi'),
        Length(min=3, max=50, message='Username harus 3-50 karakter')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email harus diisi'),
        Email(message='Format email tidak valid'),
        Length(max=100, message='Email maksimal 100 karakter')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password harus diisi'),
        Length(min=8, message='Password minimal 8 karakter')
    ])
    confirm_password = PasswordField('Konfirmasi Password', validators=[
        DataRequired(message='Konfirmasi password harus diisi'),
        EqualTo('password', message='Password tidak cocok')
    ])
    
    def validate_username(self, field):
        """Validate unique username"""
        user = AdminUser.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('Username sudah digunakan')
    
    def validate_email(self, field):
        """Validate unique email"""
        if field.data:
            user = AdminUser.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError('Email sudah digunakan')

