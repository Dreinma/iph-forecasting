#!/bin/bash
# Quick Start Deployment Script untuk Hostinger
# Usage: bash deploy_quick_start.sh

set -e  # Exit on error

echo "🚀 IPH Forecasting - Quick Deployment Script"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Don't run this script as root!"
    echo "Run as regular user, script will use sudo when needed"
    exit 1
fi

# Variables
APP_PATH="/var/www/iph-forecasting"
VENV_PATH="${APP_PATH}/venv"

# Ask for subdomain
read -p "Enter subdomain name (e.g., prisma or iph): " SUBDOMAIN
read -p "Enter domain name (e.g., bpskotabatu.com): " DOMAIN
FULL_DOMAIN="${SUBDOMAIN}.${DOMAIN}"

echo ""
echo "📋 Configuration:"
echo "  Subdomain: ${SUBDOMAIN}"
echo "  Domain: ${DOMAIN}"
echo "  Full domain: ${FULL_DOMAIN}"
echo "  App path: ${APP_PATH}"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: Install dependencies
echo ""
echo "📦 Step 1: Installing system dependencies..."
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip \
    nginx supervisor certbot python3-certbot-nginx \
    build-essential libssl-dev libffi-dev python3-dev git

# Step 2: Create directory
echo ""
echo "📁 Step 2: Creating application directory..."
sudo mkdir -p ${APP_PATH}
sudo chown $USER:$USER ${APP_PATH}

echo "✅ Directory created: ${APP_PATH}"
echo "⚠️  IMPORTANT: Upload your project files to ${APP_PATH} first!"
echo ""
read -p "Press Enter after uploading files..."

# Step 3: Setup virtual environment
echo ""
echo "🐍 Step 3: Setting up Python virtual environment..."
cd ${APP_PATH}
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Step 4: Install Python dependencies
echo ""
echo "📦 Step 4: Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Step 5: Create .env file
echo ""
echo "🔐 Step 5: Creating .env file..."
if [ ! -f ".env" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > .env <<EOF
FLASK_ENV=production
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=sqlite:////var/www/iph-forecasting/data/prisma.db
PORT=5001
EOF
    echo "✅ .env file created with generated SECRET_KEY"
else
    echo "⚠️  .env file already exists, skipping..."
fi

# Step 6: Setup directories and permissions
echo ""
echo "📂 Step 6: Setting up directories and permissions..."
mkdir -p data/models data/backups static/uploads
sudo chown -R www-data:www-data ${APP_PATH}
sudo chmod -R 755 ${APP_PATH}
sudo chmod -R 775 data/ static/uploads/

# Step 7: Setup Supervisor
echo ""
echo "👨‍💼 Step 7: Setting up Supervisor..."
bash ${APP_PATH}/setup_supervisor.sh

# Step 8: Setup Nginx
echo ""
echo "🌐 Step 8: Setting up Nginx..."
bash ${APP_PATH}/setup_nginx_subdomain.sh ${SUBDOMAIN} ${DOMAIN}

# Step 9: Final instructions
echo ""
echo "✅ Deployment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Setup DNS A record in Hostinger:"
echo "   - Type: A"
echo "   - Name: ${SUBDOMAIN}"
echo "   - Value: $(curl -s ifconfig.me)"  # Get public IP
echo "   - TTL: 14400"
echo ""
echo "2. Wait for DNS propagation (5-15 minutes)"
echo ""
echo "3. Test website:"
echo "   http://${FULL_DOMAIN}"
echo ""
echo "4. Setup SSL certificate:"
echo "   sudo certbot --nginx -d ${FULL_DOMAIN}"
echo ""
echo "5. Check logs if needed:"
echo "   sudo tail -f /var/log/iph-forecasting-error.log"
echo "   sudo tail -f /var/log/nginx/${SUBDOMAIN}-error.log"
echo ""
echo "🎉 Done!"

