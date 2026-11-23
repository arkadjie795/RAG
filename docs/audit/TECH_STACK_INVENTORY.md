# 🛠️ PHASE 1: COMPLETE TECHNOLOGY STACK INVENTORY
## Project: BPS Demak RAG Knowledge Base & AI Chatbot ("Sahabat Data BPS" / RAG3321)
**Auditor:** Multi-Disciplinary Forensic Engineering Team  
**Audit Date:** 2026-11-13  
**Classification:** Deep Dependency, Runtime, and Engine Verification  

---

### 1. Rincian Kategori Teknologi

#### A. Programming Languages
* **Python (v3.12.10 di Host, v3.11 di Docker):** Bahasa utama backend pipeline, ekstraksi PDF, vektorisasi, dan orkestrasi inferensi LLM.
* **JavaScript / TypeScript (ES2022+):** Bahasa pemrograman antarmuka frontend (Vue 3, Vite, Tailwind).
* **SQL (PostgreSQL Dialect):** DDL skema relasional, query vektor HNSW, dan query teks penuh `tsvector` dengan RRF.
* **HTML5 & CSS3:** Tata letak antarmuka web, styling Tailwind CSS, dan komponen generatif.

#### B. Framework & Server Runtime
* **FastAPI (v0.110.0+):** Framework REST API backend berkecepatan tinggi dengan validasi Pydantic v2.
* **Uvicorn (v0.28.0+):** Peladen ASGI berperforma tinggi untuk menjalankan backend FastAPI.
* **Vue.js 3 (v3.5+):** Framework frontend reaktif berbasis *Composition API* (`<script setup>`) dengan router dinamis (`vue-router` v4).
* **Vite (v8.3.6):** Build tool frontend modern dan modul bundler super cepat.
* **Tailwind CSS (v3.4):** Framework styling utilitas untuk desain UI modern, responsif, dan konsisten dengan identitas BPS.
* **Streamlit (v1.32+):** Framework antarmuka alternatif / legacy untuk demonstrasi lokal instan (`app.py`).

#### C. AI & LLM Engine
* **LLM Provider:** Google Gemini API (v1beta REST API).
* **Primary Model:** `gemini-3.1-flash-lite` (direkomendasikan karena kecepatan dan kepatuhan terhadap konteks grounded).
* **Backup/Fallback Models:** `gemini-3.5-flash`, `gemini-2.5-flash` (dieksekusi secara otomatis jika model utama mengalami kuota/timeout).
* **Alternative Providers (Implemented in `llm_client.py`):**
  * OpenAI (`gpt-4o-mini`, `gpt-4o`)
  * Groq (`llama-3.1-8b-instant`)
  * Ollama (`llama3` / local offline LLM)
  * Mock / Dry-Run (untuk pengujian isolated tanpa jaringan)
* **Klien Integrasi:** Menggunakan HTTPX langsung (`httpx.Client`) dengan header `x-goog-api-key`, mengeliminasi dependensi berat SDK pihak ketiga (`google-generativeai`).
* **Parameter Inferensi:**
  * `temperature`: 0.2 (rendah untuk mencegah halusinasi data statistik)
  * `maxOutputTokens`: 2048
  * `systemInstruction`: Definisi peran persona resmi Sahabat Data BPS Demak dengan instruksi penolakan (*abstention*) jika data tidak ditemukan di tabel.

#### D. Embedding & Semantic Vectorization
* **Embedding Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
* **Arsitektur:** Transformer berbasis BERT multilingual 12-layer.
* **Dimensi Vektor:** 384 dimensi (float32).
* **Normalisasi:** Vektor dinormalisasi L2 untuk mendukung pengukuran Cosine Distance.
* **Inference Runtime:** PyTorch CPU-only (efisien tanpa memerlukan GPU dedicated).
* **Caching Layer:** Persistent hash cache di tabel PostgreSQL `embedding_cache` (berdasarkan MD5 string teks dan nama model) untuk mengeliminasi komputasi berulang.

#### E. Vector Database & Storage Engine
* **Vector DB Utama:** PostgreSQL 16 Enterprise dengan ekstensi `pgvector` v0.8.1.
* **Indeks Vektor:** HNSW (*Hierarchical Navigable Small World*) menggunakan operator `vector_cosine_ops` (`m=16`, `ef_construction=64`).
* **Indeks Leksikal:** GIN index pada kolom `tsvector` bahasa Indonesia (`to_tsvector('indonesian', text)`).
* **Metode Retrieval:** Native Reciprocal Rank Fusion (RRF) menggabungkan Dense Score dan Lexical BM25/FTS score.
* **Vector DB Cadangan (Legacy):** ChromaDB v0.4.24 (terisolasi di `modules/storage/vector_store.py`).
* **Dokumen NoSQL:** Sistem penyimpanan JSON granular terstruktur (1 file JSON per tabel di `database/tables/`, 1 JSON per dokumen di `database/documents/`, dan 1 JSON narasi di `database/narratives/`).

#### F. Document Processing & Table Extraction
* **PDF Engine:** `pdfplumber` v0.10.4+, `pypdf` v4.1.0+, `pdfminer.six`.
* **Table Extraction Heuristic:** Custom scanning bounding box koordinat garis (`vertical_strategy: lines`, `horizontal_strategy: lines`) serta fallback scanning teks bertingkat.
* **Matrix Cleaning:** `pandas` v2.2.1+, `numpy` v1.26.4+.
* **BPS Notations Handler:** Menangani simbol resmi statistik BPS (`-`, `–`, `—`, `0`, `0,0`, `...`, `*`, `r`).
* **OCR Capability:** Tidak ada modul OCR (mengandalkan ekstraksi teks digital langsung dari PDF resmi BPS).

