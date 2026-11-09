# Plan Implementasi: Dual-Portal UI/UX RAG3321 (Public Chatbot & Admin Command Center)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun antarmuka web modern berbasis Vue 3 (Vite + Tailwind CSS Light Mode) dan FastAPI dengan arsitektur terpisah (*Dual-Portal*): Portal Publik untuk Asisten Chatbot Sahabat Data BPS (tanpa login, mobile-friendly) dan Portal Internal untuk Admin/Monitoring (kontrol scraping, explorer data PostgreSQL, telemetri vektor, live logs, dan kesiapan integrasi SSO BPS).

**Architecture:** Frontend Single Page Application (SPA) berbasis Vue 3 Composition API dengan dua layout terisolasi: `PublicLayout` pada rute publik (`/` dan `/chat`) dan `AdminLayout` dengan navigation guard pada rute internal (`/admin/*`), terhubung ke backend FastAPI modular yang mengeksekusi background tasks untuk scraping dan telemetri langsung ke PostgreSQL `10.133.21.24:5433`.

**Tech Stack:** 
- Frontend: Vue 3.5, Vite 8, Vue Router 4, Tailwind CSS 3.4 (Strict Light Mode Palette), `@lucide/vue`
- Backend: FastAPI, Pydantic v2, Uvicorn, BackgroundTasks
- Database: PostgreSQL 16 (`10.133.21.24:5433`, DB: `bps_rag3321`, pgvector 0.8.1)
- AI Model: Google Gemini API (`gemini-3.5-flash` / `gemini-3.1-flash-lite`)

**Spec:** Dokumen Arsitektur RAG3321 & Kebijakan Metadata Statistik BPS Kabupaten Demak (`docs/RAG3321_ENGINEERING_AUDIT_AND_IMPLEMENTATION_PLAN.md`).

## Global Constraints

- **Strict Light Mode:** Seluruh komponen UI menggunakan tema terang profesional BPS (`bg-slate-50`, `bg-white`, `border-slate-200`, `text-slate-900`, `text-slate-600`), BPS Blue (`#004B87`), Deep Navy (`#002B49`), dan BPS Orange (`#F26522`). Tidak ada dark mode pekat.
- **Decoupled URL & SSO Ready:** Portal Publik di rute root `/` dapat diakses langsung oleh masyarakat tanpa otentikasi. Portal Admin di rute `/admin/*` dilengkapi modul middleware / auth guard yang siap dihubungkan ke SSO (Single Sign-On BPS).
- **Integritas Database:** Dilarang melakukan drop, truncate, atau modifikasi destruktif pada database PostgreSQL `bps_rag3321`.
- **Non-blocking Operations:** Proses scraping tidak boleh membekukan request HTTP (wajib menggunakan background task asynchronous dengan tracking state).

## Review Focus

1. **Public Chat Isolation:** Akses ke `/` tidak boleh memicu request ke endpoint admin atau membocorkan telemetri internal server.
2. **SSO / Auth Guard Readiness:** Rute `/admin/*` harus memverifikasi token/status login (dengan fallback mock login mode sebelum SSO production terpasang).
3. **Scraper Progress Tracking:** Pemicuan scraping dari browser harus mengembalikan Job ID dan polling status tanpa timeout HTTP browser.
4. **Data Explorer Proof of Data:** Inspeksi sel tabel harus membedakan tanda `-` sebagai status `NIL` dan bukan nilai integer `0`.
5. **CORS & Proxy Stability:** Frontend dev server Vite (`localhost:5173`) dan preview build harus berkomunikasi mulus dengan API FastAPI (`localhost:8000`).

---

## 📐 Arsitektur Rute & Pemisahan Portal

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🌐 RAG3321 DUAL-PORTAL ARCHITECTURE (Vue 3 + Tailwind CSS Light Mode)                      │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. PORTAL PUBLIK (Akses Terbuka untuk Umum / Masyarakat)                                   │
│    URL: http://localhost:5173/ atau /chat                                                  │
│    Layout: PublicLayout.vue (Header ringkas BPS, tanpa sidebar admin, fokus percakapan)    │
│    - Chatbot interaktif cerdas "Sahabat Data BPS Demak"                                    │
│    - Filter wilayah 14 kecamatan & tahun rujukan                                           │
│    - Accordion sitasi resmi tabel BPS & ekspor ringkasan dialog                            │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. PORTAL INTERNAL ADMIN & MONITORING (Siap SSO BPS)                                       │
│    URL: http://localhost:5173/admin/*                                                      │
│    Layout: AdminLayout.vue (Sidebar navigasi, telemetri live pills, header profil SSO)      │
│    - /admin/login       : Login / SSO Connector Mock & Redirect Handler                     │
│    - /admin/ingestion   : Ingestion & Scraper Hub (Run scraper on-demand, live progress)   │
│    - /admin/data        : Publication & Data Explorer (Tabel granular, Proof of Data)      │
│    - /admin/vector      : Vector & Knowledge Observability (HNSW status, test search RRF)  │
│    - /admin/logs        : Realtime System Logs & Health Telemetry                          │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Decomposition

