#!/usr/bin/env python3
"""
Script untuk migrasi data CSV ke database SQLite
Mengkonversi data dari IPH-Kota-Batu.csv ke format database yang baru
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from database import db, IPHData, CommodityData, AdminUser, AlertRule
from werkzeug.security import generate_password_hash
import os

def parse_commodity_impact(impact_string):
    """Parse string komoditas andil menjadi dictionary"""
    if pd.isna(impact_string) or impact_string == '':
        return {}
    
    # Clean the string
    impact_string = str(impact_string).strip()
    
    # Split by semicolon
    commodities = impact_string.split(';')
    result = {}
    
    for commodity in commodities:
        commodity = commodity.strip()
        if '(' in commodity and ')' in commodity:
            # Extract commodity name and value
            match = re.match(r'([^(]+)\(([^)]+)\)', commodity)
            if match:
                name = match.group(1).strip()
                value_str = match.group(2).strip().replace(',', '.')
                try:
                    value = float(value_str)
                    result[name] = value
                except ValueError:
                    continue
    
    return result

def get_week_number(minggu_str):
    """Convert minggu string (M1, M2, etc.) to number"""
    if pd.isna(minggu_str):
        return 1
    
    minggu_str = str(minggu_str).strip()
    if minggu_str.startswith('M'):
        try:
            return int(minggu_str[1:])
        except ValueError:
            return 1
    return 1

def get_month_number(bulan_str):
    """Convert bulan string to number"""
    if pd.isna(bulan_str):
        return 1
    
    bulan_str = str(bulan_str).strip().lower()
    
    # Handle year in month name
    if "'" in bulan_str:
        bulan_str = bulan_str.split("'")[0].strip()
    
    month_map = {
        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
    }
    
    return month_map.get(bulan_str, 1)

def calculate_date_from_period(bulan_str, minggu_str, tahun=None):
    """Calculate actual date from bulan and minggu"""
    if pd.isna(bulan_str) or bulan_str == '':
        return None
    
    bulan_num = get_month_number(bulan_str)
    minggu_num = get_week_number(minggu_str)
    
    # Default to current year if not specified
    if tahun is None:
        tahun = datetime.now().year
    
    # Calculate approximate date (first week of month + (minggu-1) * 7 days)
    try:
        # First day of the month
        first_day = datetime(tahun, bulan_num, 1)
        
        # Calculate week start (Monday)
        days_since_monday = first_day.weekday()
        week_start = first_day - timedelta(days=days_since_monday)
        
        # Add weeks
        target_date = week_start + timedelta(weeks=minggu_num-1, days=6)  # End of week
        
        return target_date.date()
    except ValueError:
        return None

def migrate_csv_to_database(csv_file_path='data/IPH-Kota-Batu.csv', clear_existing=True):
    """Migrate CSV data to database"""
    print("🚀 Starting CSV to Database migration...")
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file_path)
        print(f"📊 Loaded {len(df)} records from CSV")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Normalize and clean data
    # Forward-fill Bulan so baris dengan Bulan kosong tetap terisi (CSV menggunakan blank untuk baris bulan yang sama)
    if 'Bulan' in df.columns:
        df['Bulan'] = df['Bulan'].ffill()
    # Pastikan kolom minggu ada
    if 'Minggu ke-' not in df.columns:
        raise ValueError("Kolom 'Minggu ke-' tidak ditemukan di CSV")

    # Hanya drop baris yang tidak punya nilai IPH atau minggu
    df = df.dropna(subset=['Minggu ke-', ' Indikator Perubahan Harga (%)'])
    # Buang baris bulan kosong setelah ffill (jika masih ada string kosong)
    df = df[df['Bulan'].astype(str).str.strip() != '']
    
    print(f"📋 Cleaned data: {len(df)} records")
    
    # Initialize Flask app context
    from app import app
    with app.app_context():
        # Initialize database (db sudah terdaftar pada app, cukup create_all)
        db.create_all()
        print("✅ Database tables created")
        
        try:
            # Clear existing data if requested (untuk memastikan tanggal lama yang salah dibersihkan)
            if clear_existing:
                CommodityData.query.delete()
                IPHData.query.delete()
                db.session.commit()
            
            migrated_iph = 0
            migrated_commodity = 0
            
            for index, row in df.iterrows():
                try:
                    # Parse data
                    bulan = str(row['Bulan']).strip()
                    minggu = str(row['Minggu ke-']).strip()
                    iph_value = float(row[' Indikator Perubahan Harga (%)'])
                    kab_kota = str(row.get('Kab/Kota', 'BATU')).strip()
                    
                    # Extract year from bulan if present (harus dilakukan SEBELUM hitung tanggal)
                    tahun = None
                    if "'" in bulan:
                        try:
                            tahun_part = int(bulan.split("'")[1])
                            tahun = 2000 + tahun_part if tahun_part < 100 else tahun_part
                            # Normalisasi bulan tanpa penanda tahun untuk penyimpanan
                            bulan_clean = bulan.split("'")[0].strip()
                        except Exception:
                            tahun = datetime.now().year
                            bulan_clean = bulan
                    else:
                        # Asumsi tahun berjalan untuk baris tanpa penanda tahun
                        tahun = datetime.now().year
                        bulan_clean = bulan
                    
                    # Calculate date menggunakan tahun yang sudah diparsing
                    tanggal = calculate_date_from_period(bulan_clean, minggu, tahun)
                    if not tanggal:
                        print(f"⚠️ Skipping row {index}: Cannot calculate date")
                        continue
                    
                    bulan_numerik = get_month_number(bulan_clean)
                    
                    # Check if record already exists - if exists, update it
                    existing = IPHData.query.filter_by(tanggal=tanggal).first()
                    if existing:
                        print(f"🔄 Updating existing record for {tanggal}...")
                        existing.indikator_harga = iph_value
                        existing.bulan = bulan_clean
                        existing.minggu = minggu
                        existing.tahun = tahun
                        existing.bulan_numerik = bulan_numerik
                        existing.kab_kota = kab_kota
                        existing.updated_at = datetime.utcnow()
                        iph_record = existing
                        migrated_iph += 1
                    else:
                        # Create new IPH record
                        iph_record = IPHData(
                            tanggal=tanggal,
                            indikator_harga=iph_value,
                            bulan=bulan_clean,
                            minggu=minggu,
                            tahun=tahun,
                            bulan_numerik=bulan_numerik,
                            kab_kota=kab_kota,
                            data_source='csv_migration'
                        )
                        db.session.add(iph_record)
                        db.session.flush()  # Get the ID
                        migrated_iph += 1
                    
                    # Create Commodity record
                    commodity_record = CommodityData(
                        tanggal=tanggal,
                        bulan=bulan_clean,
                        minggu=minggu,
                        tahun=tahun,
                        kab_kota=kab_kota,
                        iph_id=iph_record.id,
                        iph_value=iph_value,
                        komoditas_andil=str(row.get('Komoditas Andil Perubahan Harga', '')),
                        komoditas_fluktuasi=str(row.get('Komoditas Fluktuasi Harga Tertinggi', '')),
                        nilai_fluktuasi=float(row.get('Fluktuasi Harga', 0)) if pd.notna(row.get('Fluktuasi Harga', 0)) else 0.0
                    )
                    
                    db.session.add(commodity_record)
                    migrated_commodity += 1
                    
                    if (index + 1) % 20 == 0:
                        print(f"📝 Processed {index + 1} records...")
                        
                except Exception as e:
                    print(f"⚠️ Error processing row {index}: {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            print(f"✅ Migration completed!")
            print(f"   📊 IPH records: {migrated_iph}")
            print(f"   🌾 Commodity records: {migrated_commodity}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False

def create_default_admin():
    """Create default admin user"""
    from app import app
    with app.app_context():
        try:
            # Check if admin already exists
            existing_admin = AdminUser.query.filter_by(username='admin').first()
            if existing_admin:
                print("👤 Admin user already exists")
                return True
            
            # Create default admin
            admin = AdminUser(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                email='admin@prisma.local',
                is_active=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Default admin user created (username: admin, password: admin123)")
            return True
            
        except Exception as e:
            print(f"❌ Error creating admin: {e}")
            return False

def create_default_alert_rules():
    """Create default alert rules"""
    from app import app
    with app.app_context():
        try:
            # Check if rules already exist
            existing_rules = AlertRule.query.count()
            if existing_rules > 0:
                print("📋 Alert rules already exist")
                return True
            
            # Create default rules
            default_rules = [
                {
                    'rule_name': 'IPH Tinggi - 2 Sigma',
                    'rule_type': 'threshold',
                    'threshold_value': 2.0,
                    'comparison_operator': '>',
                    'severity_level': 'warning',
                    'description': 'Peringatan ketika IPH melebihi 2 standar deviasi'
                },
                {
                    'rule_name': 'IPH Kritis - 3 Sigma',
                    'rule_type': 'threshold',
                    'threshold_value': 3.0,
                    'comparison_operator': '>',
                    'severity_level': 'critical',
                    'description': 'Peringatan kritis ketika IPH melebihi 3 standar deviasi'
                },
                {
                    'rule_name': 'Volatilitas Tinggi',
                    'rule_type': 'volatility',
                    'threshold_value': 0.1,
                    'comparison_operator': '>',
                    'severity_level': 'warning',
                    'description': 'Peringatan ketika volatilitas komoditas tinggi'
                }
            ]
            
            for rule_data in default_rules:
                rule = AlertRule(
                    rule_name=rule_data['rule_name'],
                    rule_type=rule_data['rule_type'],
                    threshold_value=rule_data['threshold_value'],
                    comparison_operator=rule_data['comparison_operator'],
                    severity_level=rule_data['severity_level'],
                    description=rule_data['description'],
                    created_by='system'
                )
                db.session.add(rule)
            
            db.session.commit()
            print(f"✅ Created {len(default_rules)} default alert rules")
            return True
            
        except Exception as e:
            print(f"❌ Error creating alert rules: {e}")
            return False

if __name__ == '__main__':
    print("🔄 PRISMA Database Migration Tool")
    print("=" * 50)
    
    # Check if CSV file exists
    csv_path = 'data/IPH-Kota-Batu.csv'
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        exit(1)
    
    # Run migration
    success = migrate_csv_to_database(csv_path)
    
    if success:
        # Create default admin
        create_default_admin()
        
        # Create default alert rules
        create_default_alert_rules()
        
        print("\n🎉 Migration completed successfully!")
        print("📝 Next steps:")
        print("   1. Run the application: python app.py")
        print("   2. Login as admin (username: admin, password: admin123)")
        print("   3. Check data in dashboard")
    else:
        print("\n❌ Migration failed!")
