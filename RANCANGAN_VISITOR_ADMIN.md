# 📋 RANCANGAN SISTEM AKSES PENGUNJUNG DAN ADMIN
## PRISMA - IPH Forecasting Platform

---

## 🎯 **OVERVIEW**

Sistem akan memiliki 2 level akses:
- **👥 PENGUNJUNG (Visitor/Public)**: Read-only access untuk melihat data dan visualisasi, **PLUS akses Generate Forecast** (fitur utama yang tidak mempengaruhi model/data)
- **🔐 ADMIN**: Full access untuk semua operasi data, model, dan konfigurasi

### **💡 Catatan Penting: Generate Forecast untuk Pengunjung**
**Generate Forecast** adalah fitur utama aplikasi dan **tersedia untuk semua pengunjung** karena:
- ✅ **Tidak mempengaruhi model**: Hanya menggunakan model yang sudah ditraining
- ✅ **Tidak mempengaruhi data**: Hanya membaca data historis, tidak menulis
- ✅ **Fitur utama**: Ini adalah tujuan utama web ini - membuat peramalan IPH
- ✅ **Read-only operation**: Generate forecast = membuat prediksi, bukan mengubah sistem

---

## 🔐 **AUTENTIKASI & SESSION MANAGEMENT**

### **1. Authentication System**
```
┌─────────────────────────────────────────────────┐
│  Session-based Authentication                  │
│  - Flask-Login untuk session management        │
│  - Password hashing dengan bcrypt              │
│  - Remember me functionality                   │
│  - Session timeout (30 menit inaktif)          │
└─────────────────────────────────────────────────┘
```

**Implementasi:**
- Middleware `@login_required` untuk proteksi route admin
- Decorator `@admin_required` untuk validasi role
- Session storage: Flask session (bisa extend ke Redis untuk production)

### **2. User Roles**
```
ROLES:
├── VISITOR (default, tidak perlu login)
│   └── View-only access
│
└── ADMIN (perlu login)
    └── Full CRUD access
```

---

## 📄 **STRUKTUR Halaman DAN ROUTES**

### **🟢 HALAMAN PUBLIK (Pengunjung - Tidak Perlu Login)**

#### **1. Homepage/Dashboard Publik** (`/`)
- ✅ **Akses**: Semua pengunjung
- ✅ **Fitur**:
  - Grafik peramalan IPH (interaktif)
  - Tabel data peramalan (read-only)
  - Alert ekonomi (read-only)
  - Ringkasan perbedaan model (read-only)
  - **✅ Generate Forecast** - Fitur utama untuk membuat peramalan baru (tidak mempengaruhi model/data)
  - **HIDDEN**: Tombol "Retrain Model", "Upload Data", "Edit Data", "Delete Data"

#### **2. Visualisasi** (`/visualization`)
- ✅ **Akses**: Semua pengunjung
- ✅ **Fitur**:
  - Moving averages chart
  - Volatility analysis
  - Model performance comparison
  - **READ-ONLY**: Semua chart interaktif

#### **3. Commodity Insights** (`/commodity-insights`)
- ✅ **Akses**: Semua pengunjung
- ✅ **Fitur**:
  - Analisis komoditas current week
  - Monthly analysis
  - Trend analysis (1M, 3M, 6M, 1Y)
  - Volatility ranking
  - **READ-ONLY**: Semua analisis

#### **4. Alerts** (`/alerts`)
- ✅ **Akses**: Semua pengunjung
- ✅ **Fitur**:
  - Daftar alert aktif
  - Alert history (view-only)
  - Filter alert
  - **HIDDEN**: Tombol "Acknowledge", "Manage Rules"

---

### **🔴 HALAMAN ADMIN (Perlu Login)**

#### **1. Admin Login** (`/admin/login`)
- ✅ **Form Login**:
  - Username
  - Password
  - Remember me checkbox
- ✅ **Validasi**: Redirect ke `/admin/dashboard` setelah sukses
- ✅ **Security**: Rate limiting (max 5 attempts/15 menit)

#### **2. Admin Dashboard** (`/admin/dashboard`)
- ✅ **Akses**: Admin only
- ✅ **Fitur**:
  - **Statistik Overview**:
    - Total records IPH
    - Total alerts
    - Model performance summary
    - Recent activities log
  - **Quick Actions**:
    - Upload data baru
    - Retrain models
    - Export data
    - Manage forecast history (optional - link ke forecast management)

