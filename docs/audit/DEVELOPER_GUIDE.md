# Phase 14b — Panduan Pengembang & Arsitektur (Developer Guide)

## 1. Arsitektur Sistem & Direktori Proyek

Proyek `RAG3321` dibangun dengan pendekatan arsitektur terpadu (*unified architecture*):
- **Backend API**: Python 3.10+ dengan FastAPI & Uvicorn.
- **Frontend SPA**: Vue 3 + Vite + Tailwind CSS + Pinia + Lucide Icons.
- **Vector & Storage Engine**: PostgreSQL 16 dengan ekstensi `pgvector` v0.8.1 (menggunakan indeks HNSW dan GIN FTS).
- **Embedding Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensi).
- **LLM Engine**: Google Gemini API via REST / SDK resmi Google GenAI.

```
c:\Users\arkadjie\Documents\Documents\MAGANG BOSSS\IT\RAG/
├── api/                   # Controller FastAPI, Schema Pydantic, Routers
│   ├── main.py            # Entrypoint FastAPI & static mount
│   ├── routers/           # admin.py, chat.py, ingestion.py, logs.py
│   └── schemas/           # Pydantic v2 data models
├── chatbot/               # Orkestrator RAG, Prompt Engineering, LLM Client
│   ├── bot.py             # BPSChatbot logic & fallback
│   ├── rag_feeder.py      # PostgreSQL Hybrid Retriever (HNSW + FTS + RRF)
│   └── llm_client.py      # Google Gemini client wrapper
├── frontend/              # Source code Vue 3 SPA (Vite)
│   ├── src/views/         # ChatView.vue, AdminLayout.vue, DataExplorerView.vue, dll.
│   └── dist/              # Production static bundle yang di-serve oleh FastAPI
├── modules/               # Core pipeline ingestion & processing
│   ├── crawler/           # web_api_crawler.py (BPS Web API v1 client)
│   ├── extraction/        # extractor.py, cleaner.py, synthesizer.py
│   ├── storage/           # vector_store.py (PostgreSQL BPSVectorStore)
│   └── vectorization/     # embedder.py (SentenceTransformer wrapper)
├── tests/                 # Suite pengujian otomatis (unit, integration, benchmarks)
└── scripts/               # Script inisialisasi basis data dan utilitas
```

---

## 2. Petunjuk Instalasi & Setup Lingkungan Lokal

### Prasyarat:
1. Python 3.10 atau 3.11 terpasang.
2. Node.js v18+ dan npm (hanya jika ingin melakukan modifikasi pada kode frontend).
3. Akses ke instance PostgreSQL 16 dengan ekstensi `pgvector` aktif.

### Langkah-Langkah:
```powershell
# 1. Clone repositori & masuk ke direktori
git clone https://github.com/arkadjie795/RAG.git
cd RAG

# 2. Buat virtual environment & install dependensi Python
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Salin file konfigurasi environment
cp .env.example .env
# Edit variabel: POSTGRES_*, GEMINI_API_KEY, BPS_API_KEY

# 4. Inisialisasi Skema Database PostgreSQL
python scripts/init_db.py

# 5. Jalankan Server Terpadu (Single-Port Serving)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Alur Kerja Modifikasi & Kompilasi Frontend

Jika Anda mengubah kode di dalam direktori `frontend/src/`:
```powershell
cd frontend
npm install
npm run build
cd ..
```
Hasil build secara otomatis diletakkan pada `frontend/dist/`. Backend FastAPI di `api/main.py` langsung menyajikan folder ini tanpa perlu me-restart server backend jika flag `--reload` aktif.

---

## 4. Struktur Database & Konfigurasi Ekstensi pgvector

Skrip SQL inti (`scripts/init_db.sql`) mengaktifkan ekstensi dan membuat indeks:
```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabel Chunks Vektor
CREATE TABLE IF NOT EXISTS vector_chunks (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indeks HNSW Cosine
CREATE INDEX IF NOT EXISTS idx_vector_chunks_embedding_hnsw 
ON vector_chunks USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Indeks Full-Text Search Bahasa Indonesia
ALTER TABLE vector_chunks ADD COLUMN IF NOT EXISTS tsv tsvector;
UPDATE vector_chunks SET tsv = to_tsvector('indonesian', content);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_tsv ON vector_chunks USING gin(tsv);
```

---

## 5. Menjalankan Pengujian Otomatis

Untuk memastikan integritas seluruh pipeline:
```powershell
# Menjalankan seluruh unit & integration test
python -m pytest tests/ -v

# Menjalankan hanya pengujian ekstraksi data
python -m pytest tests/unit/test_cleaner.py tests/unit/test_extractor.py -v
```
