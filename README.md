# 🎯 PRISMA — Price Indicator Smart Monitoring & Analytics

Platform terpadu untuk memantau dan memprediksi Indikator Perubahan Harga (IPH) dengan dashboard interaktif, analitik komoditas, dan sistem peringatan. Dirancang untuk membantu pengambil keputusan melihat tren harga, menganalisis dampak komoditas, dan mengambil tindakan lebih cepat.

—

## 🔎 Gambaran Singkat

- **Forecasting IPH**: Prediksi jangka pendek berbasis historis.
- **Analitik Komoditas**: Lihat komoditas yang paling berpengaruh per minggu/bulan.
- **Dashboard Interaktif**: Visualisasi yang mudah dipahami oleh non-teknis.
- **Peringatan (Alerts)**: Deteksi dini anomali dan perubahan tren.
- **Admin Panel (opsional)**: Kelola aturan alert dan data.

Proyek ini menggunakan Python, Flask, dan database SQLite. Dapat dijalankan di laptop, server on‑prem, maupun VPS (contoh: Hostinger) menggunakan Gunicorn + Nginx.

—

## 🚀 Apa yang Bisa Anda Lakukan dengan PRISMA

- **Melihat kondisi IPH saat ini** beserta tren dan prediksinya.
- **Menelusuri komoditas kunci** yang mendorong kenaikan/penurunan IPH.
- **Menguji skenario cepat** dengan menghasilkan forecast baru dari data terbaru.
- **Menerima sinyal peringatan** ketika terjadi anomali statistik atau volatilitas tinggi.

—

## 🖥️ Tampilan Utama (Halaman Publik)

- **Dashboard**: Grafik historis + prediksi IPH, ringkasan performa model, dan panel peringatan.
- **Visualisasi**: Moving averages, volatilitas, dan perbandingan model.
- **Commodity Insights**: Analisis mingguan/bulanan, tren komoditas, pola musiman.
- **Alerts**: Riwayat peringatan dan temuan terbaru.

Catatan: Mode admin untuk kontrol data dan aturan alert tersedia sesuai kebutuhan.

—

## ⏱️ Cara Cepat Menjalankan (Lokal)

1) Siapkan lingkungan Python 3.8+ dan instal dependensi:

```bash
pip install -r requirements.txt
```

2) Buat folder yang dibutuhkan:

```bash
mkdir -p data/models data/backups data/db_backups static/uploads
```

3) Jalankan aplikasi:

```bash
python app.py
```

4) Buka di browser:

`http://localhost:5001`

—

## 📥 Data yang Dibutuhkan

- **IPH (wajib)**: Tanggal (YYYY‑MM‑DD) dan Indikator_Harga (%).
- **Komoditas (opsional)**: Data per minggu/bulan untuk analisis dampak.

Anda bisa mengunggah CSV/Excel dari halaman “Kontrol Data” atau menambahkan secara manual.

—

## 🧭 Bagaimana PRISMA Bekerja (Ringkas)

1) Data historis dibaca dari database/file.
2) Sistem melatih beberapa pendekatan prediksi dan memilih hasil terbaik.
3) Prediksi digabung dengan batas keyakinan (confidence interval) agar mudah ditafsirkan.
4) Dampak komoditas dianalisis agar terlihat siapa “kontributor utama”.
5) Peringatan dibuat jika ada pola yang menyimpang secara statistik.

Fokus kami adalah hasil yang mudah dipakai pengguna akhir, bukan detail teknis model.

—

## 🌐 Deploy Singkat (Opsional)

Untuk produksi, pola umum yang direkomendasikan:

- Jalankan aplikasi dengan **Gunicorn** (WSGI) di belakang **Nginx** sebagai reverse proxy.
- Kelola proses dengan **Supervisor** (restart otomatis, logging).
- Aktifkan **HTTPS** dengan **Certbot**.

Dokumen panduan lengkap disertakan di repo (`HOSTINGER_DEPLOYMENT.md` dan checklist terkait) bila Anda ingin menerapkan di VPS/Hostinger.

—

## 🧑‍💼 Untuk Siapa PRISMA Cocok?

- Tim analis harga komoditas dan inflasi.
- OPD/instansi yang memonitor IPH mingguan/bulanan.
- Pengambil keputusan yang membutuhkan ringkasan visual dan peringatan dini.

—

## ⚙️ Teknologi yang Digunakan (Ringkas)

- **Backend**: Python + Flask
- **Database**: SQLite (bisa diganti sesuai kebutuhan)
- **Antarmuka**: Bootstrap + Plotly
- **Server Produksi**: Gunicorn + Nginx (opsional)

—

## ❓ Tanya Jawab Singkat

- **Apakah harus paham machine learning?** Tidak. PRISMA menyajikan hasil akhir yang siap pakai.
- **Bisakah memakai database lain?** Bisa. Aplikasi memakai SQLAlchemy sehingga mudah dipindah.
- **Apakah butuh internet?** Tidak untuk penggunaan lokal. Internet diperlukan untuk deploy/SSL.

—

## 🧩 Roadmap Ringkas

- Peningkatan kontrol akses admin (proteksi halaman tertentu).
- Optimasi performa dan caching.
- Dokumentasi API publik bila dibutuhkan integrasi eksternal.

—

## 📄 Lisensi

MIT License — lihat berkas `LICENSE`.

—

Terima kasih telah menggunakan PRISMA. Kami fokus pada kejelasan insight, bukan kerumitan teknis. Jika memerlukan bantuan implementasi atau deploy, silakan hubungi maintainer proyek.
