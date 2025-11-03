# 🚀 Panduan Deployment Hostinger - IPH Forecasting Platform

## 📋 **Yang Perlu Disesuaikan untuk Hostinger**

Hostinger biasanya menyediakan VPS atau Cloud Hosting dengan akses SSH. Berikut yang perlu disesuaikan:

---

## ✅ **CHECKLIST SEBELUM DEPLOYMENT**

### **1. Persiapan Project**
- [x] ✅ Update `app.py` untuk production (SUDAH)
- [x] ✅ Tambahkan `gunicorn` ke requirements.txt (SUDAH)
- [x] ✅ Buat `Procfile` (SUDAH)
- [ ] Update database path (jika perlu)
- [ ] Update file upload path
- [ ] Set environment variables
- [ ] Test aplikasi local dulu

### **2. Server Configuration**
- [ ] Install Python 3.11+ di server
- [ ] Install pip dan virtual environment
- [ ] Setup Nginx sebagai reverse proxy
- [ ] Setup Gunicorn sebagai WSGI server
- [ ] Setup Supervisor/Systemd untuk process management
- [ ] Setup SSL certificate (Let's Encrypt)
- [ ] Konfigurasi firewall

### **3. Database**
- [ ] Pilih: SQLite (sederhana) atau PostgreSQL (production)
- [ ] Setup database connection
- [ ] Migrate data (jika ada data existing)

---

## 🔧 **KONFIGURASI YANG PERLU DISESUAIKAN**

### **1. Update `config.py`**

Tambahkan konfigurasi production khusus Hostinger:

```python
import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    DEBUG = False  # Set False untuk production
    
    # Database Configuration
    # Opsi 1: SQLite (sederhana, untuk start)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "prisma.db"))}'
    
    # Opsi 2: PostgreSQL (recommended untuk production)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'postgresql://user:password@localhost/prisma_db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
    
    # Data Storage - Pastikan path absolute
    DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    MODELS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'models'))
    BACKUPS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'backups'))
    
    # Session Configuration (Production)
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        directories = [
            Config.UPLOAD_FOLDER,
            Config.DATA_FOLDER,
            Config.MODELS_PATH,
            Config.BACKUPS_PATH
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        print("Application directories initialized")

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Production secret key (set via environment)
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    
    # Production database
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

### **2. Update Path di `app.py` (jika perlu)**

Pastikan semua path menggunakan absolute path:

```python
# Di bagian atas app.py, tambahkan:
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Update config loading:
app.config.from_object('config.ProductionConfig')  # Untuk production
```

### **3. Buat File `.env` (untuk environment variables)**

```bash
# .env (JANGAN commit ke Git!)
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this
DATABASE_URL=sqlite:///data/prisma.db
# atau untuk PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/prisma_db
```

### **4. Update `.gitignore`**

Pastikan file sensitif tidak ter-commit:

```gitignore
.env
.env.local
*.db
data/prisma.db
data/models/*.pkl
data/backups/*
data/debug.log
*.log
__pycache__/
*.pyc
```

---

## 🖥️ **SETUP DI HOSTINGER VPS**

### **Langkah 1: Akses Server**
```bash
ssh root@your-server-ip
# atau
ssh your-username@your-domain.com
```

### **Langkah 2: Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Nginx
sudo apt install nginx -y

# Install PostgreSQL (optional, untuk production)
sudo apt install postgresql postgresql-contrib -y

# Install Supervisor (untuk process management)
sudo apt install supervisor -y

# Install certbot (untuk SSL)
sudo apt install certbot python3-certbot-nginx -y
```

### **Langkah 3: Setup Project**
```bash
# Buat directory untuk aplikasi
sudo mkdir -p /var/www/iph-forecasting
sudo chown $USER:$USER /var/www/iph-forecasting

# Clone atau upload project
cd /var/www/iph-forecasting
# (upload files dari local, atau git clone)

# Buat virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Test aplikasi
python app.py
# Jika berhasil, stop dengan Ctrl+C
```

### **Langkah 4: Setup Gunicorn**
```bash
# Install gunicorn (sudah ada di requirements.txt)
pip install gunicorn

# Test gunicorn
gunicorn app:app --bind 0.0.0.0:5001

# Jika berhasil, stop dengan Ctrl+C
```

### **Langkah 5: Setup Supervisor (Process Manager)**

Buat file `/etc/supervisor/conf.d/iph-forecasting.conf`:

```ini
[program:iph-forecasting]
directory=/var/www/iph-forecasting
command=/var/www/iph-forecasting/venv/bin/gunicorn app:app --bind 127.0.0.1:5001 --workers 2 --threads 2 --timeout 120 --access-logfile /var/log/iph-forecasting-access.log --error-logfile /var/log/iph-forecasting-error.log
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/iph-forecasting.err.log
stdout_logfile=/var/log/iph-forecasting.out.log
environment=PATH="/var/www/iph-forecasting/venv/bin"
```

Reload supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start iph-forecasting
sudo supervisorctl status
```

### **Langkah 6: Setup Nginx (Reverse Proxy)**

Buat file `/etc/nginx/sites-available/iph-forecasting`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect to HTTPS (setelah setup SSL)
    # return 301 https://$server_name$request_uri;

    # Untuk testing tanpa SSL, gunakan ini:
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static {
        alias /var/www/iph-forecasting/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Upload files
    location /static/uploads {
        alias /var/www/iph-forecasting/static/uploads;
        client_max_body_size 16M;
    }

    # Logs
    access_log /var/log/nginx/iph-forecasting-access.log;
    error_log /var/log/nginx/iph-forecasting-error.log;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/iph-forecasting /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### **Langkah 7: Setup SSL (Let's Encrypt)**
```bash
# Setup SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (sudah otomatis, tapi test dengan):
sudo certbot renew --dry-run
```

Setelah SSL setup, update Nginx config untuk HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /var/www/iph-forecasting/static;
        expires 30d;
    }
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 📝 **FILE YANG PERLU DIUPLOAD KE SERVER**

1. ✅ Semua file Python (`*.py`)
2. ✅ `requirements.txt`
3. ✅ `templates/` folder
4. ✅ `static/` folder
5. ✅ `models/` folder (jika ada)
6. ✅ `data/` folder (untuk database, kosongkan dulu)
7. ❌ **JANGAN upload**: `.env`, `*.db`, `*.pkl`, `__pycache__/`

---

## 🔐 **ENVIRONMENT VARIABLES**

Buat file `.env` di server:
```bash
cd /var/www/iph-forecasting
nano .env
```

Isi:
```bash
FLASK_ENV=production
SECRET_KEY=generate-random-key-here-min-32-chars
DATABASE_URL=sqlite:////var/www/iph-forecasting/data/prisma.db
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📂 **PERMISSIONS**

```bash
# Set permissions
cd /var/www/iph-forecasting
sudo chown -R www-data:www-data .
sudo chmod -R 755 .
sudo chmod -R 775 data/
sudo chmod -R 775 static/uploads/
```

---

## 🔄 **UPDATE & MAINTENANCE**

### Update aplikasi:
```bash
cd /var/www/iph-forecasting
source venv/bin/activate
git pull  # jika pakai git
# atau upload files baru

pip install -r requirements.txt --upgrade
sudo supervisorctl restart iph-forecasting
```

### View logs:
```bash
# Application logs
sudo tail -f /var/log/iph-forecasting.err.log
sudo tail -f /var/log/iph-forecasting.out.log

# Nginx logs
sudo tail -f /var/log/nginx/iph-forecasting-error.log
sudo tail -f /var/log/nginx/iph-forecasting-access.log
```

---

## ⚠️ **TROUBLESHOOTING**

### Port sudah digunakan:
```bash
sudo netstat -tulpn | grep 5001
# Kill process jika perlu
sudo kill -9 <PID>
```

### Permission denied:
```bash
sudo chown -R www-data:www-data /var/www/iph-forecasting
sudo chmod -R 755 /var/www/iph-forecasting
```

### Database tidak bisa write:
```bash
sudo chmod -R 775 /var/www/iph-forecasting/data
sudo chown -R www-data:www-data /var/www/iph-forecasting/data
```

---

## ✅ **CHECKLIST FINAL**

- [ ] Aplikasi berjalan dengan Gunicorn
- [ ] Nginx reverse proxy berfungsi
- [ ] SSL certificate aktif
- [ ] Static files ter-load
- [ ] Database bisa read/write
- [ ] Upload files berfungsi
- [ ] Admin login berfungsi
- [ ] Semua routes accessible
- [ ] Logs berfungsi
- [ ] Auto-restart saat reboot (supervisor)

---

## 📞 **SUPPORT**

Jika ada masalah, cek:
1. Logs aplikasi: `/var/log/iph-forecasting-*.log`
2. Logs Nginx: `/var/log/nginx/iph-forecasting-*.log`
3. Supervisor status: `sudo supervisorctl status`
4. Nginx status: `sudo systemctl status nginx`

