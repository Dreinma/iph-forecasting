"""
Admin routes untuk IPH Forecasting Platform
CATATAN: Routes ini belum diintegrasikan ke app.py
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from auth.decorators import admin_required
from auth.forms import LoginForm, ChangePasswordForm, CreateAdminForm
from auth.utils import check_password, update_last_login, create_admin_user, hash_password
from database import db, AdminUser, IPHData, CommodityData
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import psutil
import pandas as pd
import json

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import user loader
from auth.utils import load_user, User

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page - Hanya untuk admin"""
    
    form = LoginForm()
    
    # Handle Admin Login
    if form.validate_on_submit():
        # Clear session cache untuk memastikan fresh query
        db.session.expire_all()
        
        # Find user dengan fresh query
        user = AdminUser.query.filter_by(username=form.username.data).first()
        
        # Debug logging (remove in production)
        import logging
        logger = logging.getLogger(__name__)
        
        if not user:
            flash('Username atau password salah, atau akun tidak aktif.', 'danger')
            logger.warning(f"Login attempt with non-existent username: {form.username.data}")
        elif not user.is_active:
            flash('Akun tidak aktif. Silakan hubungi administrator.', 'danger')
            logger.warning(f"Login attempt with inactive account: {form.username.data}")
        elif not user.password_hash:
            flash('Password belum diatur. Silakan hubungi administrator.', 'danger')
            logger.error(f"Login attempt with null password hash: {form.username.data}")
        else:
            # Check password
            password_check = check_password(user.password_hash, form.password.data)
            logger.debug(f"Login attempt: username={form.username.data}, success={password_check}")
            
            if password_check:
                # Login successful
                flask_user = User(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    is_active=user.is_active
                )
                
                login_user(flask_user, remember=form.remember_me.data)
                update_last_login(user.id)
                
                # Set session as permanent and initialize last_activity
                session.permanent = True
                session['user_role'] = 'admin'
                session['last_activity'] = datetime.utcnow().isoformat()
                
                flash('Login berhasil!', 'success')
                
                # Redirect to next page or admin dashboard
                next_page = request.args.get('next')
                return redirect(next_page or url_for('admin.dashboard'))
            else:
                flash('Username atau password salah, atau akun tidak aktif.', 'danger')
                logger.warning(f"Login attempt with wrong password for user: {form.username.data}")
    
    return render_template('admin/login.html', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout - Hanya untuk admin"""
    logout_user()
    session.pop('user_role', None)
    flash('Anda telah logout.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/change-password', methods=['GET', 'POST'])
@admin_required
def change_password():
    """Change password untuk admin yang sedang login"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        try:
            # Get current user
            admin_user = AdminUser.query.get(current_user.id)
            if not admin_user:
                flash('User tidak ditemukan', 'danger')
                return redirect(url_for('admin.dashboard'))
            
            # Verify current password
            if not check_password(admin_user.password_hash, form.current_password.data):
                flash('Password saat ini salah', 'danger')
                return render_template('admin/change_password.html', form=form)
            
            # Check if new password is same as current
            if check_password(admin_user.password_hash, form.new_password.data):
                flash('Password baru harus berbeda dengan password saat ini', 'warning')
                return render_template('admin/change_password.html', form=form)
            
            # Update password
            admin_user.password_hash = hash_password(form.new_password.data)
            db.session.commit()
            
            flash('Password berhasil diubah!', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('admin/change_password.html', form=form)
    
    return render_template('admin/change_password.html', form=form)

@admin_bp.route('/change-password-api', methods=['POST'])
@admin_required
def change_password_api():
    """API endpoint untuk change password via AJAX"""
    try:
        data = request.get_json()
        current_password = data.get('current_password', '').strip()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'error': 'Semua field harus diisi'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'error': 'Password minimal 8 karakter'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'Password baru dan konfirmasi tidak cocok'}), 400
        
        # Get current user
        admin_user = AdminUser.query.get(current_user.id)
        if not admin_user:
            return jsonify({'success': False, 'error': 'User tidak ditemukan'}), 404
        
        # Verify current password
        if not check_password(admin_user.password_hash, current_password):
            return jsonify({'success': False, 'error': 'Password saat ini salah'}), 400
        
        # Check if new password is same as current
        if check_password(admin_user.password_hash, new_password):
            return jsonify({'success': False, 'error': 'Password baru harus berbeda dengan password saat ini'}), 400
        
        # Update password
        admin_user.password_hash = hash_password(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password berhasil diubah!'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    from database import IPHData, AlertHistory, ModelPerformance, ActivityLog
    from sqlalchemy import func
    
    # Get statistics
    total_records = IPHData.query.count()
    active_alerts = AlertHistory.query.filter_by(is_active=True).count()
    trained_models = ModelPerformance.query.distinct(ModelPerformance.model_name).count()
    
    # Recent activities (last 10)
    recent_activities = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    
    # Last login info
    last_login = None
    if current_user.is_authenticated:
        user = AdminUser.query.get(current_user.id)
        if user:
            last_login = user.last_login
    
    return render_template('admin/dashboard.html', 
                         page_title="Admin Dashboard",
                         total_records=total_records,
                         active_alerts=active_alerts,
                         trained_models=trained_models,
                         recent_activities=recent_activities,
                         last_login=last_login)

@admin_bp.route('/data-control')
@admin_required
def data_control():
    """Data management page (moved from /data-control)"""
    from database import IPHData
    total_records = IPHData.query.count()
    return render_template('admin/data_control.html', 
                         page_title="Data Management",
                         total_records=total_records)

@admin_bp.route('/models')
@admin_required
def models():
    """Model management page"""
    return render_template('admin/models.html', page_title="Model Management")

@admin_bp.route('/forecast')
@admin_required
def forecast():
    """Forecast management page"""
    return render_template('admin/forecast.html', page_title="Forecast Management")

@admin_bp.route('/settings')
@admin_required
def settings():
    """System settings page"""
    from database import AdminUser
    admin_users = AdminUser.query.all()
    return render_template('admin/settings.html', 
                         page_title="System Settings",
                         admin_users=admin_users,
                         memory_usage=f"{psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.2f} MB")

@admin_bp.route('/create-admin', methods=['GET', 'POST'])
@admin_required
def create_admin():
    """Create new admin user"""
    from auth.forms import CreateAdminForm
    from auth.utils import create_admin_user
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    
    try:
        form = CreateAdminForm()
        
        if request.method == 'POST':
            logger.info(f"=== CREATE ADMIN POST REQUEST ===")
            logger.info(f"Form data received: username={request.form.get('username', 'N/A')}, email={request.form.get('email', 'N/A')}")
            logger.info(f"CSRF token present: {'csrf_token' in request.form}")
            
            # Validate form
            if form.validate_on_submit():
                logger.debug("Form validation passed")
                try:
                    # Additional validation: check username uniqueness
                    from database import AdminUser
                    existing_username = AdminUser.query.filter_by(username=form.username.data).first()
                    if existing_username:
                        flash(f'Username "{form.username.data}" sudah digunakan. Silakan pilih username lain.', 'danger')
                        logger.warning(f"Username already exists: {form.username.data}")
                    else:
                        # Check email uniqueness if email is provided
                        email_value = form.email.data.strip() if form.email.data else None
                        if email_value:
                            existing_email = AdminUser.query.filter_by(email=email_value).first()
                            if existing_email:
                                flash(f'Email/Identifier "{email_value}" sudah digunakan. Silakan gunakan yang lain.', 'danger')
                                logger.warning(f"Email already exists: {email_value}")
                            else:
                                # All validations passed, create user
                                admin_user, message = create_admin_user(
                                    form.username.data,
                                    form.password.data,
                                    email_value
                                )
                                
                                if admin_user:
                                    flash(f'Admin user "{form.username.data}" berhasil dibuat!', 'success')
                                    logger.info(f"Admin user created: {form.username.data}")
                                    return redirect(url_for('admin.settings'))
                                else:
                                    flash(f'Error: {message}', 'danger')
                                    logger.warning(f"Failed to create admin user: {message}")
                        else:
                            # No email provided - that's OK, email is optional
                            admin_user, message = create_admin_user(
                                form.username.data,
                                form.password.data,
                                None
                            )
                            
                            if admin_user:
                                flash(f'Admin user "{form.username.data}" berhasil dibuat!', 'success')
                                logger.info(f"Admin user created: {form.username.data}")
                                return redirect(url_for('admin.settings'))
                            else:
                                flash(f'Error: {message}', 'danger')
                                logger.warning(f"Failed to create admin user: {message}")
                except Exception as e:
                    error_detail = traceback.format_exc()
                    logger.error(f"Error creating admin user: {str(e)}\n{error_detail}")
                    flash(f'Error saat membuat admin user: {str(e)}', 'danger')
            else:
                # Form validation failed
                logger.warning(f"=== FORM VALIDATION FAILED ===")
                logger.warning(f"Form errors: {form.errors}")
                logger.warning(f"Form data: username={form.username.data if form.username.data else 'EMPTY'}, email={form.email.data if form.email.data else 'EMPTY'}")
                
                error_messages = []
                for field, errors in form.errors.items():
                    field_label = getattr(form, field).label.text if hasattr(form, field) else field
                    for error in errors:
                        error_msg = f"{field_label}: {error}"
                        error_messages.append(error_msg)
                        logger.warning(f"  - {error_msg}")
                
                if error_messages:
                    flash(f'Validation error: {"; ".join(error_messages)}', 'danger')
                else:
                    flash('Form validation failed. Silakan cek input Anda.', 'danger')
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Unexpected error in create_admin: {str(e)}\n{error_detail}")
        flash(f'Unexpected error: {str(e)}', 'danger')
    
    # Return form for GET or if POST had errors
    try:
        if 'form' not in locals():
            form = CreateAdminForm()
        return render_template('admin/create_admin.html', form=form, page_title="Create Admin User")
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}", exc_info=True)
        return f"Error: {str(e)}", 500