#### **3. Data Management** (`/admin/data-control`) ⚠️ **BERUBAH DARI `/data-control`**
- ✅ **Akses**: Admin only
- ✅ **Fitur**:
  - **Upload Data**:
    - Upload CSV/Excel massal
    - Upload commodity data
    - Template download
  - **Manual Input**:
    - Tambah record IPH manual
    - Tambah record dengan commodity data
  - **Data Management**:
    - Tabel data historis dengan pagination
    - Edit record (modal)
    - Delete record (dengan konfirmasi)
    - Search & filter
    - Export data ke CSV
  - **Data Validation**:
    - Preview data sebelum save
    - Validasi format
    - Duplicate detection

#### **4. Model Management** (`/admin/models`) 🆕 **HALAMAN BARU**
- ✅ **Akses**: Admin only
- ✅ **Fitur**:
  - **Model Training**:
    - Manual retrain semua model
    - Retrain model spesifik
    - Training parameters configuration
  - **Model Performance**:
    - Performance history per model
    - Model comparison chart
    - Model drift detection status
  - **Model Management**:
    - View trained models
    - Download model files (.pkl)
    - Delete old models
    - Model metadata

#### **5. Forecast Management** (`/admin/forecast`) 🆕 **HALAMAN BARU** (Optional)
- ✅ **Akses**: Admin only
- ✅ **Catatan**: Fitur Generate Forecast tersedia untuk semua pengunjung di dashboard utama
- ✅ **Fitur** (untuk admin advanced management):
  - **Forecast History Management**:
    - Daftar semua forecast yang pernah dibuat
    - View forecast detail
    - Compare forecasts
    - Delete forecast history
    - Export forecast dalam berbagai format
  - **Forecast Analytics**:
    - Statistik penggunaan forecast
    - Model preference analytics

#### **6. Alert Management** (`/admin/alerts`) ⚠️ **BERUBAH DARI `/alerts` untuk admin**
- ✅ **Akses**: Admin only
- ✅ **Fitur**:
  - **Alert Rules**:
    - Create/edit/delete alert rules
    - Configure thresholds
    - Set severity levels
  - **Alert History**:
    - Full history dengan pagination
    - Filter by type, severity, date
    - Acknowledge alerts
    - Add admin notes
    - Export to CSV
  - **Alert Configuration**:
    - Statistical boundaries (2σ, 3σ)
    - Volatility thresholds
    - Trend detection settings

#### **7. System Settings** (`/admin/settings`) 🆕 **HALAMAN BARU**
- ✅ **Akses**: Admin only
- ✅ **Fitur**:
  - **Model Configuration**:
    - Forecast min/max weeks
    - Auto-retrain threshold
    - Model performance threshold
  - **Data Configuration**:
    - Auto-backup settings
    - Backup retention period
    - Data validation rules
  - **Alert Configuration**:
    - Default alert rules
    - Notification settings
  - **User Management**:
    - Add/edit admin users
    - Change password
    - View login history

---

## 🔒 **API ENDPOINTS PROTECTION**

### **📖 Public APIs (No Auth Required)**
```python
GET  /api/forecast-chart-data          # Chart data untuk dashboard
POST /api/generate-forecast           # ✅ Generate forecast (public - fitur utama)
GET  /api/available-models            # List available models untuk forecast
GET  /api/dashboard/model-performance  # Model metrics (read-only)
GET  /api/economic-alerts             # Alert list (read-only)
GET  /api/visualization/*              # Semua visualization APIs
GET  /api/commodity/*                  # Commodity APIs (read-only)
GET  /api/alerts/statistical           # Statistical alerts (read-only)
GET  /api/alerts/recent                # Recent alerts (read-only)
GET  /api/data/available-periods       # Available data periods
```

### **🔐 Admin APIs (Auth Required)**
```python
# Data Management
POST   /api/admin/upload-data              # Upload data (moved dari /api/upload-data)
POST   /api/admin/add-manual-record        # Add record (moved dari /api/add-manual-record)
PUT    /api/admin/data/<id>                # Edit record 🆕
DELETE /api/admin/data/<id>                # Delete record 🆕
GET    /api/admin/data/list                # List data dengan pagination 🆕

# Model Management
POST   /api/admin/retrain-models           # Retrain (moved dari /api/retrain-models)
POST   /api/admin/retrain-model/<name>     # Retrain spesifik model 🆕
GET    /api/admin/models                    # List all models 🆕
DELETE /api/admin/models/<id>              # Delete model 🆕

# Forecast Management (Advanced - Optional)
GET    /api/admin/forecast-history         # Forecast history (all users) 🆕
DELETE /api/admin/forecast/<id>            # Delete forecast history 🆕
GET    /api/admin/forecast/analytics       # Forecast usage analytics 🆕
```

