#!/bin/bash
# Script untuk setup Supervisor configuration
# Usage: bash setup_supervisor.sh

APP_PATH="/var/www/iph-forecasting"
VENV_PATH="${APP_PATH}/venv"

echo "👨‍💼 Setting up Supervisor for IPH Forecasting..."

# Create Supervisor configuration
sudo tee /etc/supervisor/conf.d/iph-forecasting.conf > /dev/null <<EOF
[program:iph-forecasting]
directory=${APP_PATH}
command=${VENV_PATH}/bin/gunicorn app:app --bind 127.0.0.1:5001 --workers 2 --threads 2 --timeout 120 --access-logfile /var/log/iph-forecasting-access.log --error-logfile /var/log/iph-forecasting-error.log --log-level info
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/iph-forecasting.err.log
stdout_logfile=/var/log/iph-forecasting.out.log
environment=FLASK_ENV="production",PATH="${VENV_PATH}/bin"
EOF

# Create log files
echo "📝 Creating log files..."
sudo touch /var/log/iph-forecasting-access.log
sudo touch /var/log/iph-forecasting-error.log
sudo touch /var/log/iph-forecasting.err.log
sudo touch /var/log/iph-forecasting.out.log

# Set permissions
sudo chown www-data:www-data /var/log/iph-forecasting*.log

# Reload Supervisor
echo "🔄 Reloading Supervisor..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start iph-forecasting

# Check status
echo ""
echo "📊 Supervisor Status:"
sudo supervisorctl status iph-forecasting

echo ""
echo "✅ Supervisor setup complete!"

