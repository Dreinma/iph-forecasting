# ✅ Checklist Deployment Hostinger

## 📋 **YANG PERLU DISESUAIKAN**

### **1. FILE YANG PERLU DIUPDATE** ⚙️

#### ✅ **config.py**
- [ ] Set `DEBUG = False` untuk production
- [ ] Update `SECRET_KEY` dari environment variable
- [ ] Update path database (gunakan absolute path)
- [ ] Update path upload folder (absolute path)
- [ ] Enable session security (COOKIE_SECURE, HTTPONLY)

#### ✅ **app.py**
- [x] ✅ Update untuk membaca PORT dari environment (SUDAH DILAKUKAN)
- [x] ✅ Update untuk production mode (SUDAH DILAKUKAN)

#### ✅ **Database Path**
- [ ] Pastikan path database menggunakan absolute path
- [ ] Contoh: `/var/www/iph-forecasting/data/prisma.db`
- [ ] Pastikan folder `data/` bisa write (chmod 775)

#### ✅ **Upload Folder**
- [ ] Pastikan `static/uploads/` menggunakan absolute path
- [ ] Set permission: `chmod 775 static/uploads/`
- [ ] Test upload file di production

---

### **2. ENVIRONMENT VARIABLES** 🔐

Buat file `.env` di server dengan isi:
```bash
FLASK_ENV=production
SECRET_KEY=<generate-random-32-char-key>
DATABASE_URL=sqlite:////var/www/iph-forecasting/data/prisma.db
```

Generate SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

### **3. SERVER SETUP** 🖥️

#### **Install Dependencies:**
- [ ] Python 3.11+
- [ ] pip dan virtualenv
- [ ] Nginx
- [ ] Gunicorn (sudah ada di requirements.txt)
- [ ] Supervisor (untuk auto-restart)
- [ ] Certbot (untuk SSL)

#### **Jalankan Setup Script:**
```bash
bash setup_hostinger.sh
```

---

### **4. KONFIGURASI SERVER** 📝

#### **Supervisor Config:**
- [ ] Buat file `/etc/supervisor/conf.d/iph-forecasting.conf`
- [ ] Set path aplikasi: `/var/www/iph-forecasting`
- [ ] Set command gunicorn dengan config file
- [ ] Start service: `sudo supervisorctl start iph-forecasting`

#### **Nginx Config:**
- [ ] Buat file `/etc/nginx/sites-available/iph-forecasting`
- [ ] Set reverse proxy ke `127.0.0.1:5001`
- [ ] Setup static files serving
- [ ] Enable site: `sudo ln -s sites-available/iph-forecasting sites-enabled/`
- [ ] Test: `sudo nginx -t`
- [ ] Restart: `sudo systemctl restart nginx`

#### **SSL Certificate:**
- [ ] Setup domain di DNS
- [ ] Jalankan: `sudo certbot --nginx -d your-domain.com`
- [ ] Test auto-renewal: `sudo certbot renew --dry-run`

---

### **5. PERMISSIONS** 🔒

Set permissions di server:
```bash
cd /var/www/iph-forecasting
sudo chown -R www-data:www-data .
sudo chmod -R 755 .
sudo chmod -R 775 data/
sudo chmod -R 775 static/uploads/
```

---

### **6. TESTING** ✅

Setelah deployment, test:
- [ ] Akses website via domain
- [ ] Login admin berfungsi
- [ ] Upload file berfungsi
- [ ] Generate forecast berfungsi
- [ ] Static files ter-load (CSS, JS, images)
- [ ] Database read/write berfungsi
- [ ] SSL certificate aktif (HTTPS)

---

### **7. MONITORING** 📊

Setup monitoring:
- [ ] Check logs: `/var/log/iph-forecasting-*.log`
- [ ] Check Nginx logs: `/var/log/nginx/iph-forecasting-*.log`
- [ ] Monitor supervisor: `sudo supervisorctl status`
- [ ] Monitor Nginx: `sudo systemctl status nginx`

---

## 📂 **FILE YANG DIBUAT UNTUK ANDA:**

1. ✅ `HOSTINGER_DEPLOYMENT.md` - Panduan lengkap deployment
2. ✅ `gunicorn_config.py` - Konfigurasi Gunicorn
3. ✅ `setup_hostinger.sh` - Script setup otomatis
4. ✅ `CHECKLIST_HOSTINGER.md` - Checklist ini

---

## 🚀 **LANGKAH RINGKAS:**

1. **Upload project** ke `/var/www/iph-forecasting`
2. **Jalankan setup:** `bash setup_hostinger.sh`
3. **Setup virtualenv:** `python3.11 -m venv venv`
4. **Install dependencies:** `pip install -r requirements.txt`
5. **Buat `.env`** dengan SECRET_KEY dan DATABASE_URL
6. **Setup Supervisor** config
7. **Setup Nginx** config
8. **Setup SSL** certificate
9. **Test** semua fungsi
10. **Monitor** logs

---

## ⚠️ **PENTING:**

1. **JANGAN commit** `.env` ke Git
2. **Pastikan** semua path menggunakan absolute path
3. **Test** di local dulu sebelum deploy
4. **Backup** database sebelum deployment
5. **Monitor** logs setelah deployment

---

## 📞 **BUTUH BANTUAN?**

Cek file `HOSTINGER_DEPLOYMENT.md` untuk panduan detail lengkap!

