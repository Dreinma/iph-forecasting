# 🚀 Panduan Deployment Lengkap - Hostinger dengan Subdomain

## 📋 **Informasi Awal**

Berdasarkan screenshot, Anda memiliki:
- Domain: `bpskotabatu.com`
- Akses DNS Management di Hostinger
- Akses VPS/Server Hostinger

Kita akan deploy ke subdomain seperti: `prisma.bpskotabatu.com` atau `iph.bpskotabatu.com`

---

## 🎯 **LANGKAH 1: SETUP SUBDOMAIN DI HOSTINGER**

### **1.1. Login ke Hostinger Panel**
1. Buka https://hpanel.hostinger.com
2. Login dengan akun Hostinger Anda
3. Pilih domain `bpskotabatu.com`

### **1.2. Setup DNS Record untuk Subdomain**

1. Masuk ke **DNS/Nameserver** (seperti di screenshot)
2. Klik **"Tambah Record"** atau **"Add Record"**
3. Tambahkan **A Record** baru:

**Konfigurasi A Record:**
- **Type:** A
- **Nama:** `prisma` (untuk `prisma.bpskotabatu.com`) atau `iph` (untuk `iph.bpskotabatu.com`)
- **Konten/Value:** IP Address VPS Hostinger Anda (dapatkan dari halaman VPS di Hostinger)
- **TTL:** 14400 (default)
- **Prioritas:** 0

**Contoh:**
```
Type: A
Nama: prisma
Konten: 168.231.103.168  (gunakan IP VPS Anda)
TTL: 14400
```

4. Klik **"Simpan"** atau **"Save"**
5. Tunggu 5-15 menit untuk DNS propagation

**Note:** Jika Anda menggunakan IP yang sama dengan subdomain lain (`www.podes`, `apibatas`, dll), Anda bisa gunakan IP yang sama (`168.231.103.168`)

---

## 🖥️ **LANGKAH 2: AKSES SERVER VPS HOSTINGER**

### **2.1. Dapatkan Kredensial SSH**

Dari Hostinger Panel:
1. Buka halaman **VPS** Anda
2. Cari **SSH Access** atau **Server Information**
3. Catat:
   - **IP Address:** `xxx.xxx.xxx.xxx`
   - **Username:** biasanya `root` atau `u123456789`
   - **Password:** password SSH Anda
   - **Port SSH:** biasanya `22` atau `2222`

### **2.2. Koneksi ke Server**

**Windows (PowerShell/Git Bash):**
```bash
ssh root@YOUR_IP_ADDRESS
# atau
ssh username@YOUR_IP_ADDRESS -p 2222
```

**Mac/Linux:**
```bash
ssh root@YOUR_IP_ADDRESS
```

Masukkan password ketika diminta.

---

## 📦 **LANGKAH 3: INSTALL DEPENDENCIES DI SERVER**

### **3.1. Update System**
```bash
sudo apt update
sudo apt upgrade -y
```

### **3.2. Install Python 3.11**
```bash
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y
python3.11 --version  # Verify installation
```

### **3.3. Install Nginx**
```bash
sudo apt install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

### **3.4. Install Supervisor**
```bash
sudo apt install supervisor -y
sudo systemctl start supervisor
sudo systemctl enable supervisor
```

### **3.5. Install Certbot (untuk SSL)**
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### **3.6. Install Dependencies Tambahan**
```bash
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y
sudo apt install git -y  # jika ingin menggunakan git
```

---

## 📁 **LANGKAH 4: PREPARASI PROJECT**

### **4.1. Buat Directory Aplikasi**
```bash
# Buat folder aplikasi
sudo mkdir -p /var/www/iph-forecasting
sudo chown $USER:$USER /var/www/iph-forecasting
cd /var/www/iph-forecasting
```

### **4.2. Upload Project Files**

**Opsi A: Menggunakan Git (Recommended)**
```bash
cd /var/www/iph-forecasting
git clone https://github.com/YOUR_USERNAME/iph-forecasting.git .
# atau jika repo sudah ada:
git pull origin main
```

**Opsi B: Menggunakan SCP (dari local Windows/Mac)**
```bash
# Dari komputer local (PowerShell/Git Bash):
scp -r * root@YOUR_IP_ADDRESS:/var/www/iph-forecasting/
```

**Opsi C: Menggunakan File Manager Hostinger**
1. Login ke Hostinger File Manager
2. Upload semua file ke `/var/www/iph-forecasting/`

### **4.3. File yang Harus Diupload:**
```
iph-forecasting/
├── app.py
├── config.py
├── database.py
├── requirements.txt
├── Procfile
├── gunicorn_config.py
├── services/
├── models/
├── admin/
├── auth/
├── templates/
├── static/
└── data/  (kosongkan, akan dibuat otomatis)
```

**❌ JANGAN Upload:**
- `.env`
- `*.db` (database)
- `*.pkl` (model files, bisa upload nanti)
- `__pycache__/`
- `venv/`
- `*.log`

---

## 🐍 **LANGKAH 5: SETUP PYTHON VIRTUAL ENVIRONMENT**

```bash
cd /var/www/iph-forecasting

