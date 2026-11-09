# Plan Implementasi: Dashboard Manajemen & UI/UX Enterprise RAG3321 (Sahabat Data BPS Demak)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

---

## 📌 Ringkasan Eksekutif & Latar Belakang

Berdasarkan hasil inspeksi langsung terhadap project **`saham`** (`D:\Coding\saham`), arsitektur yang digunakan adalah **Decoupled Modern Stack**:
* **Backend:** FastAPI terstruktur dengan APIRouter modular (`api/routers/data_hub.py`, `system_health.py`, `fundamentals.py`), BackgroundTasks untuk scraper/backfill, dan telemetri langsung ke database PostgreSQL `10.133.21.24`.
* **Frontend:** Vue 3 (Composition API) + Tailwind CSS + Lucide Icons + Vite Single Page Application yang memiliki visual elegan (*glassmorphism*, status pills hijau-merah bursa, card telemetri kuantitatif, drawer "Proof of Data", dan live log stream).

### Kondisi Saat Ini di RAG3321:
Di project **RAG3321**, modul ingestion (`main.py`, `batch_process_10_publications.py`) dan database PostgreSQL (`bps_rag3321`) saat ini **belum memiliki GUI backend management**. Semua proses jalankan crawler, cek data tabel, inspeksi vektor, dan pemantauan error masih mengandalkan CLI terminal.

Rencana ini bertujuan membangun **"BPS Demak Data Command Center & Sahabat Data Workspace"** dengan standar visual, fungsionalitas, dan kenyamanan pengguna yang setara bahkan melampaui project saham, disesuaikan dengan kebutuhan publikasi statistik resmi BPS.

---

## 🛠️ Stack & Skill yang Telah Diinstal

Skill-skill web development relevan telah disalin dari project saham ke `.agents/skills/`:
1. `fastapi`, `fastapi-python`, `fastapi-templates` (Standar arsitektur API backend)
2. `vue-best-practices`, `vue-debug-guides`, `vue-testing-best-practices` (Standar komponen Vue 3 & Composition API)
3. `systematic-web-planning`, `python-web-builder`, `developing-with-streamlit` (Perencanaan dan scaffolding frontend)

**Teknologi UI/UX Target:**
* **Frontend:** Vue 3.5 + Vite + Tailwind CSS 3.4 + `@lucide/vue` / `lucide-vue-next` (Modern SPA di direktori `frontend/`).
* **Backend API:** FastAPI (modul `api/` yang diexpose dari port `8000`).
* **Database:** PostgreSQL 16 (`10.133.21.24:5433`, DB: `bps_rag3321`) dengan pgvector 0.8.1 HNSW & JSONB granular tables.
* **Palette Brand BPS:** Deep Navy (`#002B49`), Royal Blue (`#004B87`), Vibrant BPS Orange (`#F26522`), Neutral Slate (`#F8FAFC`).

---

## 📐 Arsitektur Navigasi & Modul Tampilan (UI/UX Modules)

Dashboard terbagi menjadi 5 view utama:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🏛️ BPS DEMAK DATA COMMAND CENTER (RAG3321)            🟢 PostgreSQL (10.133.21.24) │ Gemini 3.5 │
├───────────────┬─────────────────────────────────────────────────────────────────────────────┤
│ 📊 Ingestion  │ 1. DATA INGESTION & SCRAPER HUB                                             │
│    Hub        │    - Tombol Run Scraper: Statis (2 hal), Deep Crawl, Upload PDF Lokal       │
│               │    - Live Progress Bar, Tahap Ekstraksi (OCR/Table/Vector), Task Status     │
│ 🗄️ Data       ├─────────────────────────────────────────────────────────────────────────────┤
│    Explorer   │ 2. PUBLICATION & STATISTICAL DATA EXPLORER                                  │
│               │    - Tabel Publikasi & Granular Tables: Filter Kecamatan, Tahun, Kategori   │
│ 🧠 Vector     │    - Drawer "Proof of Data": Pratinjau isi sel, raw value (- vs 0), JSONB   │
│    Observ.    ├─────────────────────────────────────────────────────────────────────────────┤
│               │ 3. VECTOR & KNOWLEDGE OBSERVABILITY                                         │
│ 🖥️ System     │    - Matriks cakupan embedding, HNSW Index health, persistent cache hit-rate│
│    Logs       │    - Vector Search Playground: Tes query langsung & bandingkan RRF score    │
│               ├─────────────────────────────────────────────────────────────────────────────┤
│ 💬 Chatbot    │ 4. REALTIME SYSTEM LOGS & MONITORING                                        │
│    Workspace  │    - Log console berwarna (Loguru), memory/CPU usage, API response latency │
│               ├─────────────────────────────────────────────────────────────────────────────┤
│               │ 5. SAHABAT DATA AI WORKSPACE                                                │
│               │    - Chatbot interaktif terintegrasi, sitasi tabel BPS, ekspor jawaban      │
└───────────────┴─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Daftar Tugas Implementasi (Step-by-Step Tasks)

