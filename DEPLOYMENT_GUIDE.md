# 🚀 IPH Forecasting App - Deployment Guide

## 📋 Prerequisites

- [x] Vercel account (free tier OK)
- [x] GitHub account
- [x] Supabase project dengan PostgreSQL database
- [x] ONNX model files di `data/models/` folder

---

## 🔧 Pre-Deployment Checklist

### 1. Commit ONNX Models to Git

```bash
# Pastikan .onnx files ada
ls -la data/models/

# Expected output:
# KNN.onnx
# LightGBM.onnx
# Random_Forest.onnx
# XGBoost.onnx
# XGBoost_Advanced.onnx

# Commit ke Git
git add data/models/*.onnx
git commit -m "Add ONNX models for production deployment"
git push origin main
```

### 2. Verify Database Tables

Login ke Supabase Dashboard → SQL Editor, jalankan:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Expected: iph_data, commodity_data, forecast_history, model_performance

-- Check forecast_history structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'forecast_history';
```

### 3. Prepare Environment Variables

Buat file `env_template.txt` dengan values Anda:

```env
SECRET_KEY=your-super-secret-key-min-32-characters
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
FLASK_ENV=production
```

**⚠️ JANGAN commit file .env ke Git!**

---

## 🌐 Deployment Steps

### Step 1: Connect GitHub to Vercel

1. Login ke [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New Project"**
3. **Import Git Repository:**
   - Select your GitHub repository
   - Framework Preset: **Other** (Vercel will auto-detect Flask)
4. Click **"Import"**

---

### Step 2: Configure Build Settings

**Root Directory:** `./`

**Build Command:** (leave default or set to)
```bash
pip install -r requirements.txt
```

**Output Directory:** (leave empty)

**Install Command:** (leave default)

---

### Step 3: Set Environment Variables

Di Vercel Dashboard → Settings → Environment Variables, tambahkan:

| Key | Value | Environment |
|-----|-------|-------------|
| `SECRET_KEY` | (your secret key) | Production, Preview, Development |
| `DATABASE_URL` | (Supabase PostgreSQL URL) | Production, Preview, Development |
| `SUPABASE_URL` | https://xxx.supabase.co | Production, Preview, Development |
| `SUPABASE_ANON_KEY` | eyJhbGc... | Production, Preview, Development |
| `FLASK_ENV` | production | Production |

**⚠️ Important:**
- Use **Production** environment for live deployment
- Use **Preview** for testing branches
- Use **Development** for local testing (optional)

---

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for build to complete (~2-3 minutes)
3. Check build logs for errors

**Expected Build Output:**
```
✓ Installing dependencies
✓ Building application
✓ Uploading build files
✓ Deployment ready
```

---

### Step 5: Verify Deployment

**Test URLs:**

```bash
# Homepage
https://your-app.vercel.app/

# Admin login
https://your-app.vercel.app/admin/login

# API test
https://your-app.vercel.app/api/forecast-chart-data
```

**Expected Response (forecast-chart-data):**
```json
{
  "success": true,
  "data": [...],
  "model_name": "XGBoost_Advanced",
  "summary": {...}
}
```

---

## 🐛 Troubleshooting

### Issue 1: Build Failed - Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'sklearn'
```

**Solution:**
```bash
# Check requirements.txt - should NOT contain:
# scikit-learn
# xgboost
# lightgbm

# Only onnxruntime for inference
```

---

### Issue 2: Database Connection Timeout

**Error:**
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
1. Check `DATABASE_URL` di Vercel environment variables
2. Verify Supabase database is running
3. Check connection pooling settings di `config.py`

---

### Issue 3: Forecast Chart Empty

**Error:**
Chart tidak muncul, API return success tapi data kosong

**Solution:**
```bash
# Generate initial forecast via admin panel
1. Login ke https://your-app.vercel.app/admin/login
2. Go to "Forecast" page
3. Click "Generate New Forecast"

# OR run di local lalu sync database
python train_local.py
```

---

### Issue 4: Session Logout Repeatedly

**Error:**
Admin auto-logout setelah beberapa detik

**Cause:**
Session timeout logic tidak compatible dengan serverless

**Solution:**
Already fixed - session timeout di-disable di production code

---

## 📊 Post-Deployment Tasks

### 1. Create Admin Account

```bash
# Via Flask shell (local)
flask shell

>>> from database import db, Admin
>>> from werkzeug.security import generate_password_hash
>>> admin = Admin(
...     username='admin',
...     email='your-email@example.com',
...     password_hash=generate_password_hash('your-secure-password')
... )
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()

# Sync ke Supabase (auto via SQLAlchemy)
```

### 2. Upload Initial Data

1. Login ke admin panel
2. Navigate to **Data Control**
3. Upload CSV file dengan historical IPH data
4. Verify data di dashboard

### 3. Generate Initial Forecast

1. Di admin panel, go to **Forecast** page
2. Click **"Generate New Forecast"**
3. Wait ~10-30 seconds
4. Verify forecast appears di public dashboard

---

## 🔄 Update Workflow

### Updating Models (After Local Training)

```bash
# 1. Train models locally
conda activate iph-dashboard
python train_local.py

# 2. Verify new ONNX files created
ls -la data/models/*.onnx

# 3. Commit & push
git add data/models/*.onnx
git commit -m "Update models - trained on $(date +%Y-%m-%d)"
git push origin main

# 4. Vercel auto-deploys (check dashboard)
# 5. Verify new models di admin panel → Model Performance
```

### Updating Code

```bash
# 1. Make changes locally
# 2. Test locally
python app.py

# 3. Commit & push
git add .
git commit -m "Your commit message"
git push origin main

# 4. Vercel auto-deploys
# 5. Check Vercel dashboard for deployment status
```

---

## 📈 Monitoring & Maintenance

### Check Vercel Logs

```bash
# Via Vercel Dashboard
Deployments → [Your deployment] → View Function Logs

# Via Vercel CLI
npm i -g vercel
vercel logs your-app.vercel.app
```

### Database Maintenance

```sql
-- Check forecast history size
SELECT COUNT(*) FROM forecast_history;

-- Delete old forecasts (keep last 100)
DELETE FROM forecast_history 
WHERE id NOT IN (
  SELECT id FROM forecast_history 
  ORDER BY created_at DESC 
  LIMIT 100
);

-- Vacuum database
VACUUM ANALYZE;
```

### Performance Monitoring

- Vercel Analytics (free tier: 100k requests/month)
- Supabase Dashboard → Database → Performance
- Check API response times di browser DevTools

---

## 🎯 Production Checklist

- [x] ONNX models committed to Git
- [x] Environment variables set di Vercel
- [x] Database tables created di Supabase
- [x] Admin account created
- [x] Initial data uploaded
- [x] Initial forecast generated
- [x] All pages accessible (dashboard, admin, API)
- [x] No file write operations di production code
- [x] Session management working (basic login/logout)
- [x] Export functions working (CSV download)

---

## 📞 Support

**Issues?**
- Check Vercel deployment logs
- Check Supabase database logs
- Review this guide's troubleshooting section

**Contact:**
- GitHub Issues: [your-repo]/issues
- Email: your-email@example.com

---

**Last Updated:** 2024-11-15  
**Version:** 1.0.0