# Buat virtual environment
python3.11 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Verifikasi instalasi:**
```bash
pip list | grep -i flask
pip list | grep -i gunicorn
```

---

## 🔐 **LANGKAH 6: SETUP ENVIRONMENT VARIABLES**

### **6.1. Buat File .env**
```bash
cd /var/www/iph-forecasting
nano .env
```

### **6.2. Isi File .env:**
```bash
# Flask Environment
FLASK_ENV=production

# Secret Key (generate random key)
SECRET_KEY=GENERATE_RANDOM_KEY_HERE

# Database (gunakan absolute path untuk SQLite)
DATABASE_URL=sqlite:////var/www/iph-forecasting/data/prisma.db

# Port (jika diperlukan)
PORT=5001
```

### **6.3. Generate Secret Key:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy output dan paste ke `.env` sebagai `SECRET_KEY`.

**Save file:** Tekan `Ctrl+O`, Enter, lalu `Ctrl+X`

---

## 📂 **LANGKAH 7: SETUP DIRECTORY & PERMISSIONS**

```bash
cd /var/www/iph-forecasting

# Buat folder yang diperlukan
mkdir -p data/models
mkdir -p data/backups
mkdir -p static/uploads

# Set permissions
sudo chown -R www-data:www-data /var/www/iph-forecasting
sudo chmod -R 755 /var/www/iph-forecasting
sudo chmod -R 775 data/
sudo chmod -R 775 static/uploads/
```

---

## 🧪 **LANGKAH 8: TEST APLIKASI**

### **8.1. Test Flask App**
```bash
cd /var/www/iph-forecasting
source venv/bin/activate

# Test Flask langsung
python app.py
# Buka browser: http://YOUR_IP:5001
# Jika berhasil, stop dengan Ctrl+C
```

### **8.2. Test Gunicorn**
```bash
source venv/bin/activate

# Test gunicorn
gunicorn app:app --bind 0.0.0.0:5001 --workers 2

# Buka browser: http://YOUR_IP:5001
# Jika berhasil, stop dengan Ctrl+C
```

---

## ⚙️ **LANGKAH 9: SETUP SUPERVISOR (PROCESS MANAGER)**

### **9.1. Buat Supervisor Configuration**

```bash
sudo nano /etc/supervisor/conf.d/iph-forecasting.conf
```

### **9.2. Isi Configuration:**

```ini
[program:iph-forecasting]
directory=/var/www/iph-forecasting
command=/var/www/iph-forecasting/venv/bin/gunicorn app:app --bind 127.0.0.1:5001 --workers 2 --threads 2 --timeout 120 --access-logfile /var/log/iph-forecasting-access.log --error-logfile /var/log/iph-forecasting-error.log --log-level info
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/iph-forecasting.err.log
stdout_logfile=/var/log/iph-forecasting.out.log
environment=FLASK_ENV="production",PATH="/var/www/iph-forecasting/venv/bin"
```

**Save:** `Ctrl+O`, Enter, `Ctrl+X`

### **9.3. Setup Supervisor**
```bash
# Create log files
sudo touch /var/log/iph-forecasting-access.log
sudo touch /var/log/iph-forecasting-error.log
sudo touch /var/log/iph-forecasting.err.log
sudo touch /var/log/iph-forecasting.out.log

# Set permissions
sudo chown www-data:www-data /var/log/iph-forecasting*.log

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start iph-forecasting
sudo supervisorctl status
```

**Verifikasi:**
```bash
sudo supervisorctl status iph-forecasting
# Harus menampilkan: iph-forecasting    RUNNING   pid 12345, uptime 0:00:10
```

---

