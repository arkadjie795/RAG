# Phase 14a — Panduan Operasional Pengguna (User Guide)

## 1. Pendahuluan

Selamat datang di Panduan Operasional Sistem **Sahabat Data BPS Demak** (`RAG3321`). Sistem ini dirancang untuk mempermudah masyarakat, peneliti, dan staf BPS dalam menelusuri data statistik resmi Kabupaten Demak menggunakan bahasa alami melalui kecerdasan buatan (AI) yang berbasis fakta publikasi BPS.

Sistem menyediakan dua portal utama:
1. **Portal Publik (`/`)**: Antarmuka percakapan interaktif untuk masyarakat umum.
2. **BPS Demak Command Center (`/admin`)**: Panel kontrol dan observabilitas data bagi staf/operator data BPS.

---

## 2. Panduan Penggunaan Portal Publik (Chatbot Konsultasi Data)

### A. Membuka Portal
1. Buka peramban (browser) dan akses alamat sistem (misal: `http://localhost:8000/` atau IP server internal).
2. Anda akan disambut oleh antarmuka modern bertema BPS dengan bilah riwayat di samping kiri dan jendela obrolan di tengah.

### B. Cara Mengajukan Pertanyaan Statistik
Untuk memperoleh data yang paling akurat, ikuti tips berikut:
- **Sebutkan Topik, Wilayah, dan Tahun Secara Spesifik**:
  - *Contoh Efektif*: *"Berapa jumlah penduduk di Kecamatan Bonang pada tahun 2024?"*
  - *Contoh Efektif*: *"Tampilkan data luas panen padi di Kabupaten Demak tahun 2023."*
  - *Kurang Efektif*: *"Data beras."* (Terlalu umum, sistem akan meminta klarifikasi).
- **Verifikasi Rujukan Tabel (Sitasi)**:
  - Setiap jawaban yang valid akan menyertakan sitasi sumber di bagian bawah jawaban dalam tanda kurung siku, contoh: `[Kecamatan Bonang Dalam Angka 2024, Tabel 3.1, Hal. 45]`.
- **Memahami Simbol Khusus BPS**:
  - Jika sistem menjawab data bernilai `-` atau `Nihil`, artinya pada tabel resmi BPS kegiatan statistik tersebut memang tidak ada/nol.
  - Jika sistem menjawab `...`, artinya data belum tersedia saat publikasi dicetak.

---

## 3. Panduan Penggunaan Admin Command Center (`/admin`)

Untuk mengakses panel ini, buka `http://localhost:8000/admin` pada peramban.

### A. Data Ingestion & Scraper Hub (`/admin/ingestion`)
Menu ini digunakan oleh staf data untuk memperbarui dan mengindeks publikasi statistik baru:
1. **Mode 1: Mode Inkremental (Web API BPS)**
   - Fungsi: Menghubungi Web API resmi BPS (domain 3321) untuk memeriksa publikasi terbitan terbaru yang belum pernah di-ingest.
   - Cara Pakai: Klik tombol **Jalankan Mode Inkremental**. Pantau log konsol real-time di bagian bawah.
2. **Mode 2: Mode Deep Ingest**
   - Fungsi: Melakukan sinkronisasi riwayat publikasi jangka panjang (hingga 10 halaman arsip katalog Web API).
3. **Mode 3: Uji Single Dokumen**
   - Fungsi: Memproses 1 file PDF publikasi lokal secara instan untuk verifikasi cepat tanpa menunggu unduhan katalog.

### B. Publication & Data Explorer (`/admin/data`)
Menu ini menyajikan tabel-tabel data statistik yang berhasil diekstrak ke dalam PostgreSQL:
1. **Filter Data**:
   - Ketik kata kunci pada kotak pencarian (contoh: "Penduduk", "Padi", "IPM").
   - Pilih dropdown **Kecamatan** (tersedia seluruh 14 kecamatan di Demak).
   - Pilih **Tahun Rujukan** atau **Kategori Sektor**.
2. **Inspeksi Tabel**:
   - Klik baris tabel untuk melihat struktur kolom, satuan data, dan sampel baris statistik asli yang tersimpan.

### C. Vector & Knowledge Observability (`/admin/vector`)
Menu ini digunakan untuk memeriksa kesehatan basis data vektor:
- Memantau jumlah total vektor chunk yang aktif di indeks HNSW PostgreSQL.
- Memantau efisiensi *embedding cache* (MD5 deduplication).
- **Semantic Playground**: Uji langsung pencarian kemiripan vektor dan FTS untuk kueri tertentu tanpa melalui LLM.

### D. System Logs & Telemetry (`/admin/logs`)
- Memantau log backend secara langsung (*real-time log stream*).
- Mengetahui status kesehatan koneksi database PostgreSQL dan validitas kunci API model kecerdasan buatan.