### Task 1: Backend Modular Routers & SSO Auth Scaffold (`api/`)

**Files:**
- Create: `api/__init__.py`
- Create: `api/routers/__init__.py`
- Create: `api/routers/auth.py`
- Create: `api/routers/ingestion.py`
- Create: `api/routers/data_viewer.py`
- Create: `api/routers/system_telemetry.py`
- Modify: `chatbot/api.py` (mount sub-routers dan middleware CORS)
- Test: `tests/test_backend_api_routers.py`

- [ ] **Step 1.1: Write failing test for new API endpoints**
  Buat `tests/test_backend_api_routers.py` yang menguji endpoint `/api/auth/verify`, `/api/ingestion/status`, `/api/data/publications`, dan `/api/system/health`.
- [ ] **Step 1.2: Run test to confirm failure**
  Jalankan `pytest tests/test_backend_api_routers.py` dan pastikan gagal karena router belum dibuat.
- [ ] **Step 1.3: Implement `api/routers/auth.py` with SIPETRA SSO (OAuth2)**
  Implementasikan protokol OAuth2 SIPETRA BPS Demak (`https://bpsdemak.com`) sesuai `SSO_GUIDE.md`:
  - `GET /api/auth/sipetra/redirect`: Mengarahkan browser ke `https://bpsdemak.com/oauth/authorize` dengan scopes `identity_pegawai:read employee:read contact:read roles:read`.
  - `GET /api/auth/sipetra/callback`: Menerima authorization `code`, menukarnya dengan access token di `https://bpsdemak.com/oauth/token`, mengambil profil pegawai dari `https://bpsdemak.com/api/user` (NIP, nama, email, jabatan, avatar), menerbitkan JWT session, dan me-redirect ke `http://localhost:5173/admin?token=...`.
  - `GET /api/auth/me`: Mengembalikan data user terautentikasi atau status guest.
  - `POST /api/auth/logout`: Menghapus sesi otentikasi admin.
  - Sediakan fallback Mock Login Mode jika kredensial `SIPETRA_CLIENT_ID` belum diisi di `.env`.
- [ ] **Step 1.4: Implement `api/routers/ingestion.py` & Ingestion Job Tracker**
  Sediakan endpoint `POST /api/ingestion/run` (mode `statis`, `all`, `pdf`), `GET /api/ingestion/status`, dan `POST /api/ingestion/stop` menggunakan thread non-blocking.
- [ ] **Step 1.5: Implement `api/routers/data_viewer.py`**
  Sediakan endpoint `GET /api/data/publications`, `GET /api/data/tables`, dan `GET /api/data/table/{id}` yang membaca langsung dari tabel PostgreSQL `publications` dan `statistical_tables`.
- [ ] **Step 1.6: Implement `api/routers/system_telemetry.py`**
  Sediakan endpoint `GET /api/system/health`, `GET /api/system/vector-stats`, `POST /api/system/test-search`, dan `GET /api/system/logs`.
- [ ] **Step 1.7: Mount routers in `chatbot/api.py`**
  Daftarkan seluruh router di `chatbot/api.py` dengan prefix `/api` dan CORS whitelist untuk frontend Vite.
- [ ] **Step 1.8: Run tests and ensure all pass**
  Jalankan `pytest tests/test_backend_api_routers.py` hingga 100% lulus.

---

### Task 2: Scaffolding Frontend Modern (Vue 3 + Vite + Tailwind CSS Light Mode)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/style.css`
- Create: `frontend/src/router.js`
- Create: `frontend/src/lib/api.js`
- Test: Build verification (`npm run build` di folder `frontend`)

- [ ] **Step 2.1: Create `frontend/package.json`**
  Konfigurasikan dependensi frontend: Vue 3.5, Vue Router 4, Tailwind CSS 3.4, `@lucide/vue`, `lucide-vue-next`, `clsx`, `tailwind-merge`.