## 🌐 **LANGKAH 10: SETUP NGINX (REVERSE PROXY)**

### **10.1. Buat Nginx Configuration untuk Subdomain**

```bash
sudo nano /etc/nginx/sites-available/prisma.bpskotabatu.com
```

**Ganti `prisma.bpskotabatu.com` dengan subdomain yang Anda gunakan!**

### **10.2. Isi Nginx Configuration:**

```nginx
# HTTP Server (akan redirect ke HTTPS setelah SSL setup)
server {
    listen 80;
    server_name prisma.bpskotabatu.com;

    # Redirect ke HTTPS (uncomment setelah SSL setup)
    # return 301 https://$server_name$request_uri;

    # Untuk testing tanpa SSL dulu, gunakan ini:
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeout settings
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static files (CSS, JS, images)
    location /static {
        alias /var/www/iph-forecasting/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Upload files
    location /static/uploads {
        alias /var/www/iph-forecasting/static/uploads;
        client_max_body_size 16M;
    }

    # Logs
    access_log /var/log/nginx/prisma-access.log;
    error_log /var/log/nginx/prisma-error.log;
}
```

**Save:** `Ctrl+O`, Enter, `Ctrl+X`

### **10.3. Enable Site & Test**

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/prisma.bpskotabatu.com /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Jika test berhasil, restart Nginx
sudo systemctl restart nginx

# Check Nginx status
sudo systemctl status nginx
```

### **10.4. Verifikasi**

Buka browser dan akses:
- **HTTP:** `http://prisma.bpskotabatu.com`

Jika berhasil, lanjutkan ke setup SSL.

---

## 🔒 **LANGKAH 11: SETUP SSL CERTIFICATE (HTTPS)**

### **11.1. Pastikan DNS Sudah Propagate**

Cek dengan command:
```bash
nslookup prisma.bpskotabatu.com
# atau
dig prisma.bpskotabatu.com
```

Pastikan mengarah ke IP VPS Anda.

### **11.2. Setup SSL dengan Certbot**

```bash
sudo certbot --nginx -d prisma.bpskotabatu.com
```

Ikuti prompt:
1. Enter email address (untuk notifikasi renewal)
2. Agree to terms (A)
3. Share email with EFF? (opsional, Y/N)
4. Certbot akan otomatis setup SSL

### **11.3. Verifikasi SSL**

Buka browser:
- **HTTPS:** `https://prisma.bpskotabatu.com`

### **11.4. Test Auto-Renewal**

```bash
sudo certbot renew --dry-run
```

Certbot akan auto-renew setiap 90 hari.

---

## 🔄 **LANGKAH 12: UPDATE NGINX SETELAH SSL**

Setelah SSL setup, Certbot akan otomatis update Nginx config. Tapi jika perlu manual, update ke:

```nginx
# HTTPS Server
server {
    listen 443 ssl http2;
    server_name prisma.bpskotabatu.com;

    # SSL Certificates (auto-generated by Certbot)
    ssl_certificate /etc/letsencrypt/live/prisma.bpskotabatu.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/prisma.bpskotabatu.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Reverse Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
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
    access_log /var/log/nginx/prisma-access.log;
    error_log /var/log/nginx/prisma-error.log;
}

# HTTP to HTTPS Redirect
server {
    listen 80;
    server_name prisma.bpskotabatu.com;
    return 301 https://$server_name$request_uri;
}
```

Reload Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🧪 **LANGKAH 13: TESTING FINAL**

### **13.1. Test Website**
- [ ] Akses: `https://prisma.bpskotabatu.com`
- [ ] Halaman utama load dengan benar
- [ ] Static files (CSS, JS, images) ter-load
- [ ] SSL certificate aktif (gembok hijau)

### **13.2. Test Functionality**
- [ ] Login admin berfungsi
- [ ] Generate forecast berfungsi
- [ ] Upload data berfungsi
- [ ] Dashboard load dengan benar
- [ ] Commodity insights load dengan benar

### **13.3. Test Database**
```bash
cd /var/www/iph-forecasting
source venv/bin/activate
python3 -c "from database import db, IPHData; print(f'IPHData records: {IPHData.query.count()}')"
```

---

## 📊 **LANGKAH 14: MONITORING & LOGS**

### **14.1. Check Application Logs**
```bash
# Application logs
sudo tail -f /var/log/iph-forecasting-access.log
sudo tail -f /var/log/iph-forecasting-error.log
sudo tail -f /var/log/iph-forecasting.err.log
sudo tail -f /var/log/iph-forecasting.out.log
```

