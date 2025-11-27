"""
Admin routes untuk IPH Forecasting Platform
VERSI PRODUCTION (Login Aman dengan Autentikasi Database)
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from auth.decorators import admin_required
from auth.forms import LoginForm, ChangePasswordForm, CreateAdminForm
from auth.utils import check_password, update_last_login, create_admin_user, hash_password, User
from database import db, AdminUser, IPHData, CommodityData, ForecastHistory, AlertHistory, ModelPerformance, ActivityLog
from datetime import datetime, timedelta
import os
import psutil
import json
import pandas as pd
from sqlalchemy import func, or_, distinct

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# =================================================================
# AUTHENTICATION ROUTES
# =================================================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Admin login page - PRODUCTION MODE
    Memverifikasi username dan password dari database.
    """
    # Jika sudah login, redirect ke dashboard
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    form = LoginForm()
    
    # Validasi form saat submit (POST)
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # 1. Cari user berdasarkan username
        user = AdminUser.query.filter_by(username=username).first()
        
        # 2. Verifikasi password dan status aktif
        if user and check_password(user.password_hash, password):
            if not user.is_active:
                flash('Akun ini telah dinonaktifkan.', 'warning')
                return render_template('admin/login.html', form=form, page_title="Login Admin")
            
            # 3. Buat Session User (Flask-Login Wrapper)
            flask_user = User(
                user_id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active
            )
            
            # 4. Login User
            login_user(flask_user, remember=form.remember_me.data)
            
            # 5. Update waktu login terakhir
            update_last_login(user.id)
            
            # 6. Redirect ke halaman yang dituju atau dashboard
            next_page = request.args.get('next')
            # Validasi keamanan redirect (mencegah open redirect vulnerability)
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.dashboard')
                
            flash('Login Berhasil', 'success')
            return redirect(next_page)
        else:
            flash('Username atau password salah.', 'danger')
            
    return render_template('admin/login.html', form=form, page_title="Login Admin")

@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('admin.login'))

# =================================================================
# PAGE ROUTES
# =================================================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard view"""
    
    # 1. Statistik Dasar
    total_records = IPHData.query.count()
    active_alerts = AlertHistory.query.filter_by(is_active=True).count()
    trained_models = ModelPerformance.query.distinct(ModelPerformance.model_name).count()
    
    # 2. Aktivitas Terbaru
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # 3. Ambil last_login dari DB untuk ditampilkan
    last_login_str = "-"
    if current_user.is_authenticated:
        try:
            # Ambil ID dari session (pastikan int)
            uid_str = current_user.get_id()
            if uid_str:
                uid = int(uid_str)
                # Query ke tabel asli untuk data fresh
                real_user = AdminUser.query.get(uid)
                if real_user and real_user.last_login:
                    last_login_str = real_user.last_login.strftime('%d %b %Y %H:%M')
        except Exception as e:
            # Fallback diam-diam jika gagal load detail user
            print(f"Warning: Gagal ambil last login: {e}")
            last_login_str = "Baru saja"
    
    return render_template('admin/dashboard.html', 
                         page_title="Admin Dashboard",
                         total_records=total_records,
                         active_alerts=active_alerts,
                         trained_models=trained_models,
                         recent_activities=recent_activities,
                         last_login=last_login_str)

@admin_bp.route('/data-control')
@admin_required
def data_control():
    """Data management page"""
    total_records = IPHData.query.count()
    return render_template('admin/data_control.html', 
                         page_title="Manajemen Data",
                         total_records=total_records)

@admin_bp.route('/models')
@admin_required
def models():
    """Model management page"""
    return render_template('admin/models.html', page_title="Manajemen Model")

@admin_bp.route('/forecast')
@admin_required
def forecast():
    """Forecast management page"""
    return render_template('admin/forecast.html', page_title="Manajemen Forecast")

@admin_bp.route('/settings')
@admin_required
def settings():
    """System settings page"""
    admin_users = AdminUser.query.all()
    
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        memory_usage = f"{mem_info.rss / 1024 / 1024:.2f} MB"
    except:
        memory_usage = "N/A"
    
    return render_template('admin/settings.html', 
                         page_title="Pengaturan Sistem",
                         admin_users=admin_users,
                         memory_usage=memory_usage)

@admin_bp.route('/create-admin', methods=['GET', 'POST'])
@admin_required
def create_admin():
    """Create new admin user"""
    form = CreateAdminForm()
    if form.validate_on_submit():
        if AdminUser.query.filter_by(username=form.username.data).first():
            flash('Username sudah digunakan', 'warning')
        else:
            create_admin_user(form.username.data, form.password.data, form.email.data)
            flash('Admin baru berhasil dibuat', 'success')
            return redirect(url_for('admin.settings'))
    return render_template('admin/create_admin.html', form=form, page_title="Tambah Admin")