# Alert Management
GET    /api/admin/alert-rules              # Alert rules (existing)
POST   /api/admin/alert-rules              # Create rule (existing)
PUT    /api/admin/alert-rules/<id>         # Update rule (existing)
DELETE /api/admin/alert-rules/<id>         # Delete rule (existing)
GET    /api/admin/alert-history            # Full history (existing)
POST   /api/admin/alerts/<id>/acknowledge # Acknowledge alert 🆕
POST   /api/admin/alerts/<id>/notes        # Add admin notes 🆕

# Settings
GET    /api/admin/settings                # Get settings 🆕
PUT    /api/admin/settings                # Update settings 🆕
GET    /api/admin/users                   # List admin users 🆕
POST   /api/admin/users                   # Create admin user 🆕
PUT    /api/admin/users/<id>              # Update admin user 🆕
DELETE /api/admin/users/<id>              # Delete admin user 🆕
```

---

## 🎨 **UI/UX CHANGES**

### **1. Navigation Bar**

#### **Public Navigation (Pengunjung)**
```
[Logo] PRISMA
├── Dashboard
├── Visualisasi
├── Commodity Insights
├── Alerts
└── [🔐 Login] ← Link ke /admin/login
```

#### **Admin Navigation**
```
[Logo] PRISMA [ADMIN BADGE]
├── Dashboard
├── Visualisasi
├── Commodity Insights
├── Alerts
├── ──────────
├── 🛠️ Admin Panel
│   ├── Dashboard Admin
│   ├── Data Management
│   ├── Model Management
│   ├── Forecast Management
│   ├── Alert Management
│   └── Settings
└── [👤 Admin Name ▼]
    ├── Profile
    ├── Change Password
    └── Logout
```

### **2. Visual Indicators**

#### **Public Pages**
- ✅ Tidak ada tombol "Upload", "Edit", "Delete", "Retrain"
- ✅ Alert badge: "Info" (no action buttons)
- ✅ **Forecast: Button "Buat Forecast" TERSEDIA** (fitur utama - tidak mempengaruhi model/data)
- ✅ Model metrics: Hanya view, tidak ada tombol "Retrain"

#### **Admin Pages**
- ✅ Badge "ADMIN" di navigation bar
- ✅ Tombol "Quick Actions" di dashboard
- ✅ Icons berbeda untuk admin actions (🛠️, ✏️, 🗑️)
- ✅ Confirmation modals untuk destructive actions

### **3. Dashboard Differences**

#### **Public Dashboard** (`/`)
```html
✅ Forecast Chart (interaktif, bisa generate forecast baru)
✅ Economic Alerts (read-only)
✅ Model Differences (read-only)
✅ Forecast Table (read-only)
✅ Button "Buat Forecast" → ✅ TERSEDIA (fitur utama)
✅ Button "Refresh" → Refresh view
❌ Button "Retrain Model" → HIDDEN (admin only)
❌ Button "Upload Data" → HIDDEN (admin only)
```

#### **Admin Dashboard** (`/admin/dashboard`)
```html
✅ Forecast Chart (dengan semua actions)
✅ Economic Alerts (dengan acknowledge buttons)
✅ Model Differences (dengan retrain buttons)
✅ Forecast Table (dengan regenerate)
✅ Quick Stats Panel
✅ Recent Activities Log
✅ Quick Actions Panel:
   - Upload Data
   - Retrain Models
   - Manage Alerts
   - View Forecast History (optional)
```

---

## 📁 **STRUKTUR TEMPLATE BARU**

```
templates/
├── base.html                    # Base template (existing)
├── base_admin.html              # 🆕 Base template untuk admin pages
│
├── public/                      # 🆕 Folder untuk public pages
│   ├── dashboard.html          # Dashboard publik (modified dari existing)
│   ├── visualization.html      # Existing
│   ├── commodity_insights.html # Existing
│   └── alerts.html             # Existing (modified - read-only)
│
├── admin/                       # 🆕 Folder untuk admin pages
│   ├── login.html              # Admin login (existing, moved)
│   ├── dashboard.html          # Admin dashboard (new, different from public)
│   ├── data_control.html        # Data management (moved dari root)
│   ├── models.html             # 🆕 Model management
│   ├── forecast.html           # 🆕 Forecast management
│   ├── alerts_manage.html      # 🆕 Alert management (different from public)
│   └── settings.html           # 🆕 System settings
│
└── components/                 # 🆕 Reusable components
    ├── _navigation.html        # Navigation component
    ├── _admin_nav.html         # Admin navigation component
    ├── _chart_card.html        # Chart card component
    └── _data_table.html        # Data table component
