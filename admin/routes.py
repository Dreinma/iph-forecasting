"""
Admin routes untuk IPH Forecasting Platform
CATATAN: Routes ini belum diintegrasikan ke app.py
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from auth.decorators import admin_required
from auth.forms import LoginForm, ChangePasswordForm, CreateAdminForm
from auth.utils import check_password, update_last_login, create_admin_user
from database import db, AdminUser

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
            # Debug: Print info untuk troubleshooting
            print(f"\n=== DEBUG LOGIN ===")
            print(f"Username: {form.username.data}")
            print(f"Password length: {len(form.password.data) if form.password.data else 0}")
            print(f"Password hash (first 30): {user.password_hash[:30] if user.password_hash else 'None'}...")
            print(f"Hash format: {'bcrypt' if user.password_hash and user.password_hash.startswith('$2b$') else 'werkzeug' if user.password_hash and user.password_hash.startswith('pbkdf2:') else 'unknown'}")
            
            password_check = check_password(user.password_hash, form.password.data)
            print(f"Password check result: {password_check}")
            print(f"===================\n")
            
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
                
                session['user_role'] = 'admin'
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

@admin_bp.route('/alerts')
@admin_required
def alerts_manage():
    """Alert management page (different from public /alerts)"""
    return render_template('admin/alerts_manage.html', page_title="Alert Management")

@admin_bp.route('/settings')
@admin_required
def settings():
    """System settings page"""
    from database import AdminUser
    admin_users = AdminUser.query.all()
    return render_template('admin/settings.html', 
                         page_title="System Settings",
                         admin_users=admin_users)

@admin_bp.route('/create-admin', methods=['GET', 'POST'])
@admin_required
def create_admin():
    """Create new admin user"""
    from auth.forms import CreateAdminForm
    
    form = CreateAdminForm()
    
    if form.validate_on_submit():
        admin_user, message = create_admin_user(
            form.username.data,
            form.password.data,
            form.email.data if form.email.data else None
        )
        
        if admin_user:
            flash(f'Admin user "{form.username.data}" berhasil dibuat!', 'success')
            return redirect(url_for('admin.settings'))
        else:
            flash(f'Error: {message}', 'danger')
    
    return render_template('admin/create_admin.html', form=form, page_title="Create Admin User")

# ==================== API ROUTES ====================

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

@admin_bp.route('/api/models/retrain', methods=['POST'])
@admin_required
def api_retrain_models():
    """API untuk retrain models (specific atau semua)"""
    from app import forecast_service
    from flask_login import current_user
    
    try:
        data = request.get_json() or {}
        model_name = data.get('model_name')  # None = retrain all
        
        # Load historical data
        df = forecast_service.data_handler.load_historical_data()
        
        if df is None or df.empty:
            return jsonify({
                'success': False,
                'message': 'No historical data available for training'
            }), 400
        
        # Retrain models
        result = forecast_service.model_manager.train_and_compare_models(df)
        
        # Log activity
        try:
            from database import ActivityLog
            activity = ActivityLog(
                user_id=current_user.id if current_user.is_authenticated else None,
                username=current_user.username if current_user.is_authenticated else 'system',
                action_type='train',
                entity_type='model',
                description=f'Retrained models: {", ".join(result.get("summary", {}).get("models_trained", []))}'
            )
            db.session.add(activity)
            db.session.commit()
        except:
            db.session.rollback()
        
        return jsonify({
            'success': True,
            'message': 'Models retrained successfully',
            'best_model': result['summary']['best_model'],
            'summary': {
                'models_trained': result['summary']['total_models_trained'],
                'is_improvement': result['summary']['is_improvement'],
                'best_mae': result['comparison']['new_best_model']['mae']
            }
        })
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

# ==================== FORECAST MANAGEMENT APIs ====================

@admin_bp.route('/api/forecasts/history')
@admin_required
def api_forecast_history():
    """API untuk forecast history dengan filter"""
    from database import ForecastHistory
    from sqlalchemy import func
    
    try:
        model_filter = request.args.get('model', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = ForecastHistory.query
        
        if model_filter:
            query = query.filter(ForecastHistory.model_name == model_filter)
        
        pagination = query.order_by(ForecastHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        data = {
            'items': [forecast.to_dict() for forecast in pagination.items],
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

