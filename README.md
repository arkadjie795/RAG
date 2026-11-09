## 🌐 Dual-Portal Architecture (Vue 3 + Tailwind Light Mode + FastAPI)

Sistem RAG3321 hadir dengan arsitektur terpisah (*Dual-Portal*) yang memenuhi kebutuhan publik umum dan manajemen internal BPS:

### 1. Peluncur Satu Pintu (1-Click Launcher):
Cukup jalankan file batch di terminal Windows:
```cmd
.\run_dashboard.bat
```
Skrip ini otomatis menyalakan backend FastAPI (port `8000`), frontend Vite (port `5173`), dan langsung membuka browser.

---

### 2. Portal Publik: "Sahabat Data BPS Demak"
* **URL:** `http://localhost:5173/` (atau `/chat`)
* **Akses:** Terbuka bebas untuk masyarakat/umum (tanpa login).
* **Fitur:** Dialog interaktif cerdas seputar data statistik Kabupaten Demak, filter 14 kecamatan & tahun rujukan, quick prompt chips, accordion sitasi resmi nomor halaman tabel BPS, dan full responsive mobile.

---

### 3. Portal Admin & Monitoring: "BPS Demak Command Center"
* **URL:** `http://localhost:5173/admin/`
* **Akses:** Khusus pegawai/admin BPS (dilengkapi SSO SIPETRA & Mock Login pengembang).
* **Fitur Modul:**
  1. **Ingestion & Scraper Hub (`/admin/ingestion`)**: Pemicu scraping katalog web BPS (mode statis, deep crawl, single PDF), live animated progress bar, dan tombol batalkan proses (*stop job*).
  2. **Data & Table Explorer (`/admin/data`)**: Penjelajah data tabel hasil ekstraksi, filter per kecamatan, dan drawer samping **"Proof of Data"** untuk memverifikasi sel mentah di database PostgreSQL (memastikan `-` berstatus `NIL` bukan `0`).
  3. **Vector Observability (`/admin/vector`)**: Telemetri jumlah vector chunks di pgvector, persistent embedding cache, dan form live playground pengujian kueri pencarian semantik (RRF).
  4. **System Logs & Telemetry (`/admin/logs`)**: Pemantau log konsol real-time dengan pewarnaan level loguru (INFO, WARNING, ERROR), tombol pause stream, dan kesehatan server.

---

### 4. Integrasi SIPETRA SSO (OAuth2 BPS Demak):
Konfigurasi file `.env` untuk menghubungkan ke portal SSO `bpsdemak.com`:
```env
SIPETRA_CLIENT_ID=isi_client_id_dari_sipetra
SIPETRA_CLIENT_SECRET=isi_client_secret_dari_sipetra
SIPETRA_REDIRECT_URI=http://localhost:8000/api/auth/sipetra/callback
SIPETRA_BASE_URL=https://bpsdemak.com
```

---

## Changelog

### 2026-11-09
- **Dual-Portal Web UI/UX & SIPETRA SSO Enterprise Ready**:
  - Pembangunan arsitektur antarmuka terpisah (*Dual-Portal*) berbasis Vue 3.5, Vite 8, Tailwind CSS 3.4 (Strict Light Mode), dan FastAPI.
  - Implementasi Portal Publik (`/` dan `/chat`): Asisten AI Sahabat Data BPS Demak yang ramah masyarakat umum, responsive mobile, tanpa login.
  - Implementasi Portal Internal Admin (`/admin/*`): Command center dengan Ingestion Hub, Data Explorer dengan drawer "Proof of Data" sel PostgreSQL, Vector Observability Playground, dan System Logs.
  - Integrasi protokol OAuth2 SIPETRA BPS Demak (`https://bpsdemak.com`) dengan endpoint `/api/auth/sipetra/redirect` & `/callback`, scopes pegawai resmi, serta mock login mode untuk pengujian lokal.
  - Penyediaan skrip peluncur 1-klik `run_dashboard.bat` (Windows) dan `run_dashboard.sh` (Linux).