```

---

## 🔧 **IMPLEMENTATION STRUCTURE**

### **1. Authentication Module** (`auth/`)
```
auth/
├── __init__.py
├── decorators.py          # @login_required, @admin_required
├── forms.py              # LoginForm, ChangePasswordForm
└── utils.py              # check_password, hash_password, etc.
```

### **2. Admin Routes** (`admin/`)
```
admin/
├── __init__.py
├── routes.py             # All admin routes
├── views/
│   ├── dashboard.py
│   ├── data_management.py
│   ├── model_management.py
│   ├── forecast_management.py
│   ├── alert_management.py
│   └── settings.py
└── forms/
    ├── data_forms.py
    ├── model_forms.py
    └── settings_forms.py
```

### **3. Modified Files**
```
app.py                    # Main routes (public + admin registration)
config.py                 # Add AUTH settings
database.py               # Existing (AdminUser model already exists)
services/
└── auth_service.py       # 🆕 Authentication service
```

---

## 📊 **DATABASE CHANGES**

### **1. AdminUser Model** (Already Exists - ✅)
```python
# Sudah ada di database.py
class AdminUser(db.Model):
    username
    password_hash
    last_login
    is_active           # 🆕 Add field
    created_at          # 🆕 Add field
```

### **2. Activity Log Model** 🆕
```python
class ActivityLog(db.Model):
    id
    user_id (FK → AdminUser)
    action_type         # 'upload', 'edit', 'delete', 'train', etc.
    entity_type         # 'data', 'model', 'alert', etc.
    entity_id
    description
    ip_address
    created_at