@admin_bp.route('/change-password', methods=['GET', 'POST'])
@admin_required
def change_password():
    """Change password for current user"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            # Dapatkan user asli dari DB
            user_db = AdminUser.query.get(int(current_user.id))
            
            # Verifikasi password lama
            if user_db and check_password(user_db.password_hash, form.current_password.data):
                user_db.password_hash = hash_password(form.new_password.data)
                db.session.commit()
                flash('Password berhasil diubah. Silakan login ulang.', 'success')
                logout_user() # Logout keamanan setelah ganti password
                return redirect(url_for('admin.login'))
            else:
                flash('Password saat ini salah.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal mengubah password: {str(e)}', 'danger')
            
    return render_template('admin/change_password.html', form=form, page_title="Ubah Password")

# =================================================================
# API ROUTES (Semua dilindungi @admin_required)
# =================================================================

@admin_bp.route('/api/data/list')
@admin_required
def api_data_list():
    """API untuk list data historis dengan pagination & search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        query = IPHData.query
        
        if search:
            query = query.filter(
                or_(
                    IPHData.bulan.ilike(f'%{search}%'),
                    IPHData.kab_kota.ilike(f'%{search}%'),
                    IPHData.minggu.ilike(f'%{search}%')
                )
            )
        
        # Sort by date desc
        pagination = query.order_by(IPHData.tanggal.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        data = {
            'items': [item.to_dict() for item in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }
        
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/add-manual-record', methods=['POST'])
@admin_required
def add_manual_record():
    """
    Menambah data manual IPH & Komoditas ke Database.
    FIX: Menggunakan DataHandler langsung & memperbaiki nama kolom DataFrame.
    """
    # Gunakan DataHandler langsung (lebih ringan & stabil daripada ForecastService)
    from services.data_handler import DataHandler
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Tidak ada data yang dikirim'})
        
        # 1. Ekstrak Data
        bulan = data.get('bulan')
        minggu = data.get('minggu')
        tahun = data.get('tahun')
        kab_kota = data.get('kab_kota', 'BATU')
        iph_value = data.get('iph_value')
        
        komoditas_andil = data.get('komoditas_andil', '')
        komoditas_fluktuasi = data.get('komoditas_fluktuasi', '')
        nilai_fluktuasi = data.get('nilai_fluktuasi', 0.0)
        
        # 2. Validasi
        if not all([bulan, minggu, tahun, iph_value]):
            return jsonify({'success': False, 'message': 'Field wajib tidak lengkap'})
        
        # 3. Konversi Tanggal
        try:
            bulan_map = {'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4, 'Mei': 5, 'Juni': 6, 'Juli': 7, 'Agustus': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12}
            
            minggu_clean = str(minggu).upper().replace('M', '').strip()
            minggu_num = int(minggu_clean)
            bulan_num = bulan_map.get(bulan, 1)
            tahun_num = int(tahun)
            
            first_day_of_month = datetime(tahun_num, bulan_num, 1)
            days_offset = (minggu_num - 1) * 7
            target_date = first_day_of_month + timedelta(days=days_offset)
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Gagal konversi tanggal: {str(e)}'})

        # 4. Buat DataFrame (FIX: Nama kolom harus sesuai dengan ekspektasi DataHandler/DB)
        new_record_data = {
            'Tanggal': [target_date.strftime('%Y-%m-%d')],
            'Indikator_Harga': [float(iph_value)],
            'Bulan': [bulan],
            'Minggu': [minggu],
            'Tahun': [tahun_num],
            'Kab/Kota': [kab_kota],
            # PENTING: Gunakan nama kolom lengkap dengan spasi, bukan underscore
            'Komoditas Andil Perubahan Harga': [komoditas_andil],
            'Komoditas Fluktuasi Harga Tertinggi': [komoditas_fluktuasi],
            'Fluktuasi Harga': [nilai_fluktuasi]
        }
        new_record_df = pd.DataFrame(new_record_data)
        
        # 5. Simpan via DataHandler
        data_handler = DataHandler()
        combined_df, merge_info = data_handler.merge_and_save_data(new_record_df)
        
        return jsonify({
            'success': True,
            'message': 'Data berhasil disimpan. Jalankan training lokal untuk update model.',
            'merge_info': merge_info
        })
        
    except Exception as e:
        # Log error untuk debugging di server console
        print(f"Add Manual Error: {e}")
        return jsonify({'success': False, 'message': f'Error System: {str(e)}'}), 500

@admin_bp.route('/api/data/update', methods=['POST'])
@admin_required
def api_data_update():
    """Update data IPH secara manual (Edit dari Tabel)"""
    try:
        data = request.get_json()
        record_id = data.get('id')
        
        if not record_id:
             return jsonify({'success': False, 'message': 'ID tidak ditemukan'})

        record = IPHData.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'message': 'Record tidak ditemukan'})

        if 'indikator_harga' in data:
            record.indikator_harga = float(data['indikator_harga'])
        
        record.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Data berhasil diperbarui'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@admin_bp.route('/api/data/<int:data_id>', methods=['DELETE'])
@admin_required
def api_delete_data(data_id):
    """API untuk delete data"""
    try:
        data = IPHData.query.get_or_404(data_id)
        db.session.delete(data)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Data deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/models/list')
@admin_required
def api_models_list():
    """API untuk list models performance"""
    try:
        latest_performances = {}
        models_query = ModelPerformance.query.order_by(ModelPerformance.trained_at.desc()).all()
        
        for model in models_query:
            model_name = model.model_name
            if model_name not in latest_performances:
                model_dict = model.to_dict()
                latest_performances[model_name] = model_dict
        
        models_data = list(latest_performances.values())
        return jsonify({'success': True, 'models': models_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/models/performance-history')
@admin_required
def api_models_performance_history():
    """API untuk chart performance history"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        performances = ModelPerformance.query.filter(
            ModelPerformance.trained_at >= cutoff_date
        ).order_by(ModelPerformance.trained_at.asc()).all()
        
        chart_data = {}
        for perf in performances:
            m_name = perf.model_name
            if m_name not in chart_data:
                chart_data[m_name] = {'dates': [], 'mae': [], 'rmse': [], 'r2': []}
            
            chart_data[m_name]['dates'].append(perf.trained_at.isoformat())
            chart_data[m_name]['mae'].append(float(perf.mae) if perf.mae else None)
            chart_data[m_name]['rmse'].append(float(perf.rmse) if perf.rmse else None)
            chart_data[m_name]['r2'].append(float(perf.r2_score) if perf.r2_score else None)
        
        return jsonify({'success': True, 'chart_data': chart_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/generate-forecast', methods=['POST'])
@admin_required
def generate_forecast():
    """Generate forecast on demand (Admin Button)"""
    from services.forecast_service import ForecastService
    forecast_service = ForecastService()
    
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        weeks = int(data.get('weeks', 8))
        
        # Panggil dengan save_history=True
        result = forecast_service.get_current_forecast(
            model_name=model_name, 
            forecast_weeks=weeks, 
            save_history=True 
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Peramalan berhasil dibuat dan disimpan.',
                'forecast': result['forecast']
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('error', 'Gagal membuat peramalan')
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@admin_bp.route('/api/forecasts/history')
@admin_required
def api_forecast_history():
    """Get forecast history with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        model_filter = request.args.get('model')

        query = ForecastHistory.query
        if model_filter:
            query = query.filter(ForecastHistory.model_name == model_filter)
            
        # Order by newest first
        pagination = query.order_by(ForecastHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        history_data = []
        for item in pagination.items:
            # Pastikan atribut ini ada di model database Anda
            weeks = getattr(item, 'forecast_weeks', getattr(item, 'weeks_forecasted', 0))
            
            history_data.append({
                'id': item.id,
                'model_name': item.model_name,
                'weeks': weeks,
                'avg_prediction': float(item.avg_prediction) if item.avg_prediction else 0.0,
                'trend': item.trend,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M') if item.created_at else '-',
                'created_by': item.created_by
            })
            
        return jsonify({
            'success': True,
            'data': history_data,
            'pagination': {
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        print(f"Error in api_forecast_history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/forecasts/<int:forecast_id>', methods=['DELETE'])
@admin_required
def api_delete_forecast(forecast_id):
    """Delete forecast history"""
    try:
        forecast = ForecastHistory.query.get_or_404(forecast_id)
        db.session.delete(forecast)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Forecast deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/system/storage')
@admin_required
def api_system_storage():
    """Dummy API for storage (Cloud)"""
    return jsonify({
        'success': True,
        'storage': {
            'database_size': 0, 
            'models_size': 0, 
            'total_size': 0
        }
    })

@admin_bp.route('/api/activities')
@admin_required
def api_activities():
    """API for audit logs"""
    try:
        limit = request.args.get('limit', 10, type=int)
        activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
        data = [activity.to_dict() for activity in activities]
        return jsonify({'success': True, 'activities': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@admin_required
def api_manage_user(user_id):
    """API Manage Admin Users"""
    try:
        user = AdminUser.query.get_or_404(user_id)
        
        if request.method == 'DELETE':
            if user.id == current_user.id:
                return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
            db.session.delete(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User deleted'})
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Update basic fields
            if 'username' in data: user.username = data['username']
            if 'email' in data: user.email = data['email']
            if 'is_active' in data: user.is_active = data['is_active']
            
            # Update password only if provided and not empty
            if 'password' in data and data['password'].strip():
                user.password_hash = hash_password(data['password'])
                
            db.session.commit()
            return jsonify({'success': True, 'message': 'User updated successfully'})
            
        return jsonify({'success': False, 'message': 'Method not allowed'}), 405
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500