### **14.2. Check Nginx Logs**
```bash
# Nginx logs
sudo tail -f /var/log/nginx/prisma-access.log
sudo tail -f /var/log/nginx/prisma-error.log
```

### **14.3. Check Supervisor Status**
```bash
sudo supervisorctl status iph-forecasting
```

### **14.4. Check Nginx Status**
```bash
sudo systemctl status nginx
```

---

## 🔄 **LANGKAH 15: UPDATE & MAINTENANCE**

### **15.1. Update Aplikasi**

```bash
cd /var/www/iph-forecasting
source venv/bin/activate

# Jika menggunakan Git:
git pull origin main

# Update dependencies (jika ada perubahan)
pip install -r requirements.txt --upgrade

# Restart aplikasi
sudo supervisorctl restart iph-forecasting

# Check status
sudo supervisorctl status iph-forecasting
```

### **15.2. Backup Database**

```bash
# Backup database
cp /var/www/iph-forecasting/data/prisma.db /var/www/iph-forecasting/data/backups/prisma_$(date +%Y%m%d_%H%M%S).db
```

---

## ⚠️ **TROUBLESHOOTING**

### **Problem 1: Website tidak bisa diakses**

**Cek:**
```bash
# Check DNS
nslookup prisma.bpskotabatu.com

# Check Nginx
sudo systemctl status nginx
sudo nginx -t

# Check Supervisor
sudo supervisorctl status iph-forecasting

# Check port
sudo netstat -tulpn | grep 5001
```

### **Problem 2: 502 Bad Gateway**

**Kemungkinan:**
- Gunicorn tidak berjalan
- Port tidak match

**Fix:**
```bash
sudo supervisorctl restart iph-forecasting
sudo systemctl restart nginx
```

### **Problem 3: 500 Internal Server Error**

**Cek logs:**
```bash
sudo tail -50 /var/log/iph-forecasting-error.log
sudo tail -50 /var/log/nginx/prisma-error.log
```

**Kemungkinan:**
- Permission issue
- Database path salah
- Missing dependencies

### **Problem 4: Static files tidak load**

**Fix:**
```bash
sudo chown -R www-data:www-data /var/www/iph-forecasting/static
sudo chmod -R 755 /var/www/iph-forecasting/static
```

### **Problem 5: Upload file gagal**

**Fix:**
```bash
sudo chmod -R 775 /var/www/iph-forecasting/static/uploads
sudo chown -R www-data:www-data /var/www/iph-forecasting/static/uploads
```

### **Problem 6: Database tidak bisa write**

**Fix:**
```bash
sudo chmod -R 775 /var/www/iph-forecasting/data
sudo chown -R www-data:www-data /var/www/iph-forecasting/data
```

---

## ✅ **CHECKLIST FINAL**

Setelah semua langkah, pastikan:

- [x] DNS A Record untuk subdomain sudah dibuat
- [x] DNS sudah propagate (cek dengan nslookup)
- [x] Semua dependencies terinstall
- [x] Virtual environment setup
- [x] File .env sudah dibuat dengan SECRET_KEY
- [x] Supervisor running (`sudo supervisorctl status`)
- [x] Nginx running (`sudo systemctl status nginx`)
- [x] SSL certificate aktif
- [x] Website bisa diakses via HTTPS
- [x] Static files ter-load
- [x] Login admin berfungsi
- [x] Upload file berfungsi
- [x] Database read/write berfungsi
- [x] Logs berfungsi

---

## 📝 **QUICK REFERENCE COMMANDS**

```bash
# Restart aplikasi
sudo supervisorctl restart iph-forecasting

# Restart Nginx
sudo systemctl restart nginx

# Check status
sudo supervisorctl status
sudo systemctl status nginx

# View logs
sudo tail -f /var/log/iph-forecasting-error.log
sudo tail -f /var/log/nginx/prisma-error.log

# Reload Nginx config
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🎉 **SELESAI!**

Aplikasi Anda sekarang sudah live di `https://prisma.bpskotabatu.com` (atau subdomain yang Anda pilih)!

**Next Steps:**
1. Upload data historis via admin panel
2. Upload model files (jika ada) ke `data/models/`
3. Setup admin user pertama kali
4. Monitor logs untuk beberapa hari pertama