```

---

## 🚀 **MIGRATION PLAN**

### **Phase 1: Authentication Setup**
1. ✅ Install Flask-Login
2. ✅ Create auth module
3. ✅ Create login page
4. ✅ Implement session management

### **Phase 2: Route Protection**
1. ✅ Protect existing admin routes
2. ✅ Create public versions of pages
3. ✅ Add middleware checks

### **Phase 3: Admin Pages**
1. ✅ Create admin dashboard
2. ✅ Move data-control to admin
3. ✅ Create new admin pages (models, forecast, settings)

### **Phase 4: UI Updates**
1. ✅ Update navigation bars
2. ✅ Hide/show elements based on role
3. ✅ Add admin indicators

### **Phase 5: Testing & Refinement**
1. ✅ Test all public routes
2. ✅ Test all admin routes
3. ✅ Test security (unauthorized access)
4. ✅ Performance testing

---

## 🔐 **SECURITY CONSIDERATIONS**

### **1. Password Security**
- ✅ Minimum 8 characters
- ✅ Require uppercase, lowercase, number
- ✅ Bcrypt hashing (10 rounds)
- ✅ Password change requirement (every 90 days)

### **2. Session Security**
- ✅ Secure cookies (HTTPS in production)
- ✅ Session timeout: 30 menit inaktif
- ✅ CSRF protection (Flask-WTF)
- ✅ Rate limiting untuk login attempts

### **3. Route Protection**
- ✅ All admin routes protected with `@admin_required`
- ✅ API endpoints validate session
- ✅ Direct URL access blocked untuk non-admin
- ✅ Audit logging untuk admin actions

### **4. Data Protection**
- ✅ Input validation & sanitization
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ File upload validation
- ✅ XSS protection (template auto-escaping)

---

## 📝 **FEATURE COMPARISON TABLE**

| Fitur | Pengunjung | Admin |
|-------|-----------|-------|
| **Dashboard** |
| View Forecast Chart | ✅ | ✅ |
| View Model Performance | ✅ | ✅ |
| View Alerts | ✅ | ✅ |
| **Generate Forecast** | **✅** | **✅** |
| Retrain Models | ❌ | ✅ |
| **Data Management** |
| View Historical Data | ✅ | ✅ |
| Upload Data | ❌ | ✅ |
| Edit Data | ❌ | ✅ |
| Delete Data | ❌ | ✅ |
| Export Data | ✅ (limited) | ✅ (full) |
| **Forecast Management** |
| Generate Forecast | **✅** | **✅** |
| View Forecast History | ✅ (limited) | ✅ (full) |
| Delete Forecast History | ❌ | ✅ |
| Export Forecast | ✅ | ✅ |
| **Model Management** |
| View Models | ✅ | ✅ |
| Retrain Models | ❌ | ✅ |
| Delete Models | ❌ | ✅ |
| Configure Models | ❌ | ✅ |
| **Alert Management** |
| View Alerts | ✅ | ✅ |
| Acknowledge Alerts | ❌ | ✅ |
| Manage Alert Rules | ❌ | ✅ |
| Export Alert History | ❌ | ✅ |
| **Settings** |
| View Settings | ❌ | ✅ |
| Modify Settings | ❌ | ✅ |
| User Management | ❌ | ✅ |

---

## 🎯 **RECOMMENDATIONS**

### **✅ YANG PERLU DILAKUKAN:**

1. **Halaman Tambahan Khusus Admin:**
   - ✅ `/admin/models` - Model Management
   - ✅ `/admin/forecast` - Forecast History Management (optional - advanced)
   - ✅ `/admin/settings` - System Settings
   - ✅ `/admin/dashboard` - Admin Dashboard (terpisah dari public)

2. **Kontrol Data Khusus Admin:**
   - ✅ Pindahkan `/data-control` → `/admin/data-control`
   - ✅ Tambahkan fitur Edit & Delete data
   - ✅ Tambahkan preview & validation sebelum save

3. **Public Pages:**
   - ✅ Semua halaman utama tetap accessible
   - ✅ **Generate Forecast** tersedia untuk semua pengunjung (fitur utama)
   - ✅ Hide tombol aksi yang mempengaruhi data/model (upload, edit, delete, retrain)
   - ✅ Alert hanya view, tidak ada acknowledge

4. **Authentication:**
   - ✅ Implement Flask-Login
   - ✅ Session management
   - ✅ Middleware protection

### **⚠️ PERTIMBANGAN:**

1. **Backward Compatibility:**
   - Existing URLs tetap bisa diakses (redirect ke admin jika perlu login)
   - Atau buat versi public terpisah dengan URL berbeda

2. **URL Structure Options:**

   **Option A: Route Prefix (Recommended)**
   ```
   /                    → Public dashboard
   /admin/*             → All admin pages
   /api/public/*        → Public APIs
   /api/admin/*         → Admin APIs
   ```

   **Option B: Subdomain**
   ```
   app.domain.com       → Public
   admin.domain.com     → Admin (untuk production)
   ```

3. **Data Export:**
   - Pengunjung bisa export forecast chart (PNG/PDF)
   - Admin bisa export semua data (CSV, JSON, Excel)

---

## 📋 **CHECKLIST IMPLEMENTASI**

### **Backend**
- [ ] Install Flask-Login, Flask-WTF, bcrypt
- [ ] Create auth module (`auth/`)
- [ ] Create decorators (`@login_required`, `@admin_required`)
- [ ] Create login/logout routes
- [ ] Protect admin routes
- [ ] Create admin service layer
- [ ] Add activity logging
- [ ] Add rate limiting

### **Frontend**
- [ ] Create base_admin.html template
- [ ] Create admin navigation component
- [ ] Update public pages (hide admin actions)
- [ ] Create admin dashboard
- [ ] Create admin data management page
- [ ] Create admin model management page
- [ ] Create admin forecast management page
- [ ] Create admin settings page
- [ ] Add role-based UI components

### **Database**
- [ ] Update AdminUser model (is_active, created_at)
- [ ] Create ActivityLog model
- [ ] Add database indexes
- [ ] Create migration script

### **Testing**
- [ ] Test public routes (no auth)
- [ ] Test admin routes (with auth)
- [ ] Test unauthorized access attempts
- [ ] Test session timeout
- [ ] Test password security
- [ ] Test CSRF protection

---

## 📚 **TECHNICAL STACK ADDITIONS**

### **New Dependencies**
```
Flask-Login==0.6.3          # Session management
Flask-WTF==1.2.1            # CSRF protection & forms
WTForms==3.1.1              # Form handling
bcrypt==4.1.2                # Password hashing
Flask-Limiter==3.5.0         # Rate limiting (optional)
```

---

**📅 Estimasi Waktu Implementasi: 3-5 hari**

**🎯 Prioritas:**
1. **High**: Authentication + Route Protection
2. **High**: Admin Data Management
3. **Medium**: Admin Model Management
4. **Medium**: Admin Dashboard
5. **Low**: System Settings

---

*Dokumen ini adalah rancangan awal. Dapat disesuaikan berdasarkan kebutuhan dan feedback.*

