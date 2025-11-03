"""
Script untuk menambahkan kolom reset_token dan reset_token_expiry ke tabel admin_users
"""

import sqlite3
import os
from pathlib import Path

# Path ke database
db_path = Path('data/prisma.db')

if not db_path.exists():
    print(f"ERROR: Database tidak ditemukan di {db_path}")
    exit(1)

print(f"Membuka database: {db_path}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Cek apakah kolom sudah ada
    cursor.execute("PRAGMA table_info(admin_users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    print(f"Kolom yang ada: {columns}")
    
    # Tambahkan kolom reset_token jika belum ada
    if 'reset_token' not in columns:
        print("\nMenambahkan kolom reset_token...")
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_token TEXT")
        print("✓ Kolom reset_token ditambahkan")
    else:
        print("✓ Kolom reset_token sudah ada")
    
    # Tambahkan kolom reset_token_expiry jika belum ada
    if 'reset_token_expiry' not in columns:
        print("Menambahkan kolom reset_token_expiry...")
        cursor.execute("ALTER TABLE admin_users ADD COLUMN reset_token_expiry DATETIME")
        print("✓ Kolom reset_token_expiry ditambahkan")
    else:
        print("✓ Kolom reset_token_expiry sudah ada")
    
    conn.commit()
    print("\n✅ Migration berhasil! Kolom reset_token dan reset_token_expiry telah ditambahkan.")
    
    # Verifikasi
    cursor.execute("PRAGMA table_info(admin_users)")
    columns_after = [row[1] for row in cursor.fetchall()]
    print(f"\nKolom setelah migration: {columns_after}")
    
    conn.close()
    print("\nDatabase ditutup.")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    if conn:
        conn.rollback()
        conn.close()
    exit(1)

