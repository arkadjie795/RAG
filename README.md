# BPS Demak Automated ETL & RAG Vectorization Pipeline

A production-grade, automated Data Pipeline (ETL) and Indexing System designed for Retrieval-Augmented Generation (RAG) over Badan Pusat Statistik (BPS) publications (Kabupaten Demak).

---

## Operational Modes

The master orchestrator (`main.py`) supports three distinct operational modes via `--mode`:

### 1. `statis` (Default)
Periodic incremental ingestion. Scrapes the first 2 pages of the BPS catalog, downloads only new publications (verified against SQLite registry), and indexes them into the Document & Vector databases.
```bash
python main.py --mode statis
```

### 2. `all`
Deep historical crawl. Scrapes up to 50 pages of the BPS catalog and downloads/indexes all unindexed publications.
```bash
python main.py --mode all
# Or with custom depth:
python main.py --mode all --max-pages 20
```

### 3. `test`
Single-document verification run. Fetches page 1, acquires the latest document, parses, structures, vectorizes, stores, and executes an automated semantic search retrieval proof.
```bash
python main.py --mode test
```

---

## On-Demand Utilities

### Direct Single PDF Processing
```bash
python main.py --pdf "data_publikasi/demak/2026/01/sample_demak_test.pdf"
```

### On-Demand Semantic Search with Metadata Pre-filtering
```bash
python main.py --query "Berapa jumlah penduduk di Kecamatan Mranggen?" --filter-kategori Kependudukan --filter-tahun 2026
```

---

## System Architecture

```
[ BPS Demak Portal ]
        │
        ▼ (Module 1: Ingestion)
[ SQLite Deduplication Registry ] ──> Downloads only new PDFs to /data_publikasi/demak/YYYY/MM/
        │
        ▼ (Module 2: Extraction)
[ PDF Extractor (pdfplumber) ] ──> Multi-level header flattening + forward-fill (ffill) + BPS numeric sanitization
        │
        ▼ (Module 3: Structuring)
[ JSON Formulation Engine ] ──> Injects context + generates dynamic natural language 'representasi_teks'
        │
        ▼ (Module 4: Vectorization)
[ SentenceTransformers Embedder ] ──> Generates normalized dense vectors (paraphrase-multilingual-MiniLM-L12-v2)
        │
        ├─────────────────────────────────────────────────┐
        ▼ (Module 5a: Granular JSON Storage)              ▼ (Module 5b: Vector DB)
[ 1 JSON Per Tabel: database/tables/{doc_id}/ ]     [ PostgreSQL 16 + pgvector (0.8.1) HNSW ]
[ 1 JSON Per PDF  : database/documents/{doc_id}.json ] (Vectors point directly to table JSONs)
[ 1 JSON Per Teks : database/narratives/{doc_id}/ ]
```

---

## Granular JSON Storage (Anti-Token Blowout)

To prevent LLM context-window exhaustion and hallucinations, the pipeline does NOT dump entire books into a single monolithic JSON file. Instead, it generates granular, self-contained files:

1. **1 File JSON Per Tabel (`database/tables/{doc_id}/tabel_{tabel_id}.json`)**:
   Contains table headers, cleaned records, row-level natural language representations, units, sources, and chunk IDs (~2-5 KB).
2. **1 File JSON Per PDF (`database/documents/{doc_id}.json`)**:
   Contains document metadata, list of extracted table JSON file paths, list of narrative JSON file paths, and chunk summaries.
3. **1 File JSON Per Narasi (`database/narratives/{doc_id}/naratif_{idx}.json`)**:
   Contains chapter and paragraph-level narrative text blocks.
4. **Direct Vector-to-JSON Linking**:
   When Vector Search retrieves relevant chunks, it returns the direct file path to the corresponding table JSON (`file_json_tabel`), allowing AI agents to read only the target table without loading the whole publication.

---

## 🤖 AI Chatbot (RAG-Fed Assistant & Web GUI)

Sistem ini dilengkapi antarmuka lengkap (Web GUI modern, CLI interaktif, dan REST API) di dalam folder [`chatbot/`](chatbot/README.md) yang mengonsumsi data dari pipeline RAG secara langsung.

### 1. Menjalankan Web GUI Interaktif (Streamlit) — *Sangat Direkomendasikan*
Antarmuka visual modern bertema BPS dengan panel chat, filter 14 kecamatan/tahun, status koneksi database, dan sitasi dokumen:
```bash
streamlit run app.py
```
*(Atau dengan environment Python Laragon):*
```bash
C:\laragon\bin\python\python-3.10\python.exe -m streamlit run app.py
```
Akses di browser: `http://localhost:8501`

### 2. Menjalankan Terminal Interaktif (CLI)
Sesi percakapan interaktif langsung di command line:
```bash
python -m chatbot.cli
```

### 3. Menjalankan REST API & Swagger UI (FastAPI)
Untuk integrasi dengan aplikasi eksternal atau WhatsApp/Telegram bot:
```bash
python -m uvicorn chatbot.api:app --reload --port 8000
```
Akses dokumentasi interaktif Swagger UI di: `http://127.0.0.1:8000/docs`

### Konfigurasi API LLM:
Salin file `.env.example` menjadi `.env`, lalu masukkan API Key (misal: Google Gemini atau OpenAI):
```bash
copy .env.example .env
```
Dokumentasi edukasi hasil audit & roadmap untuk tim magang dapat dilihat di:
- [`docs/LAPORAN_EDUKASI_HASIL_AUDIT_MAGANG.md`](docs/LAPORAN_EDUKASI_HASIL_AUDIT_MAGANG.md)
- [`docs/RAG3321_ENGINEERING_AUDIT_AND_IMPLEMENTATION_PLAN.md`](docs/RAG3321_ENGINEERING_AUDIT_AND_IMPLEMENTATION_PLAN.md)

---

## Changelog

### 2026-11-09
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