- **Interactive Web GUI (Streamlit) & Laporan Edukasi Hasil Audit**:
  - Pembangunan antarmuka visual modern `app.py` berbasis Streamlit dengan visual branding BPS (Biru & Oranye), percakapan interaktif, filter 14 kecamatan Demak & tahun, indikator status arsitektur PostgreSQL pgvector, serta panel sitasi rujukan resmi.
  - Penyusunan dokumen edukatif komprehensif [`docs/LAPORAN_EDUKASI_HASIL_AUDIT_MAGANG.md`](docs/LAPORAN_EDUKASI_HASIL_AUDIT_MAGANG.md) untuk tim magang yang merinci 5 pelajaran penting (integritas data `-` vs `0`, bahaya silent failure random hash, migrasi ke pgvector enterprise, format desimal Indonesia, dan RRF hybrid search) serta 5 topik inovasi untuk diskusi pengembangan masa depan.
- **PostgreSQL 15 + pgvector (0.8.1) Migration & Technical Audit Remediation**:
  - Provisioning database baru `bps_rag3321` pada `10.133.21.24:5433` dengan ekstensi `vector` (pgvector 0.8.1).
  - Skema PostgreSQL terpadu (`modules/storage/postgres_schema.sql` dan `postgres_migrator.py`) untuk registri publikasi, tabel statistik granular (JSONB), `vector_chunks` (`embedding vector(384)` + HNSW Index + GIN FTS `tsvector`), dan tabel `embedding_cache`.
  - Refactoring integritas data statistik `table_cleaner.py` & `json_builder.py` dengan skema `StatisticalCell`: menghapus konversi destruktif `-` -> `0` (status `NIL`), melestarikan catatan revisi (`r`) dan footnote (`*`), serta memperbaiki pemformatan desimal Indonesia.
  - Peningkatan pipeline embedder (`embedder.py`): menghapus pseudo-random hash generator dan mengaktifkan persistent cache berbasis hash di PostgreSQL.
  - Modul `PostgresVectorStore` (`modules/storage/postgres_store.py`) dan `HybridRetriever` (`modules/retrieval/hybrid_search.py`) menggabungkan pgvector HNSW dan PostgreSQL Full-Text Search via Reciprocal Rank Fusion (RRF).
  - Integrasi RAG Feeder & Chatbot (`chatbot/rag_feeder.py`, `chatbot/llm_client.py`, `chatbot/bot.py`) dengan fallback model stabil dan deteksi kesopanan/salam kontekstual.
  - Implementasi Golden Benchmark Dataset (30 pertanyaan riil BPS Demak) di `tests/benchmarks/golden_dataset.json` dan automated test suite dengan 100% kelulusan (18/18 tests passed).
- **Technical Engineering Audit & Implementation Plan**:
  - Menyelesaikan audit menyeluruh (19 bab analisis independen) terhadap arsitektur RAG, integritas data statistik, performa CPU, vector store fallback, dan konfigurasi multi-provider.
  - Mengidentifikasi temuan kritis (P0): konversi simbol strip `-` ke integer `0` pada `table_cleaner.py`, degradasi senyap pseudo-random hash pada `embedder.py`, dan bottleneck $O(N)$ linear scan pada fallback SQLite.
  - Merumuskan cetak biru arsitektur target: Hybrid Retrieval (Dense + SQLite FTS5 + RRF), Deterministic Numerical Answer Engine, Controlled Parallel Processing, dan spesifikasi implementasi bertahap (Phase 1 P0, Phase 2 P1, Phase 3 P2) di dokumen [`docs/RAG3321_ENGINEERING_AUDIT_AND_IMPLEMENTATION_PLAN.md`](docs/RAG3321_ENGINEERING_AUDIT_AND_IMPLEMENTATION_PLAN.md).
