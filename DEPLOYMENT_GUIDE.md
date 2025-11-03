# 🚀 Deployment Guide - IPH Forecasting Platform

## 📋 **Rekomendasi Platform Deployment**

Berdasarkan project ini (Flask + SQLite + ML Models), berikut rekomendasi platform:

### 🥇 **1. Render.com** (Rekomendasi Utama)
**✅ Kelebihan:**
- ✅ Free tier tersedia (hobby plan)
- ✅ Mudah setup (connect GitHub langsung)
- ✅ Auto-deploy dari Git
- ✅ Support PostgreSQL (upgrade dari SQLite)
- ✅ Custom domain support
- ✅ SSL certificate gratis
- ✅ Buildpack Python otomatis

**Setup:**
1. Push project ke GitHub
2. Buat akun Render.com
3. New → Web Service → Connect GitHub repo
4. Environment: `Python 3`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
7. Set environment variables di dashboard

**Port Configuration:**
- Render menggunakan environment variable `PORT`
- Update `app.py` untuk membaca `PORT` dari env

---

### 🥈 **2. Railway.app**
**✅ Kelebihan:**
- ✅ Free tier ($5 credit/bulan)
- ✅ Auto-deploy dari Git
- ✅ Support PostgreSQL gratis
- ✅ Environment variables mudah
- ✅ Logs real-time
- ✅ Custom domain

**Setup:**
1. Push ke GitHub
2. New Project → Deploy from GitHub
3. Add PostgreSQL (opsional)
4. Railway auto-detect Python
5. Set start command: `gunicorn app:app`

---

### 🥉 **3. PythonAnywhere**
**✅ Kelebihan:**
- ✅ Free tier untuk Python apps
- ✅ Khusus Python (optimized)
- ✅ Web interface untuk manage files
- ✅ Scheduled tasks support
- ✅ MySQL/PostgreSQL free

**⚠️ Keterbatasan:**
- Free tier: 1 web app
- Custom domain (paid)
- Static files perlu konfigurasi manual

---

### 💼 **4. VPS (DigitalOcean/Linode/Vultr) + Gunicorn + Nginx**
**✅ Kelebihan:**
- ✅ Full control
- ✅ Murah ($5-10/bulan)
- ✅ Production-ready
- ✅ Scalable

**⚠️ Perlu:**
- Server management knowledge
- Setup Gunicorn, Nginx
- SSL setup (Let's Encrypt)
- Backup management

**Recommended Stack:**
- Gunicorn (WSGI server)
- Nginx (Reverse proxy)
- Supervisor (Process manager)
- PostgreSQL (Replace SQLite)

---

## 📦 **Preparasi Project untuk Deployment**

### **1. Update requirements.txt**
Pastikan semua dependencies ada:
```txt
Flask==2.3.3
gunicorn==21.2.0
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
lightgbm==4.0.0
xgboost==1.7.6
plotly==5.15.0
flask-sqlalchemy==3.0.5
flask-login==0.6.3
bcrypt==4.1.2
# ... lainnya
```

### **2. Update app.py untuk Production**
```python
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
```

### **3. Update config.py untuk Production**
```python
import os

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    
    # Database - Gunakan PostgreSQL untuk production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///data/prisma.db'
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

### **4. Create Procfile (untuk Heroku/Render)**
```txt
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
```

### **5. Create runtime.txt (optional)**
```txt
python-3.11.5
```

### **6. Update .gitignore**
Pastikan file sensitif tidak ter-commit:
```gitignore
.env
*.db
data/prisma.db
data/models/*.pkl
.env.local
```

---

## 🔧 **Environment Variables**

Set di platform deployment:
```bash
FLASK_ENV=production
SECRET_KEY=<random-secure-key>
DATABASE_URL=<postgresql-url-jika-upgrade>
PORT=5001  # Auto-set oleh platform
```

---

## 📝 **Deployment Checklist**

### **Pre-Deployment:**
- [ ] Update `requirements.txt` dengan semua dependencies
- [ ] Test aplikasi di local
- [ ] Update `config.py` untuk production settings
- [ ] Set environment variables
- [ ] Update database path (jika perlu)
- [ ] Test static files loading
- [ ] Check file upload permissions
- [ ] Update `app.py` untuk production port

### **Database Migration (SQLite → PostgreSQL):**
- [ ] Install PostgreSQL adapter: `psycopg2-binary`
- [ ] Update `DATABASE_URL` di config
- [ ] Run migration script (jika ada)
- [ ] Test database connections

### **Post-Deployment:**
- [ ] Test semua routes
- [ ] Test file upload
- [ ] Test login functionality
- [ ] Check logs untuk errors
- [ ] Monitor performance
- [ ] Setup backup (jika perlu)

---

## 🎯 **Rekomendasi Final**

**Untuk Quick Start:**
→ **Render.com** (paling mudah, free tier, auto-deploy)

**Untuk Production Serius:**
→ **VPS + Gunicorn + Nginx** (full control, scalable, cost-effective)

**Untuk Development/Testing:**
→ **PythonAnywhere** (free tier, mudah untuk testing)

---

## 📚 **Resources**

- [Render.com Docs](https://render.com/docs)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [Flask Production](https://flask.palletsprojects.com/en/2.3.x/deploying/)

---

## ⚠️ **Catatan Penting**

1. **SQLite di Production:**
   - SQLite tidak recommended untuk production
   - Upgrade ke PostgreSQL untuk concurrent access
   
2. **File Storage:**
   - Upload files perlu persistent storage
   - Gunakan cloud storage (S3, etc) atau volume di VPS

3. **ML Models:**
   - Model files (*.pkl) perlu disimpan
   - Pastikan ada di repository atau storage terpisah

4. **Security:**
   - Set strong `SECRET_KEY`
   - Enable HTTPS (SSL)
   - Update dependencies secara berkala