### Task 1: Scaffolding API Backend Management (`api/`)
Membangun router FastAPI modular di backend untuk melayani telemetri, kontrol scraper, data viewer, dan chat.

- [ ] **Step 1.1:** Buat struktur folder `api/` dan `api/routers/` di root proyek.
- [ ] **Step 1.2:** Implementasikan `api/routers/ingestion_hub.py`:
  - `POST /api/ingestion/run` (parameter: mode `statis`, `all`, `pdf_path`, background task).
  - `GET /api/ingestion/status` (status proses scraping yang sedang berjalan, persentase progress, pesan log terakhir).
  - `POST /api/ingestion/stop` (membatalkan proses scraping yang sedang aktif).
- [ ] **Step 1.3:** Implementasikan `api/routers/data_explorer.py`:
  - `GET /api/data/publications` (daftar publikasi BPS di PostgreSQL, filter tahun/kategori, total tabel statistik).
  - `GET /api/data/tables` (daftar granular tables dengan pagination, search keyword, filter kecamatan).
  - `GET /api/data/table/{table_id}` (detail JSON granular tabel, headers, data sel, status `NIL` vs `NUMERIC`).
- [ ] **Step 1.4:** Implementasikan `api/routers/system_observability.py`:
  - `GET /api/system/health` (status koneksi PostgreSQL `10.133.21.24`, ekstensi pgvector, model AI aktif, memori host).
  - `GET /api/system/vector-stats` (total chunks, embedding cache count, perbandingan tabel ber-vektor vs belum).
  - `POST /api/system/test-retrieval` (menguji query pencarian RRF secara live dan mengembalikan top-k score).
- [ ] **Step 1.5:** Implementasikan `api/routers/logs_stream.py`:
  - `GET /api/system/logs` (membaca 100-200 baris log terakhir dari `logs/` untuk ditampilkan secara live).
- [ ] **Step 1.6:** Daftarkan seluruh router baru ke `chatbot/api.py` (atau `api/main.py`) dengan konfigurasi CORS lengkap agar dapat diakses oleh Vite frontend (`http://localhost:5173`).
- [ ] **Step 1.7:** Buat unit test pytest untuk memverifikasi endpoint API backend berjalan (HTTP 200).

---

### Task 2: Background Ingestion Job Manager (`modules/ingestion/job_manager.py`)
Membangun manajer proses asynchronous agar eksekusi scraping tidak memblokir server HTTP dan dapat dipantau real-time.

- [ ] **Step 2.1:** Buat kelas `IngestionJobManager` untuk melacak status job (`IDLE`, `RUNNING`, `COMPLETED`, `FAILED`).
- [ ] **Step 2.2:** Integrasikan logging handler kustom ke Loguru untuk meneruskan log output scraper ke memory buffer / queue telemetri.
- [ ] **Step 2.3:** Hubungkan `main.py` (`statis`, `all`, `pdf`) ke background runner job manager.
- [ ] **Step 2.4:** Tulis unit test untuk memverifikasi job submission, progress tracking, dan completion signal.

---

### Task 3: Scaffolding Frontend Modern (Vue 3 + Vite + Tailwind CSS)
Menginisiasi Single Page Application di folder `frontend/` dengan tema profesional BPS.

- [ ] **Step 3.1:** Inisiasi proyek Vite Vue 3 di folder `frontend/` menggunakan `package.json` yang kompatibel (Vue 3.5, Tailwind CSS, Lucide icons, Vue Router).
- [ ] **Step 3.2:** Konfigurasikan `tailwind.config.js` dengan palet warna resmi BPS:
  - `bps-navy`: `#002B49`
  - `bps-blue`: `#004B87`
  - `bps-orange`: `#F26522`
  - `bps-amber`: `#FF9E1B`
  - `bps-slate`: `#F8FAFC`
- [ ] **Step 3.3:** Konfigurasikan `vite.config.js` dengan proxy API otomatis ke `http://127.0.0.1:8000`.
- [ ] **Step 3.4:** Jalankan `npm install` di folder `frontend/` dan verifikasi build berjalan tanpa error.