# ==================== API ROUTES ====================

@admin_bp.route('/api/add-manual-record', methods=['POST'])
@admin_required
def add_manual_record():
    """Add manual IPH and commodity record to database"""

    from database import db, IPHData, CommodityData
    from datetime import datetime, timedelta
    from services.forecast_service import forecast_service


    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Tidak ada data yang dikirim'})
        
        # 1. Ekstrak Data dari Request
        bulan = data.get('bulan')
        minggu = data.get('minggu')
        tahun = data.get('tahun')
        kab_kota = data.get('kab_kota', 'BATU')
        iph_value = data.get('iph_value')
        
        # Data Komoditas (Opsional)
        komoditas_andil = data.get('komoditas_andil', '')
        komoditas_fluktuasi = data.get('komoditas_fluktuasi', '')
        nilai_fluktuasi = data.get('nilai_fluktuasi', 0.0)
        
        # 2. Validasi Field Wajib
        if not all([bulan, minggu, tahun, iph_value]):
            return jsonify({'success': False, 'message': 'Bulan, Minggu, Tahun, dan Nilai IPH wajib diisi'})
        
        # 3. Konversi Periode (Bulan/Minggu) menjadi Tanggal (Date)
        #    Kita perlu tanggal spesifik agar bisa disimpan di kolom 'Tanggal'
        try:
            bulan_map = {
                'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4,
                'Mei': 5, 'Juni': 6, 'Juli': 7, 'Agustus': 8,
                'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12
            }
            
            # Bersihkan input (misal "M1" -> 1)
            minggu_clean = str(minggu).upper().replace('M', '').strip()
            minggu_num = int(minggu_clean)
            bulan_num = bulan_map.get(bulan, 1)
            tahun_num = int(tahun)
            
            # Logika: Cari tanggal hari Senin pada minggu ke-X di bulan tersebut
            # Mulai dari tanggal 1 bulan tersebut
            first_day_of_month = datetime(tahun_num, bulan_num, 1)
            
            # Cari hari Senin pertama di bulan itu (atau hari pertama minggu statistik BPS)
            # weekday(): Senin=0, Minggu=6. 
            # Kita asumsikan data mingguan BPS biasanya dihitung per pekan.
            # Ini adalah estimasi tanggal agar bisa masuk ke DB.
            # Logic: (Minggu ke-X - 1) * 7 hari + offset
            days_offset = (minggu_num - 1) * 7
            target_date = first_day_of_month + timedelta(days=days_offset)
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Gagal mengkonversi tanggal: {str(e)}'})

        # 4. Buat DataFrame Satu Baris
        #    Kita format agar mirip dengan hasil bacaan CSV, sehingga bisa
        #    diproses oleh DataHandler.merge_and_save_data
        new_record_data = {
            'Tanggal': [target_date.strftime('%Y-%m-%d')],
            'Indikator_Harga': [float(iph_value)],
            'Bulan': [bulan],
            'Minggu': [minggu],
            'Tahun': [tahun_num],
            'Kab/Kota': [kab_kota],
            
            # Masukkan data komoditas jika ada (agar disimpan ke tabel commodity_data juga)
            'Komoditas_Andil': [komoditas_andil],
            'Komoditas_Fluktuasi_Tertinggi': [komoditas_fluktuasi],
            'Fluktuasi_Harga': [nilai_fluktuasi]
        }
        
        new_record_df = pd.DataFrame(new_record_data)
        
        # 5. Simpan ke Database menggunakan DataHandler
        #    Fungsi ini akan menangani duplikasi (update jika tanggal sama)
        combined_df, merge_info = forecast_service.data_handler.merge_and_save_data(new_record_df)
        
        return jsonify({
            'success': True,
            'message': 'Data berhasil ditambahkan ke database. Silakan jalankan training lokal untuk memperbarui model.',
            'merge_info': merge_info,
            'data': {
                'tanggal': target_date.strftime('%d %B %Y'),
                'iph': iph_value
            }
        })
        
    except Exception as e:
        # Log error di sini jika perlu
        return jsonify({'success': False, 'message': f'Error adding record: {str(e)}'}), 500

    
