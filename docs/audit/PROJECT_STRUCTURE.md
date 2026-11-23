# 📁 PHASE 0: PROJECT DISCOVERY & STRUCTURE MAPPING
## Project: BPS Demak RAG Knowledge Base & AI Chatbot ("Sahabat Data BPS" / RAG3321)
**Auditor:** Multi-Disciplinary Forensic Engineering Team  
**Audit Date:** 2026-11-13  
**Classification:** Deep File, Directory, and Artifact Topology Review  

---

### 1. Root Directory & Core Topology

Direktori utama proyek berada pada:  
`c:\Users\arkadjie\Documents\Documents\MAGANG BOSSS\IT\RAG\`

Struktur direktori level atas dikelompokkan ke dalam 8 layer fungsional:

```
RAG/
├── api/                   [Backend API Routers]: Modul REST controller modular FastAPI
├── chatbot/               [AI & RAG Engine]: Core chatbot, prompt engineering, LLM gateway, memory
├── config/                [Configuration Layer]: Pydantic settings & PostgreSQL connection management
├── database/              [Data Persistence Tier]: File JSON granular, SQLite registry, ChromaDB (legacy)
├── data_publikasi/        [Raw PDF Repository]: Arsip berkas PDF publikasi resmi BPS Demak
├── frontend/              [Dual-Portal UI/UX]: Vue 3 + Vite + Tailwind CSS Single Page Application
├── modules/               [Core ETL & RAG Pipeline]: Ingestion, extraction, structuring, storage, vectorization, retrieval
├── tests/                 [Testing & Benchmarking Suite]: Pytest unit tests, integration tests, golden dataset
├── docs/ & doc/           [Documentation & Reports]: Dokumen arsitektur, laporan magang, spesifikasi teknis
└── logs/                  [Operational Telemetry]: File log harian Loguru
```

---

### 2. Pemetaan Detail Struktur File per Komponen

#### 2.1 Backend API Layer (`api/`)
* [api/routers/auth.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/api/routers/auth.py): Controller autentikasi SIPETRA SSO (OAuth2) BPS Demak dan mock-login lokal.
* [api/routers/data_viewer.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/api/routers/data_viewer.py): Endpoint penjelajah data publikasi dan tabel statistik granular dengan pagination dan filter dinamis.
* [api/routers/ingestion.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/api/routers/ingestion.py): State machine non-blocking dan controller trigger job scraper/ingestion dengan background worker dan streaming log.
* [api/routers/system_telemetry.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/api/routers/system_telemetry.py): Health check endpoint, observabilitas pgvector HNSW, embedding cache hit rate, dan log reader.

#### 2.2 Chatbot & RAG Orchestration Layer (`chatbot/`)
* [chatbot/api.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/api.py): Inisialisasi aplikasi FastAPI utama, middleware CORS, mounting modular routers, dan static mounting SPA Vue 3.
* [chatbot/bot.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/bot.py): Orkestrator utama bot cerdas dengan dual-mode routing (percakapan santai vs data terstruktur), query expansion follow-up, dan warmup memori.
* [chatbot/rag_feeder.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/rag_feeder.py): Jembatan antara retriever dan LLM context window; melakukan format markdown table injection dan metadata citation compiler.
* [chatbot/llm_client.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/llm_client.py): Gateway HTTPX mandiri tanpa SDK berat; mendukung Google Gemini REST API (dengan model cascading), OpenAI, Groq, Ollama, dan Mock mode.
* [chatbot/prompt_templates.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/prompt_templates.py): System prompt persona Sahabat Data BPS, aturan ketat anti-halusinasi (groundedness), notasi BPS, dan format kutipan.
* [chatbot/memory.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/memory.py): Manajemen session state percakapan berbasis sliding-window in-memory.
* [chatbot/cli.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/cli.py): Antarmuka baris perintah (CLI REPL) interaktif untuk pengujian terminal mandiri.
* [chatbot/config.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/config.py): Konfigurasi runtime chatbot berbasis Pydantic BaseSettings.

#### 2.3 Configuration & Database Connection (`config/`)
* [config/settings.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/config/settings.py): Master settings singleton proyek; path directory, batas ekstraksi, konfigurasi model embedding, dan kredensial API BPS.
* [config/database.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/config/database.py): Pengelola koneksi PostgreSQL terpusat dengan context manager `get_db_cursor()` untuk mencegah connection leak, serta fungsi verifikasi ekstensi `vector`.

#### 2.4 Pipeline Modules (`modules/`)
* **Ingestion:**
  * [modules/ingestion/bps_api_client.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/ingestion/bps_api_client.py): Klien resmi BPS Web API (`webapi.bps.go.id`) untuk Domain 3321; mengunduh metadata dan stream berkas PDF tanpa risiko bot challenge.
  * [modules/ingestion/bps_scraper.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/ingestion/bps_scraper.py): Web scraper HTML warisan (legacy fallback).
  * [modules/ingestion/registry.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/ingestion/registry.py): Registry SQLite (`database/bps_registry.db`) untuk deduplikasi unduhan dan pelacakan status ekstraksi.
* **Extraction:**
  * [modules/extraction/pdf_pipeline.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/extraction/pdf_pipeline.py): Orkestrator pemrosesan dokumen PDF menjadi tabel dan narasi per halaman.
  * [modules/extraction/table_extractor.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/extraction/table_extractor.py): Detektor tabel berbasis `pdfplumber` dengan pemindaian koordinat bounding box, judul tabel, catatan kaki, dan satuan.
  * [modules/extraction/table_cleaner.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/extraction/table_cleaner.py): Sanitasi matriks tabel; pemipihan multi-level header, forward-fill kolom kategorikal, serta preservasi notasi simbol statistik BPS (`-` sebagai NIL, `0` sebagai nol absolut, `...` sebagai data belum tersedia, `*` sebagai angka sementara).
  * [modules/extraction/text_extractor.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/extraction/text_extractor.py): Ekstraksi blok teks naratif dengan eliminasi margin header/footer dan deteksi hierarki bab/sub-bab.
* **Structuring:**
  * [modules/structuring/json_builder.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/structuring/json_builder.py): Mengonversi baris tabel dan paragraf naratif menjadi representasi kalimat alami (*row-to-speech representation*) serta menyusun chunk RAG ber-ID deterministik (MD5).
* **Vectorization:**
  * [modules/vectorization/embedder.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/vectorization/embedder.py): Penghasil dense vector 384 dimensi berbasis `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` dengan persistent cache PostgreSQL (`embedding_cache`).
* **Storage:**
  * [modules/storage/doc_store.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/storage/doc_store.py): Sistem penyimpanan NoSQL berjenjang: 1 JSON per tabel di `database/tables/`, 1 JSON per dokumen di `database/documents/`, dan 1 JSON narasi di `database/narratives/`.
  * [modules/storage/postgres_store.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/storage/postgres_store.py): Layer interaksi PostgreSQL untuk upsert vektor pgvector (HNSW) dan inverted index `tsvector` bahasa Indonesia.
  * [modules/storage/postgres_schema.sql](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/storage/postgres_schema.sql): DDL skema terpadu (tabel `publications`, `statistical_tables`, `vector_chunks`, `embedding_cache`).
  * [modules/storage/vector_store.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/storage/vector_store.py): Wrapper ChromaDB lokal (legacy fallback).
* **Retrieval:**
  * [modules/retrieval/hybrid_search.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/retrieval/hybrid_search.py): Engine pencarian hibrida menggabungkan dense cosine similarity pgvector dan lexical Full-Text Search via Reciprocal Rank Fusion (RRF).
  * [modules/retrieval/entity_dictionary.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/retrieval/entity_dictionary.py): Ekstraktor entitas 14 kecamatan di Kabupaten Demak dan tahun referensi untuk dynamic pre-filtering.

#### 2.5 Dual-Portal Frontend SPA (`frontend/`)
* [frontend/src/views/public/PublicChatView.vue](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/frontend/src/views/public/PublicChatView.vue): Antarmuka obrolan publik dengan pill pertanyaan rekomendasi, rendering Markdown, kartu sitasi resmi BPS, dan drawer transparansi data sumber.
* [frontend/src/views/admin/IngestionHubView.vue](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/frontend/src/views/admin/IngestionHubView.vue): Hub kontrol ingestion data; trigger Mode Inkremental (Web API), Mode Deep Ingest, dan Test Single Dokumen dengan progress bar dan log eksekusi real-time.
* [frontend/src/views/admin/DataExplorerView.vue](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/frontend/src/views/admin/DataExplorerView.vue): Antarmuka grid penjelajah 524+ tabel statistik, filter per-kecamatan, dan inspeksi JSON terstruktur.
* [frontend/src/views/admin/VectorObservabilityView.vue](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/frontend/src/views/admin/VectorObservabilityView.vue): Dashboard telemetri vektor HNSW, rasio cache embedding, dan playground uji pencarian semantik hibrida secara live.
* [frontend/src/views/admin/SystemLogsView.vue](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/frontend/src/views/admin/SystemLogsView.vue): Live log console viewer membaca log backend dan status koneksi database.
* [frontend/src/views/admin/AdminLoginView.vue](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/frontend/src/views/admin/AdminLoginView.vue): Portal login admin dengan integrasi tombol SIPETRA SSO BPS Demak dan fast local bypass login.

#### 2.6 Testing Suite (`tests/`)
* [tests/test_backend_api_routers.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_backend_api_routers.py): Pengujian endpoint auth, ingestion status, data viewer, dan telemetry.
* [tests/test_chatbot_integration.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_chatbot_integration.py): Pengujian routing obrolan santai vs feeding data grounded.
* [tests/test_embedder_cache.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_embedder_cache.py): Pengujian persistent caching dan jaminan ketiadaan random hash fallback.
* [tests/test_extraction.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_extraction.py): Pengujian sanitasi tabel, flattening header, dan numeric parsing.
* [tests/test_hybrid_retrieval.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_hybrid_retrieval.py): Pengujian ekstraksi entitas Demak dan eksekusi RRF search.
* [tests/test_pipeline_e2e.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_pipeline_e2e.py): Pengujian end-to-end penataan JSON dan penyimpanan dokumen.
* [tests/test_postgres_connection.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_postgres_connection.py): Verifikasi koneksi peladen PostgreSQL.
* [tests/test_postgres_schema.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_postgres_schema.py): Verifikasi keberadaan tabel DDL.
* [tests/test_postgres_store.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_postgres_store.py): Pengujian CRUD dan pencarian vektor di PostgreSQL.
* [tests/test_statistical_semantics.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/test_statistical_semantics.py): Pengujian kepatuhan semantik simbol statistik BPS.
* [tests/benchmarks/golden_dataset.json](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/benchmarks/golden_dataset.json): Dataset acuan emas berisi 36 skenario pertanyaan (kependudukan, pertanian, perikanan, kesehatan, geografi, dan pertanyaan unanswerable/out-of-domain).
* [tests/benchmarks/test_golden_benchmark.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/tests/benchmarks/test_golden_benchmark.py): Runner pengujian kualitas jawaban, ketepatan sitasi, dan abstention.

---

### 3. Identifikasi Masalah Struktur & Dead Code (Forensic Findings)

Berdasarkan penelusuran kode aktual, ditemukan beberapa kategori artefak struktural:

| File / Modul | Status | Analisis & Bukti | Rekomendasi Auditor |
|:---|:---:|:---|:---|
| `app.py` | **LEGACY GUI** | File antarmuka Streamlit berukuran 8.5 KB. Berfungsi penuh tetapi terpisah dari ekosistem SPA Vue 3 modern. | Pertahankan sebagai GUI alternatif pengujian cepat, namun dokumentasikan bahwa production UI adalah `frontend/`. |
| `run_dashboard.bat` & `run_dashboard.sh` | **LEGACY SCRIPT** | Script shell untuk menjalankan Streamlit `app.py`. | Tandai sebagai legacy launcher. |
| `test_run.py` & `test_download_and_convert.py` | **LEGACY TEST** | Script pengujian ad-hoc dari bulan Agustus 2026 sebelum dibuatnya suite `tests/` berbasis pytest. | Arsipkan ke folder `scripts/archive/` agar tidak membingungkan developer baru. |
| `batch_process_10_publications.py` & `run_ingestion.py` | **LEGACY CLI** | Script CLI ad-hoc yang ditulis sebelum modul `main.py` dan `api/routers/ingestion.py` disempurnakan. | Fungsionalitas sudah sepenuhnya terangkum dalam `main.py` dan API ingestion. |
| `database/chroma_store/` | **LEGACY STORE** | Direktori ChromaDB lokal berukuran 3.0 GB di disk. Masih memiliki fungsi fallback di `modules/storage/vector_store.py` namun database utama sudah PostgreSQL pgvector. | Aman untuk diabaikan atau dibersihkan secara bertahap setelah PostgreSQL stabil 100%. |
| `doc/` vs `docs/` | **FOLDER DUPLICATION** | Terdapat folder `doc/` (berisi file Word `.docx`) dan folder `docs/` (berisi file Markdown `.md`). | Pisahkan dengan jelas: `docs/` untuk dokumentasi teknis markdown, `doc/` untuk arsip laporan magang format office. |
| `TODO` / `FIXME` | **CLEAN** | Tidak ditemukan komentar `TODO` atau `FIXME` tak terselesaikan di seluruh file kode Python aktif. | Menunjukkan proses refaktorisasi sebelumnya telah menuntaskan tugas sementara. |