#### G. RAG Framework
* **Implementasi:** **100% Custom Native Architecture** (Modular Micro-Engine).
* **Evaluasi Ketergantungan:** Proyek ini **TIDAK** menggunakan LangChain atau LlamaIndex. Seluruh alur (ekstraksi, penataan, vektorisasi, penyimpanan, dan retrieval) dibangun secara spesifik menggunakan modul Python mandiri untuk performa optimal dan ketiadaan abstraksi tersembunyi.

#### H. Infrastruktur & DevOps
* **Sistem Operasi Host:** Microsoft Windows 10 Pro (x64).
* **Sistem Operasi Kontainer:** Debian GNU/Linux 12 (bookworm) / Python 3.11-slim.
* **Peladen Database Eksternal:** PostgreSQL 16 di `10.133.21.24:5433` (Database: `bps_rag3321`).
* **Kontainerisasi:** Dockerfile multi-stage (Node.js 20 build stage $\to$ Python 3.11 run stage) & `docker-compose.yml`.
* **Proses Background:** Threading daemon aman dengan `threading.RLock()` dan state manager `IngestionJobState`.

#### I. Testing & Observability Tools
* **Testing Framework:** `pytest` v9.2.0, `anyio` v4.14.2, `Faker`.
* **Logging Engine:** `loguru` v0.7.2 dengan sink ke terminal dan file harian `logs/pipeline_YYYYMMDD.log`.
* **SSO Gateway:** SIPETRA OAuth2 client (`bpsdemak.com`).

---

### 2. Tabel Inventaris Lengkap Komponen Teknologi

| Komponen | Teknologi | Versi Terpasang | Fungsi Spesifik | Lokasi Implementasi | Status Operasional |
|:---|:---|:---|:---|:---|:---:|
| **Web API Backend** | FastAPI | `0.110.0+` | REST API, Controller Router, CORS | `chatbot/api.py`, `api/routers/` | **AKTIF (PROD)** |
| **ASGI Server** | Uvicorn | `0.28.0+` | Web server runtime port 8000 | `chatbot/api.py`, `Dockerfile` | **AKTIF (PROD)** |
| **Frontend Framework** | Vue.js | `v3.5.31` | Single Page Application framework | `frontend/src/` | **AKTIF (PROD)** |
| **Build Bundler** | Vite | `v8.3.6` | Kompilasi aset frontend ke `dist/` | `frontend/vite.config.js` | **AKTIF (PROD)** |
| **CSS Framework** | Tailwind CSS | `v3.4.1` | Desain responsif BPS dual-portal | `frontend/tailwind.config.js` | **AKTIF (PROD)** |
| **UI Icons** | Lucide Vue Next | `v1.16.0` | Ikon antarmuka portal | `frontend/package.json` | **AKTIF (PROD)** |
| **Alternative GUI** | Streamlit | `v1.32.0+` | Dashboard demonstrasi lokal cepat | `app.py`, `run_dashboard.bat` | **LEGACY / OPT** |
| **Language Model** | Google Gemini | REST v1beta | Inferensi penalaran dan generasi jawaban | `chatbot/llm_client.py` | **AKTIF (PROD)** |
| **Embedding Model** | SentenceTransformers | `v2.5.1` | Mengubah teks ke vektor 384-d | `modules/vectorization/embedder.py` | **AKTIF (PROD)** |
| **Vector DB** | pgvector (PostgreSQL) | `v0.8.1` | Indeks HNSW vektor & pencarian leksikal | Peladen `10.133.21.24:5433` | **AKTIF (PROD)** |
| **Fallback Vector DB**| ChromaDB | `v0.4.24` | Penyimpanan vektor lokal warisan | `modules/storage/vector_store.py` | **FALLBACK** |
| **PDF Parser** | pdfplumber | `v0.10.4` | Ekstraksi tabel koordinat bounding box | `modules/extraction/` | **AKTIF (PROD)** |
| **PDF Reader** | pypdf | `v4.1.0` | Validasi berkas PDF dan pembuatan sampel| `main.py`, `bps_api_client.py` | **AKTIF (PROD)** |
| **Data Processing** | pandas & numpy | `2.2.1 / 1.26.4` | Sanitasi matriks tabel dan angka | `modules/extraction/table_cleaner.py`| **AKTIF (PROD)** |
| **BPS Web API** | HTTPX | `v0.27.0` | Unduh metadata & berkas Domain 3321 | `modules/ingestion/bps_api_client.py`| **AKTIF (PROD)** |
| **Registry Tracker** | SQLite3 | Native Python | Deduplikasi berkas unduhan lokal | `modules/ingestion/registry.py` | **AKTIF (PROD)** |
| **Logging** | Loguru | `v0.7.2` | Structured telemetry & daily logs | `logs/`, seluruh modul | **AKTIF (PROD)** |
| **Unit Testing** | Pytest | `v9.2.0` | Pengujian otomasi 24 skenario | `tests/` | **AKTIF (PROD)** |
| **Container Engine** | Docker & Compose | Multi-stage | Deployment kontainer terisolasi | `Dockerfile`, `docker-compose.yml` | **AKTIF (PROD)** |