---

### Task 4: Pembuatan Komponen & Views Utama Frontend

- [ ] **Step 4.1:** **Layout & Navigation (`App.vue`, `Sidebar.vue`, `Header.vue`)**:
  - Logo BPS Demak, status koneksi PostgreSQL live pill (hijau berkedip), status model AI (`gemini-3.5-flash`), dan tab navigasi interaktif.
- [ ] **Step 4.2:** **View 1: Ingestion & Scraper Hub (`views/IngestionHubView.vue`)**:
  - Card pemicu scraper dengan opsi mode (*Statis 2 Halaman*, *Full Crawl*, *Proses PDF Spesifik*).
  - Progress bar animasi, status tahapan aktif (*Unduh PDF -> Ekstraksi Tabel -> Sanitasi Nilai -> Embedding Vektor -> PostgreSQL Commit*).
  - Log console card untuk memantau proses scraping secara live.
- [ ] **Step 4.3:** **View 2: Publication & Data Explorer (`views/DataExplorerView.vue`)**:
  - Filter interaktif: Dropdown 14 Kecamatan Demak, Filter Tahun Publikasi, Kategori Statistik.
  - Data Grid daftar tabel statistik hasil ekstraksi lengkap dengan jumlah baris/kolom.
  - Drawer modal **"Proof of Data"** (seperti di project saham): menampilkan sel data mentah, verifikasi bahwa tanda `-` berstatus `NIL` dan bukan `0`, serta representasi kalimat alami (*natural language*).
- [ ] **Step 4.4:** **View 3: Vector & Knowledge Observability (`views/VectorObservabilityView.vue`)**:
  - Metrik kuantitatif: Total Vector Chunks, Total Cached Embeddings di PostgreSQL, Latensi Kueri Rata-rata.
  - Form Playground: Pengguna dapat mengetik kueri pencarian, dan sistem menampilkan hasil RRF (Dense Vector Score + PostgreSQL FTS Rank) beserta teks cuplikan tabel.
- [ ] **Step 4.5:** **View 4: Realtime System Logs (`views/SystemLogsView.vue`)**:
  - Console viewer dengan warna syntax loguru (INFO hijau, WARNING kuning, ERROR merah).
  - Fitur Auto-Scroll, Pause Stream, dan Filter Level Log.
- [ ] **Step 4.6:** **View 5: Sahabat Data AI Chatbot (`views/ChatWorkspaceView.vue`)**:
  - Antarmuka chat modern dengan streaming response, suggestion chips BPS, rendering tabel data responsif, dan accordion sumber sitasi resmi.

---

### Task 5: Script Orchestrator Satu Pintu (`run_dashboard.bat` & `run_dashboard.sh`)
Membuat kemudahan operasional bagi tim BPS Demak untuk menjalankan seluruh ekosistem hanya dengan satu klik / perintah.

- [ ] **Step 5.1:** Buat file `run_dashboard.bat` (untuk Windows) yang otomatis:
  1. Menjalankan backend FastAPI di background (`uvicorn chatbot.api:app --host 127.0.0.1 --port 8000`).
  2. Menjalankan frontend Vite dev server (`npm --prefix frontend run dev`).
  3. Membuka browser langsung ke `http://localhost:5173`.
- [ ] **Step 5.2:** Buat file `run_dashboard.sh` (untuk Linux / server staging).
- [ ] **Step 5.3:** Perbarui `README.md` dengan panduan penggunaan dashboard visual baru.

---

### Task 6: Verifikasi Akhir & Commit
- [ ] **Step 6.1:** Jalankan seluruh pengujian backend (`pytest tests/ -v`).
- [ ] **Step 6.2:** Jalankan `npm run build` pada folder `frontend/` untuk memastikan tidak ada syntax/type error.
- [ ] **Step 6.3:** Commit perubahan ke git dan push ke repositori GitHub sesuai aturan workflow.

---

## 🎯 Indikator Keberhasilan (Definition of Done)
1. Tim BPS dan magang dapat memicu scraping publikasi hanya dengan menekan tombol di browser dan melihat progress bar-nya bergerak.
2. Seluruh tabel statistik yang ada di PostgreSQL dapat dicari, difilter per kecamatan, dan diinspeksi selnya secara visual lewat modal "Proof of Data".
3. Log server dan status koneksi database dapat dipantau langsung tanpa harus membuka terminal hitam.
4. Desain antarmuka rapi, responsif, elegan, dan konsisten dengan identitas visual resmi Badan Pusat Statistik (BPS).