@admin_bp.route('/api/data/update', methods=['POST'])
@admin_required
def api_data_update():
    """Update data IPH secara manual (Edit)"""
    try:
        data = request.get_json()
        record_id = data.get('id')
        
        # Validasi input
        if not record_id:
             return jsonify({'success': False, 'message': 'ID tidak ditemukan'})

        record = IPHData.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'message': 'Record tidak ditemukan'})

        # Update field yang diizinkan
        if 'indikator_harga' in data:
            record.indikator_harga = float(data['indikator_harga'])
        
        # (Opsional) Update field lain jika perlu
        # if 'bulan' in data: record.bulan = data['bulan']
        
        record.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Data berhasil diperbarui'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
    
@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API untuk dashboard statistics"""
    from database import IPHData, AlertHistory, ModelPerformance, ActivityLog
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        stats = {
            'total_records': IPHData.query.count(),
            'active_alerts': AlertHistory.query.filter_by(is_active=True).count(),
            'trained_models': ModelPerformance.query.distinct(ModelPerformance.model_name).count(),
            'recent_activities_count': ActivityLog.query.filter(
                ActivityLog.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count(),
            'latest_data_date': db.session.query(func.max(IPHData.tanggal)).scalar()
        }
        
        # Convert date to string if exists
        if stats['latest_data_date']:
            stats['latest_data_date'] = stats['latest_data_date'].strftime('%Y-%m-%d')
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/data/list')
@admin_required
def api_data_list():
    """API untuk list data dengan pagination"""
    from database import IPHData
    from sqlalchemy import or_
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        
        query = IPHData.query
        
        # Search filter
        if search:
            query = query.filter(
                or_(
                    IPHData.bulan.contains(search),
                    IPHData.kab_kota.contains(search),
                    IPHData.minggu.contains(search)
                )
            )
        
        # Pagination
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

@admin_bp.route('/api/data/<int:data_id>', methods=['PUT'])
@admin_required
def api_update_data(data_id):
    """API untuk update data"""
    from database import IPHData
    from datetime import datetime
    
    try:
        data = IPHData.query.get_or_404(data_id)
        json_data = request.get_json()
        
        # Update fields
        if 'indikator_harga' in json_data:
            data.indikator_harga = json_data['indikator_harga']
        if 'tanggal' in json_data:
            data.tanggal = datetime.strptime(json_data['tanggal'], '%Y-%m-%d').date()
        if 'bulan' in json_data:
            data.bulan = json_data['bulan']
        if 'minggu' in json_data:
            data.minggu = json_data['minggu']
        
        data.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Data updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/data/<int:data_id>', methods=['DELETE'])
@admin_required
def api_delete_data(data_id):
    """API untuk delete data"""
    from database import IPHData
    
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
    """API untuk list models dengan grouping dan summary"""
    from database import ModelPerformance
    from sqlalchemy import func
    import json
    
    try:
        # Get latest performance per model
        latest_performances = {}
        models_query = ModelPerformance.query.order_by(ModelPerformance.trained_at.desc()).all()
        
        for model in models_query:
            model_name = model.model_name
            if model_name not in latest_performances:
                model_dict = model.to_dict()
                # Parse feature_importance if it's a string
                if isinstance(model_dict.get('feature_importance'), str):
                    try:
                        model_dict['feature_importance'] = json.loads(model_dict['feature_importance'])
                    except:
                        pass
                latest_performances[model_name] = model_dict
        
        # Get model statistics
        model_stats = {}
        for model_name in latest_performances.keys():
            all_performances = ModelPerformance.query.filter_by(model_name=model_name).order_by(ModelPerformance.trained_at.desc()).all()
            model_stats[model_name] = {
                'training_count': len(all_performances),
                'latest_trained': all_performances[0].trained_at.isoformat() if all_performances else None,
                'best_mae': min([m.mae for m in all_performances]) if all_performances else None,
                'latest_mae': all_performances[0].mae if all_performances else None
            }
        
        # Combine data
        models_data = []
        for model_name, perf in latest_performances.items():
            perf['statistics'] = model_stats.get(model_name, {})
            models_data.append(perf)
        
        return jsonify({'success': True, 'models': models_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/models/performance-history')
@admin_required
def api_models_performance_history():
    """API untuk performance history chart data"""
    from database import ModelPerformance
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        # Get last 30 days of training
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        performances = ModelPerformance.query.filter(
            ModelPerformance.trained_at >= cutoff_date
        ).order_by(ModelPerformance.trained_at.asc()).all()
        
        # Group by model_name and prepare chart data
        chart_data = {}
        for perf in performances:
            model_name = perf.model_name
            if model_name not in chart_data:
                chart_data[model_name] = {
                    'dates': [],
                    'mae': [],
                    'rmse': [],
                    'r2': []
                }
            
            chart_data[model_name]['dates'].append(perf.trained_at.isoformat())
            chart_data[model_name]['mae'].append(float(perf.mae) if perf.mae else None)
            chart_data[model_name]['rmse'].append(float(perf.rmse) if perf.rmse else None)
            chart_data[model_name]['r2'].append(float(perf.r2_score) if perf.r2_score else None)
        
        return jsonify({'success': True, 'chart_data': chart_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/activities')
@admin_required
def api_activities():
    """API untuk recent activities"""
    from database import ActivityLog
    from datetime import datetime, timedelta
    
    try:
        limit = request.args.get('limit', 10, type=int)
        activities = ActivityLog.query.order_by(
            ActivityLog.created_at.desc()
        ).limit(limit).all()
        
        data = [activity.to_dict() for activity in activities]
        return jsonify({'success': True, 'activities': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/data/update', methods=['POST'])
@admin_required
def update_data():
    try:
        data = request.get_json()
        record_id = data.get('id')
        new_iph = data.get('indikator_harga')
        
        # Cari record di DB (asumsi IPHData punya kolom id)
        record = IPHData.query.get(record_id)
        if record:
            record.indikator_harga = float(new_iph)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Record not found'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# ==================== FORECAST MANAGEMENT APIs ====================


@admin_bp.route('/api/generate-forecast', methods=['POST'])
@admin_required
def generate_forecast():
    """Generate forecast on demand"""
    from services.forecast_service import forecast_service
    
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        weeks = int(data.get('weeks', 8))
        
        # Panggil dengan save_history=True karena ini dari tombol admin
        result = forecast_service.get_current_forecast(
            model_name=model_name, 
            forecast_weeks=weeks, 
            save_history=True # <--- Pastikan ini True
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

# --- TAMBAHKAN API HISTORY INI ---
@admin_bp.route('/api/forecasts/history')
@admin_required
def api_forecast_history():
    """Get forecast history with pagination"""
    from database import ForecastHistory
    
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

@admin_bp.route('/api/forecasts/statistics')
@admin_required
def api_forecast_statistics():
    """API untuk forecast statistics"""
    from database import ForecastHistory
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        # Total forecasts
        total = ForecastHistory.query.count()
        
        # This month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = ForecastHistory.query.filter(
            ForecastHistory.created_at >= start_of_month
        ).count()
        
        # Most used model
        most_used = db.session.query(
            ForecastHistory.model_name,
            func.count(ForecastHistory.id).label('count')
        ).group_by(ForecastHistory.model_name).order_by(
            func.count(ForecastHistory.id).desc()
        ).first()
        
        most_used_model = most_used[0] if most_used else 'N/A'
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_forecasts': total,
                'this_month': this_month,
                'most_used_model': most_used_model
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/forecasts/<int:forecast_id>', methods=['DELETE'])
@admin_required
def api_delete_forecast(forecast_id):
    """API untuk delete forecast history"""
    from database import ForecastHistory
    
    try:
        forecast = ForecastHistory.query.get_or_404(forecast_id)
        db.session.delete(forecast)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Forecast deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/forecasts/export')
@admin_required
def api_export_forecast_history():
    """API untuk export forecast history ke CSV"""
    from database import ForecastHistory
    import csv
    import io
    from flask import Response
    
    try:
        forecasts = ForecastHistory.query.order_by(ForecastHistory.created_at.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID', 'Model Name', 'Weeks Forecasted', 'Avg Prediction', 
            'Trend', 'Volatility', 'Min Prediction', 'Max Prediction',
            'Model MAE', 'Model RMSE', 'Model R2', 'Created By', 'Created At'
        ])
        
        # Data
        for forecast in forecasts:
            writer.writerow([
                forecast.id,
                forecast.model_name,
                forecast.weeks_forecasted,
                forecast.avg_prediction,
                forecast.trend,
                forecast.volatility,
                forecast.min_prediction,
                forecast.max_prediction,
                forecast.model_mae,
                forecast.model_rmse,
                forecast.model_r2,
                forecast.created_by,
                forecast.created_at.isoformat() if forecast.created_at else ''
            ])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=forecast_history.csv'}
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ALERT MANAGEMENT APIs ====================

@admin_bp.route('/api/alerts/rules')
@admin_required
def api_alert_rules():
    """API untuk list alert rules"""
    from database import AlertRule
    
    try:
        rules = AlertRule.query.order_by(AlertRule.created_at.desc()).all()
        data = [rule.to_dict() for rule in rules]
        return jsonify({'success': True, 'rules': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/alerts/rules', methods=['POST'])
@admin_required
def api_create_alert_rule():
    """API untuk create alert rule"""
    from database import AlertRule
    from flask_login import current_user
    
    try:
        data = request.get_json()
        
        # Check if rule name already exists
        existing = AlertRule.query.filter_by(rule_name=data.get('rule_name')).first()
        if existing:
            return jsonify({'success': False, 'error': 'Rule name already exists'}), 400
        
        rule = AlertRule(
            rule_name=data.get('rule_name'),
            rule_type=data.get('rule_type', 'threshold'),
            is_active=data.get('is_active', True),
            threshold_value=data.get('threshold_value'),
            comparison_operator=data.get('comparison_operator', '>'),
            severity_level=data.get('severity_level', 'warning'),
            check_period_days=data.get('check_period_days', 7),
            min_data_points=data.get('min_data_points', 5),
            created_by=current_user.username if current_user.is_authenticated else 'system',
            description=data.get('description', '')
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({'success': True, 'rule': rule.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/alerts/rules/<int:rule_id>', methods=['PUT'])
@admin_required
def api_update_alert_rule(rule_id):
    """API untuk update alert rule"""
    from database import AlertRule
    
    try:
        rule = AlertRule.query.get_or_404(rule_id)
        data = request.get_json()
        
        if 'rule_name' in data and data['rule_name'] != rule.rule_name:
            existing = AlertRule.query.filter_by(rule_name=data['rule_name']).first()
            if existing and existing.id != rule_id:
                return jsonify({'success': False, 'error': 'Rule name already exists'}), 400
        
        if 'rule_name' in data:
            rule.rule_name = data['rule_name']
        if 'rule_type' in data:
            rule.rule_type = data['rule_type']
        if 'is_active' in data:
            rule.is_active = data['is_active']
        if 'threshold_value' in data:
            rule.threshold_value = data['threshold_value']
        if 'comparison_operator' in data:
            rule.comparison_operator = data['comparison_operator']
        if 'severity_level' in data:
            rule.severity_level = data['severity_level']
        if 'check_period_days' in data:
            rule.check_period_days = data['check_period_days']
        if 'min_data_points' in data:
            rule.min_data_points = data['min_data_points']
        if 'description' in data:
            rule.description = data['description']
        
        rule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'rule': rule.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/alerts/rules/<int:rule_id>', methods=['DELETE'])
@admin_required
def api_delete_alert_rule(rule_id):
    """API untuk delete alert rule"""
    from database import AlertRule
    
    try:
        rule = AlertRule.query.get_or_404(rule_id)
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Alert rule deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/alerts/history')
@admin_required
def api_alert_history():
    """API untuk alert history dengan filter"""
    from database import AlertHistory
    
    try:
        severity_filter = request.args.get('severity', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = AlertHistory.query
        
        if severity_filter:
            query = query.filter(AlertHistory.severity == severity_filter)
        
        pagination = query.order_by(AlertHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        data = {
            'items': [alert.to_dict() for alert in pagination.items],
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

@admin_bp.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@admin_required
def api_acknowledge_alert(alert_id):
    """API untuk acknowledge alert"""
    from database import AlertHistory
    from flask_login import current_user
    
    try:
        alert = AlertHistory.query.get_or_404(alert_id)
        data = request.get_json() or {}
        
        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = current_user.username if current_user.is_authenticated else 'system'
        alert.admin_notes = data.get('notes', '')
        
        db.session.commit()
        
        return jsonify({'success': True, 'alert': alert.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SETTINGS APIs ====================

@admin_bp.route('/api/settings/config', methods=['GET', 'POST'])
@admin_required
def api_settings_config():
    """API untuk get/save system configuration"""
    from config import Config
    
    try:
        if request.method == 'GET':
            # Return current config values
            return jsonify({
                'success': True,
                'config': {
                    'forecast_min_weeks': Config.FORECAST_MIN_WEEKS,
                    'forecast_max_weeks': Config.FORECAST_MAX_WEEKS,
                    'model_performance_threshold': Config.MODEL_PERFORMANCE_THRESHOLD,
                    'auto_retrain_threshold': Config.AUTO_RETRAIN_THRESHOLD,
                    'auto_backup_enabled': Config.AUTO_BACKUP_ENABLED,
                    'db_backup_retention_days': Config.DB_BACKUP_RETENTION_DAYS
                }
            })
        else:
            # Save config (for now, just return success - config is loaded from file/env)
            # In production, save to database or config file
            data = request.get_json()
            
            # TODO: Save to database or update config file
            # For now, just acknowledge
            return jsonify({
                'success': True,
                'message': 'Configuration saved (Note: Some settings require app restart)'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/settings/app', methods=['GET', 'POST'])
@admin_required
def api_app_settings():
    """API untuk application settings"""
    try:
        if request.method == 'GET':
            # Get from session or default values
            return jsonify({
                'success': True,
                'settings': {
                    'app_name': 'PRISMA',  # Read-only, always 'PRISMA'
                    'timezone': session.get('timezone', 'Asia/Jakarta'),
                    'date_format': session.get('date_format', 'DD/MM/YYYY'),
                    'time_format': session.get('time_format', '24h'),
                    'items_per_page': session.get('items_per_page', 25),
                    'refresh_interval': session.get('refresh_interval', 300)
                }
            })
        else:
            # Save to session (in production, save to database)
            # Note: app_name is read-only and cannot be changed
            data = request.get_json()
            for key in ['timezone', 'date_format', 'time_format', 'items_per_page', 'refresh_interval']:
                if key in data:
                    session[key] = data[key]
            
            # Ignore app_name if sent - it's read-only
            if 'app_name' in data:
                del data['app_name']
            
            return jsonify({'success': True, 'message': 'Application settings saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@admin_bp.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@admin_required
def api_manage_user(user_id):
    """API untuk edit/delete admin user"""
    from database import AdminUser
    from auth.utils import hash_password
    from flask_login import current_user
    
    try:
        user = AdminUser.query.get_or_404(user_id)
        
        # Prevent self-deletion
        if request.method == 'DELETE':
            if user.id == current_user.id:
                return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
            
            db.session.delete(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'User deleted successfully'})
        
        # PUT - Update user
        data = request.get_json()
        
        if 'username' in data and data['username'] != user.username:
            existing = AdminUser.query.filter_by(username=data['username']).first()
            if existing:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            user.username = data['username']
        
        if 'email' in data:
            if data['email'] != user.email:
                existing = AdminUser.query.filter_by(email=data['email']).first()
                if existing:
                    return jsonify({'success': False, 'error': 'Email already exists'}), 400
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.password_hash = hash_password(data['password'])
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({'success': True, 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== BACKUP & RESTORE APIs ====================

@admin_bp.route('/api/backup/create', methods=['POST'])
@admin_required
def api_create_backup():
    """API untuk membuat database backup"""
    import shutil
    import zipfile
    from datetime import datetime
    from config import Config
    
    try:
        data = request.get_json() or {}
        include_models = data.get('include_models', True)
        include_uploads = data.get('include_uploads', True)
        
        # Create backup directory if not exists
        os.makedirs(Config.DB_BACKUP_FOLDER, exist_ok=True)
        
        # Backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.zip'
        backup_path = os.path.join(Config.DB_BACKUP_FOLDER, backup_filename)
        
        # Create ZIP file
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup database
            db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
            if os.path.exists(db_path):
                zipf.write(db_path, 'database.db')
            
            # Backup models if requested
            if include_models and os.path.exists(Config.MODELS_PATH):
                for root, dirs, files in os.walk(Config.MODELS_PATH):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, Config.MODELS_PATH)
                        zipf.write(file_path, f'models/{arc_name}')
            
            # Backup uploads if requested
            if include_uploads and os.path.exists(Config.UPLOAD_FOLDER):
                for root, dirs, files in os.walk(Config.UPLOAD_FOLDER):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, Config.UPLOAD_FOLDER)
                        zipf.write(file_path, f'uploads/{arc_name}')
        
        file_size = os.path.getsize(backup_path)
        
        return jsonify({
            'success': True,
            'backup_file': backup_filename,
            'size': file_size,
            'created_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/backup/list')
@admin_required
def api_list_backups():
    """API untuk list semua backup files"""
    import os
    from datetime import datetime
    from config import Config
    
    try:
        backups = []
        backup_folder = Config.DB_BACKUP_FOLDER
        
        if os.path.exists(backup_folder):
            for filename in os.listdir(backup_folder):
                if filename.endswith('.zip'):
                    file_path = os.path.join(backup_folder, filename)
                    stat = os.stat(file_path)
                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        # Sort by created_at descending
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'success': True, 'backups': backups})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/backup/download/<filename>')
@admin_required
def api_download_backup(filename):
    """API untuk download backup file"""
    from flask import send_file
    from config import Config
    
    try:
        backup_path = os.path.join(Config.DB_BACKUP_FOLDER, filename)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup file not found'}), 404
        
        return send_file(backup_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/backup/delete/<filename>', methods=['DELETE'])
@admin_required
def api_delete_backup(filename):
    """API untuk delete backup file"""
    from config import Config
    
    try:
        backup_path = os.path.join(Config.DB_BACKUP_FOLDER, filename)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup file not found'}), 404
        
        os.remove(backup_path)
        return jsonify({'success': True, 'message': 'Backup deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/backup/restore', methods=['POST'])
@admin_required
def api_restore_backup():
    """API untuk restore dari backup"""
    import zipfile
    import shutil
    from config import Config
    
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'Filename required'}), 400
        
        backup_path = os.path.join(Config.DB_BACKUP_FOLDER, filename)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup file not found'}), 404
        
        # Extract backup
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(Config.DATA_FOLDER)
        
        # Move database to correct location if extracted
        extracted_db = os.path.join(Config.DATA_FOLDER, 'database.db')
        db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        if os.path.exists(extracted_db):
            # Backup current database first
            current_backup = db_path + '.pre_restore'
            if os.path.exists(db_path):
                shutil.copy2(db_path, current_backup)
            # Move extracted database
            shutil.move(extracted_db, db_path)
        
        return jsonify({'success': True, 'message': 'Restore completed. Please restart the application.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== AUDIT LOG APIs ====================

@admin_bp.route('/api/audit/logs')
@admin_required
def api_audit_logs():
    """API untuk audit logs dengan filter dan pagination"""
    from database import ActivityLog
    from datetime import datetime
    from sqlalchemy import and_
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 25, type=int)
        action_type = request.args.get('action_type', '')
        username = request.args.get('username', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        logger.debug(f"Audit logs request: page={page}, limit={limit}, action={action_type}, user={username}")
        
        query = ActivityLog.query
        
        # Apply filters
        if action_type:
            query = query.filter(ActivityLog.action_type == action_type)
        if username:
            query = query.filter(ActivityLog.username == username)
        if date_from:
            try:
                date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(ActivityLog.created_at >= date_from_dt)
            except Exception as e:
                logger.warning(f"Invalid date_from format: {date_from}, error: {e}")
                pass
        if date_to:
            try:
                date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                # Add one day to include the entire day
                date_to_dt = date_to_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(ActivityLog.created_at <= date_to_dt)
            except Exception as e:
                logger.warning(f"Invalid date_to format: {date_to}, error: {e}")
                pass
        
        # Get total count
        total = query.count()
        logger.debug(f"Total audit logs found: {total}")
        
        # Paginate
        pagination = query.order_by(ActivityLog.created_at.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )
        
        activities = [activity.to_dict() for activity in pagination.items]
        logger.debug(f"Returning {len(activities)} activities for page {page}")
        
        return jsonify({
            'success': True,
            'activities': activities,
            'total': total,
            'page': page,
            'pages': pagination.pages if pagination.pages else 1
        })
    except Exception as e:
        logger.error(f"Error in api_audit_logs: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/audit/users')
@admin_required
def api_audit_users():
    """API untuk mendapatkan daftar unique users dari audit log"""
    from database import ActivityLog
    from sqlalchemy import distinct
    
    try:
        users = db.session.query(distinct(ActivityLog.username)).all()
        user_list = [user[0] for user in users if user[0]]
        
        return jsonify({'success': True, 'users': user_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/audit/export')
@admin_required
def api_export_audit_logs():
    """API untuk export audit logs ke CSV"""
    from database import ActivityLog
    from flask import send_file
    import csv
    import io
    from datetime import datetime
    
    try:
        action_type = request.args.get('action_type', '')
        username = request.args.get('username', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        query = ActivityLog.query
        
        if action_type:
            query = query.filter(ActivityLog.action_type == action_type)
        if username:
            query = query.filter(ActivityLog.username == username)
        if date_from:
            try:
                date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(ActivityLog.created_at >= date_from_dt)
            except:
                pass
        if date_to:
            try:
                date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                query = query.filter(ActivityLog.created_at <= date_to_dt)
            except:
                pass
        
        activities = query.order_by(ActivityLog.created_at.desc()).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'User', 'Action Type', 'Entity Type', 'Description'])
        
        for activity in activities:
            writer.writerow([
                activity.created_at.strftime('%Y-%m-%d %H:%M:%S') if activity.created_at else '',
                activity.username or 'system',
                activity.action_type or '',
                activity.entity_type or '',
                activity.description or ''
            ])
        
        # Create file response
        output.seek(0)
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8'))
        mem.seek(0)
        
        filename = f'audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SYSTEM MONITORING APIs ====================

@admin_bp.route('/api/system/db-stats')
@admin_required
def api_db_stats():
    """API untuk database statistics"""
    from database import get_db_stats, ForecastHistory
    
    try:
        stats = get_db_stats()
        
        # Add forecast history count
        stats['forecast_history'] = ForecastHistory.query.count()
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/system/health')
@admin_required
def api_system_health():
    """API untuk system health status"""
    import os
    from datetime import datetime
    
    try:
        # Database connection check
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except:
            db_status = 'disconnected'
        
        # Try to import psutil
        try:
            import psutil
            psutil_available = True
        except ImportError:
            psutil_available = False
        
        # Get system info if psutil is available
        if psutil_available:
            try:
                memory = psutil.virtual_memory()
                process = psutil.Process(os.getpid())
                uptime_seconds = int((datetime.now().timestamp() - process.create_time()))
                memory_used = memory.used
                memory_total = memory.total
                memory_percent = memory.percent
            except Exception:
                # Fallback if psutil fails
                psutil_available = False
        
        if not psutil_available:
            # psutil not available, return minimal info
            uptime_seconds = 0
            memory_used = 0
            memory_total = 0
            memory_percent = 0
        
        # Determine health status
        health_status = 'healthy'
        if db_status != 'connected':
            health_status = 'critical'
        elif psutil_available and memory_percent > 90:
            health_status = 'warning'
        
        return jsonify({
            'success': True,
            'health': {
                'status': health_status,
                'database': db_status,
                'uptime_seconds': uptime_seconds,
                'server_time': datetime.now().isoformat(),
                'memory_used': memory_used,
                'memory_total': memory_total,
                'memory_percent': memory_percent
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/system/storage')
@admin_required
def api_system_storage():
    """API untuk storage information (Disederhanakan untuk Cloud)"""
    from config import Config
    
    try:
        
        return jsonify({
            'success': True,
            'storage': {
                'database_size': 0, # Tidak relevan di Cloud SQL
                'models_size': 0,   # Tidak relevan (read-only)
                'backups_size': 0,  # Tidak ada backup lokal
                'total_size': 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