- [ ] **Step 2.2: Configure `frontend/vite.config.js`**
  Pasang `@vitejs/plugin-vue` dan konfigurasi reverse proxy API: `/api` diarahkan ke `http://127.0.0.1:8000`.
- [ ] **Step 2.3: Configure `frontend/tailwind.config.js` for Strict Light Mode**
  Definisikan warna tema resmi BPS:
  ```javascript
  colors: {
    bps: {
      navy: '#002B49',
      blue: '#004B87',
      sky: '#0284C7',
      orange: '#F26522',
      amber: '#FF9E1B',
      slate: '#F8FAFC',
    }
  }
  ```
- [ ] **Step 2.4: Install dependencies**
  Jalankan `npm install` di dalam direktori `frontend/`.
- [ ] **Step 2.5: Implement `frontend/src/router.js` with Navigation Guards**
  Definisikan rute publik (`/`, `/chat`) dan rute admin (`/admin`, `/admin/ingestion`, `/admin/data`, `/admin/vector`, `/admin/logs`, `/admin/login`) dengan guard `meta.requiresAuth`.
- [ ] **Step 2.6: Implement `frontend/src/lib/api.js`**
  Buat client fetch/axios terpadu dengan penyertaan token otentikasi otomatis jika mengakses endpoint `/api/admin/*`.

---

### Task 3: Portal Publik "Sahabat Data BPS Demak" (`views/public/`)

**Files:**
- Create: `frontend/src/layouts/PublicLayout.vue`
- Create: `frontend/src/views/public/PublicChatView.vue`
- Create: `frontend/src/components/chat/ChatMessage.vue`
- Create: `frontend/src/components/chat/CitationModal.vue`
- Create: `frontend/src/components/chat/QuickPrompts.vue`
- Test: Verifikasi interaksi chat publik via Vite preview

- [ ] **Step 3.1: Implement `PublicLayout.vue`**
  Header bersih khas portal instansi pemerintah dengan lambang BPS, judul *"Sahabat Data BPS Kabupaten Demak"*, tombol tautan cepat ke portal resmi, dan navigasi minimalis tanpa sidebar admin.
- [ ] **Step 3.2: Implement `PublicChatView.vue`**
  Area percakapan elegan dengan layout terpusat (*max-w-4xl*), balon pesan user dan assistant yang kontras dan bersih, status *typing indicator*, dan penanganan error yang ramah.
- [ ] **Step 3.3: Implement `CitationModal.vue` / Citation Drawer**
  Komponen untuk menampilkan detail dokumen sumber publikasi BPS, nomor halaman, dan judul tabel saat pengguna mengklik kartu sitasi rujukan.
- [ ] **Step 3.4: Implement `QuickPrompts.vue`**
  Tombol-tombol pertanyaan cepat populer (Jumlah Penduduk 2024, Pertumbuhan Padi, Capaian IPM, Profil Kepala BPS).

---

### Task 4: Portal Admin — Data Ingestion & Scraper Hub (`views/admin/`)

**Files:**
- Create: `frontend/src/layouts/AdminLayout.vue`
- Create: `frontend/src/views/admin/AdminLoginView.vue`
- Create: `frontend/src/views/admin/IngestionHubView.vue`
- Create: `frontend/src/components/admin/ScraperControlCard.vue`
- Create: `frontend/src/components/admin/ScraperProgressBar.vue`
- Test: Verifikasi pemicuan job scraping dan update progress bar

- [ ] **Step 4.1: Implement `AdminLayout.vue`**
  Sidebar vertikal dengan ikon Lucide untuk navigasi (Ingestion, Data Explorer, Vector Observability, System Logs), header status koneksi PostgreSQL live pill (hijau berkedip), dan tombol logout / switch to Public Chat.
- [ ] **Step 4.2: Implement `AdminLoginView.vue`**
  Halaman login admin dengan form login sederhana dan kartu *"BPS Single Sign-On (SSO) Ready"* yang siap menerima callback URL dari SSO BPS.
- [ ] **Step 4.3: Implement `IngestionHubView.vue`**
  Command center scraper:
  - Tombol aksi: *Run Incremental (2 hal)*, *Run Deep Crawl (Semua)*, *Process Uploaded PDF*.
  - Status aktif: Badge status (IDLE / RUNNING / COMPLETED / FAILED), progress bar halaman dan tabel.
  - Kartu konsol ringkas untuk memantau output log scraper secara real-time.

