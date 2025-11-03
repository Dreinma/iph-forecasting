#!/bin/bash
# Script untuk setup Nginx configuration untuk subdomain
# Usage: bash setup_nginx_subdomain.sh <subdomain> <domain>
# Example: bash setup_nginx_subdomain.sh prisma bpskotabatu.com

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <subdomain> <domain>"
    echo "Example: $0 prisma bpskotabatu.com"
    exit 1
fi

SUBDOMAIN=$1
DOMAIN=$2
FULL_DOMAIN="${SUBDOMAIN}.${DOMAIN}"
APP_PATH="/var/www/iph-forecasting"

echo "🔧 Setting up Nginx for ${FULL_DOMAIN}..."

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/${FULL_DOMAIN} > /dev/null <<EOF
# HTTP Server (will redirect to HTTPS after SSL setup)
server {
    listen 80;
    server_name ${FULL_DOMAIN};

    # For testing without SSL first:
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeout settings
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static files
    location /static {
        alias ${APP_PATH}/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Upload files
    location /static/uploads {
        alias ${APP_PATH}/static/uploads;
        client_max_body_size 16M;
    }

    # Logs
    access_log /var/log/nginx/${SUBDOMAIN}-access.log;
    error_log /var/log/nginx/${SUBDOMAIN}-error.log;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/${FULL_DOMAIN} /etc/nginx/sites-enabled/

# Test configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration valid!"
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    echo "✅ Done! Your site should be accessible at http://${FULL_DOMAIN}"
    echo ""
    echo "📋 Next steps:"
    echo "1. Setup DNS A record for ${SUBDOMAIN} pointing to your VPS IP"
    echo "2. Wait for DNS propagation (5-15 minutes)"
    echo "3. Setup SSL: sudo certbot --nginx -d ${FULL_DOMAIN}"
else
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

