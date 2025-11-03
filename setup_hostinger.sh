#!/bin/bash
# Setup script untuk Hostinger VPS
# Jalankan dengan: bash setup_hostinger.sh

echo "🚀 Setting up IPH Forecasting Platform on Hostinger..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Nginx
echo "🌐 Installing Nginx..."
sudo apt install nginx -y

# Install Supervisor
echo "👨‍💼 Installing Supervisor..."
sudo apt install supervisor -y

# Install Certbot (for SSL)
echo "🔒 Installing Certbot..."
sudo apt install certbot python3-certbot-nginx -y

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/iph-forecasting
sudo chown $USER:$USER /var/www/iph-forecasting

# Create log directory
echo "📝 Creating log directory..."
sudo mkdir -p /var/log/iph-forecasting
sudo touch /var/log/iph-forecasting-access.log
sudo touch /var/log/iph-forecasting-error.log
sudo chown www-data:www-data /var/log/iph-forecasting-*.log

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Upload project files to /var/www/iph-forecasting"
echo "2. Create virtual environment: python3.11 -m venv venv"
echo "3. Install dependencies: pip install -r requirements.txt"
echo "4. Setup .env file with SECRET_KEY and DATABASE_URL"
echo "5. Setup Supervisor configuration"
echo "6. Setup Nginx configuration"
echo "7. Setup SSL certificate"