---

### Task 5: Portal Admin — Data Explorer & "Proof of Data" (`views/admin/`)

**Files:**
- Create: `frontend/src/views/admin/DataExplorerView.vue`
- Create: `frontend/src/components/admin/ProofOfDataDrawer.vue`
- Create: `frontend/src/components/admin/TableDataGrid.vue`
- Test: Verifikasi data filtering per kecamatan dan inspeksi sel tabel

- [ ] **Step 5.1: Implement `DataExplorerView.vue`**
  Toolbar filter: Dropdown 14 Kecamatan Demak, Filter Tahun Publikasi, Kategori Data, dan kolom pencarian kata kunci.
- [ ] **Step 5.2: Implement `TableDataGrid.vue`**
  Data table modern (paginasi, status baris, judul tabel, jumlah record, ukuran chunk) yang mengambil data dari `GET /api/data/tables`.
- [ ] **Step 5.3: Implement `ProofOfDataDrawer.vue`**
  Drawer samping yang muncul saat admin mengklik baris tabel:
  - Menampilkan sel data mentah dalam format spreadsheet.
  - Membuktikan visualisasi status: tanda strip `-` ditampilkan sebagai badge `NIL (Tidak ada data)`, bukan angka `0`.
  - Menampilkan representasi teks alami (*natural language*) yang dikirim ke LLM.

---

### Task 6: Portal Admin — Vector Observability & System Logs (`views/admin/`)

**Files:**
- Create: `frontend/src/views/admin/VectorObservabilityView.vue`
- Create: `frontend/src/views/admin/SystemLogsView.vue`
- Test: Verifikasi live logs polling dan semantic search testing

- [ ] **Step 6.1: Implement `VectorObservabilityView.vue`**
  - KPI Cards: Total Vektor Chunks di pgvector, Total Embedding Cache di PostgreSQL, Latensi Rerata.
  - **Semantic Search Playground**: Form input untuk menguji pertanyaan secara langsung, menampilkan skor kosinus `<=>`, peringkat PostgreSQL FTS `tsvector`, dan hasil gabungan RRF Score.
- [ ] **Step 6.2: Implement `SystemLogsView.vue`**
  Viewer log real-time dengan styling light mode elegan, penanda warna level Loguru (INFO hijau, WARNING kuning, ERROR merah), tombol *Pause Stream*, *Clear*, dan *Export Logs*.

---

### Task 7: Orchestrator Runner Satu Pintu (`run_dashboard.bat`) & Dokumentasi

**Files:**
- Create: `run_dashboard.bat` (Windows 1-click launcher)
- Create: `run_dashboard.sh` (Linux / staging launcher)
- Modify: `README.md` (Update panduan dual portal & changelog)
- Test: Uji build frontend (`npm run build`) dan end-to-end launcher test

- [ ] **Step 7.1: Create `run_dashboard.bat`**
  Skrip batch otomatis yang menyalakan backend FastAPI (`chatbot/api.py`), menyalakan frontend Vite dev server, dan langsung membuka browser pada rute publik `http://localhost:5173/`.
- [ ] **Step 7.2: Create `run_dashboard.sh`**
  Skrip bash ekuivalen untuk sistem Linux / server produksi.
- [ ] **Step 7.3: Update `README.md`**
  Dokumentasikan pembagian portal publik vs admin, instruksi peluncuran satu pintu, dan update Changelog per aturan global pengguna.
- [ ] **Step 7.4: End-to-End Verification & Git Push**
  Jalankan `npm run build` di `frontend/`, jalankan `pytest tests/ -v`, pastikan seluruh tes 100% lulus, lalu commit dan push ke GitHub.

---

## 🎯 Definisi Selesai (Acceptance Criteria)
1. **Pemisahan URL Jelas:** 
   * `http://localhost:5173/` membuka Portal Publik Asisten Sahabat Data BPS (bebas diakses siapapun tanpa login).
   * `http://localhost:5173/admin/` membuka Portal Manajemen Data & Monitoring Internal (dilengkapi guard dan siap disambungkan ke SSO).
2. **Visual Light Mode:** Seluruh antarmuka mengusung tema terang (*clean light mode*), tidak ada kontras gelap yang menyulitkan pembacaan data statistik.
3. **Fungsionalitas Backend Management Lengkap:** Admin dapat memicu scraper, memantau progress bar, menginspeksi tabel hasil ekstraksi (Proof of Data), menguji pencarian vektor, dan memantau log server langsung dari browser.
