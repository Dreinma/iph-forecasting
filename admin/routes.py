"""
Admin routes untuk IPH Forecasting Platform
Disesuaikan untuk Arsitektur Inference-Only (Render/Vercel + Supabase)
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from auth.decorators import admin_required
from auth.forms import LoginForm, ChangePasswordForm, CreateAdminForm
from auth.utils import check_password, update_last_login, create_admin_user, hash_password, load_user, User
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
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        # Clear session cache
        db.session.expire_all()
        
        user = AdminUser.query.filter_by(username=form.username.data).first()
        
        if user and check_password(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Akun tidak aktif.', 'danger')
                return render_template('admin/login.html', form=form)
            
            # Buat objek wrapper User untuk Flask-Login
            flask_user = User(
                user_id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active
            )
            
            login_user(flask_user, remember=form.remember_me.data)
            
            # Update last login (gunakan ID atau objek, tergantung implementasi utils)
            try:
                # Coba update manual jika fungsi util bermasalah
                user.last_login = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                print(f"Warning: Failed to update last_login: {e}")
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            flash('Username atau password salah', 'danger')
            
    return render_template('admin/login.html', form=form, page_title="Login Admin")

@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    flash('Anda telah logout', 'info')
    return redirect(url_for('admin.login'))

# =================================================================
# PAGE ROUTES (RENDER TEMPLATES)
# =================================================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard view"""
    from database import IPHData, AlertHistory, ModelPerformance, ActivityLog, AdminUser
    from sqlalchemy import func
    
    # 1. Ambil Statistik (Tetap Sama)
    total_records = IPHData.query.count()
    active_alerts = AlertHistory.query.filter_by(is_active=True).count()
    trained_models = ModelPerformance.query.distinct(ModelPerformance.model_name).count()
    
    # 2. Ambil Aktivitas Terbaru (Tetap Sama)
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # 3. PERBAIKAN TOTAL UNTUK LAST LOGIN
    last_login_str = "-" # Default jika gagal/belum pernah login
    
    if current_user.is_authenticated:
        try:
            # Ambil ID user dari sesi
            user_id = int(current_user.get_id())
            
            # Query langsung ke Database (AdminUser) menggunakan ID tersebut
            user_from_db = AdminUser.query.get(user_id)
            
            if user_from_db and user_from_db.last_login:
                # Format tanggal agar cantik
                last_login_str = user_from_db.last_login.strftime('%d %B %Y %H:%M')
        except Exception as e:
            print(f"Error mengambil last_login: {e}")
            # Jika error, biarkan default "-" agar dashboard TIDAK CRASH

    print("DEBUG USER INFO:")
    print(f"Is Authenticated: {current_user.is_authenticated}")
    print(f"User ID: {current_user.get_id()}")
    print(f"Dir Current User: {dir(current_user)}") # Ini akan mencetak semua atribut yang dimiliki current_user

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
    
    # Get memory usage (Container safe)
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
        # Ambil user asli dari DB untuk cek password
        user_db = AdminUser.query.get(int(current_user.id))
        
        if user_db and check_password(user_db.password_hash, form.current_password.data):
            user_db.password_hash = hash_password(form.new_password.data)
            db.session.commit()
            flash('Password berhasil diubah', 'success')
            return redirect(url_for('admin.settings'))
        else:
            flash('Password saat ini salah', 'danger')
    return render_template('admin/change_password.html', form=form, page_title="Ubah Password")

# =================================================================
# API ROUTES: DATA MANAGEMENT
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
    Menggunakan DataHandler untuk standardisasi penyimpanan.
    """
    # Import service di dalam fungsi untuk menghindari circular import
    from services.forecast_service import forecast_service
    
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

        # 4. Buat DataFrame
        new_record_data = {
            'Tanggal': [target_date.strftime('%Y-%m-%d')],
            'Indikator_Harga': [float(iph_value)],
            'Bulan': [bulan],
            'Minggu': [minggu],
            'Tahun': [tahun_num],
            'Kab/Kota': [kab_kota],
            'Komoditas_Andil': [komoditas_andil],
            'Komoditas_Fluktuasi_Tertinggi': [komoditas_fluktuasi],
            'Fluktuasi_Harga': [nilai_fluktuasi]
        }
        new_record_df = pd.DataFrame(new_record_data)
        
        # 5. Simpan via DataHandler
        combined_df, merge_info = forecast_service.data_handler.merge_and_save_data(new_record_df)
        
        return jsonify({
            'success': True,
            'message': 'Data berhasil disimpan. Jalankan training lokal untuk update model.',
            'merge_info': merge_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

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

# =================================================================
# API ROUTES: MODEL & FORECAST
# =================================================================

@admin_bp.route('/api/models/list')
@admin_required
def api_models_list():
    """API untuk list models performance"""
    try:
        # Get latest performance per model
        latest_performances = {}
        models_query = ModelPerformance.query.order_by(ModelPerformance.trained_at.desc()).all()
        
        for model in models_query:
            model_name = model.model_name
            if model_name not in latest_performances:
                # to_dict() di database.py sudah menangani JSON parsing feature_importance
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
    from services.forecast_service import forecast_service
    
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        weeks = int(data.get('weeks', 8))
        
        # Panggil dengan save_history=True karena ini aksi manual admin
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
            
        pagination = query.order_by(ForecastHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        history_data = []
        for item in pagination.items:
            history_data.append({
                'id': item.id,
                'model_name': item.model_name,
                'weeks': item.weeks_forecasted,
                'avg_prediction': item.avg_prediction,
                'trend': item.trend,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%M'),
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
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/forecasts/<int:forecast_id>', methods=['DELETE'])
@admin_required
def api_delete_forecast(forecast_id):
    """Delete forecast history item"""
    try:
        forecast = ForecastHistory.query.get_or_404(forecast_id)
        db.session.delete(forecast)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Forecast deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# =================================================================
# API ROUTES: SYSTEM & AUDIT
# =================================================================

@admin_bp.route('/api/system/storage')
@admin_required
def api_system_storage():
    """API untuk storage information (Dummy/Minimal untuk Cloud)"""
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
    """API untuk recent activities (Audit Log)"""
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
        
        return jsonify({'success': False, 'message': 'Update not implemented yet'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500