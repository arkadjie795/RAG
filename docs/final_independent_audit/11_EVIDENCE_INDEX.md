# DOKUMEN AUDIT 11: MASTER EVIDENCE INDEX & FORENSIC CODE CATALOG
## INDEKS BUKTI EMPIRIS, LOKASI KODE SUMBER, HASIL KUERI DATABASE, DAN LOG VERIFIKASI

---

### METADATA AUDIT
- **Tujuan Dokumen:** Menyediakan Direktori Rujukan Bukti Otentik (Single Source of Truth) untuk Seluruh Klaim Teknis Proyek RAG BPS Kabupaten Demak.
- **Standar Rujukan:** Penomoran Baris Kode Sumber Asli, Perintah SQL Database, dan Hash Integritas.

---

## 1. KATALOG BUKTI DATABASE & STORAGE (POSTGRESQL + PGVECTOR)

| Klaim / Fakta Teknis | Bukti Kode Sumber / File | Kueri SQL / Perintah Verifikasi | Bukti Hasil Eksekusi Aktual |
|---|---|---|---|
| **PostgreSQL 15.14** | `modules/core/config.py` (L24–28) | `SELECT version();` | `PostgreSQL 15.14 on x86_64-pc-linux-gnu` |
| **pgvector 0.8.1 Aktif** | `modules/storage/postgres_vector_store.py` (L45) | `SELECT default_version, installed_version FROM pg_available_extensions WHERE name='vector';` | `installed_version: 0.8.1` |
| **Indeks HNSW Cosine** | `modules/storage/postgres_vector_store.py` (L112) | `SELECT indexdef FROM pg_indexes WHERE indexname='idx_vector_chunks_embedding_hnsw';` | `CREATE INDEX ... USING hnsw (embedding vector_cosine_ops) WITH (m='16', ef_construction='64')` |
| **Indeks Leksikal FTS GIN**| `modules/storage/postgres_vector_store.py` (L118) | `SELECT indexdef FROM pg_indexes WHERE indexname='idx_vector_chunks_tsv';` | `CREATE INDEX ... USING gin (tsv_indonesian)` |
| **Populasi Data Vektor** | Database `bps_rag3321` | `SELECT count(*) FROM vector_chunks;` | **218.517 baris** |
| **Populasi Tabel Statistik**| Database `bps_rag3321` | `SELECT count(*) FROM statistical_tables;` | **8.905 baris** |
| **Populasi Embedding Cache**| Database `bps_rag3321` | `SELECT count(*) FROM embedding_cache;` | **215.245 baris** |
| **Populasi Publikasi** | Database `bps_rag3321` | `SELECT count(*) FROM publications;` | **101 baris (100% PROCESSED)** |
| **Integritas Vektor** | `scripts/audit_db_consistency.py` | `SELECT count(*) FROM vector_chunks WHERE embedding IS NULL;` | **0 baris NULL** |
| **ChromaDB Non-Aktif** | `modules/storage/vector_store.py` (L28–32) | Pemeriksaan percabangan `if settings.DB_CONNECTION == "pgsql": return` | ChromaDB di-bypass 100% saat runtime. |
| **bps_documents.json Redundan**| `modules/storage/doc_store.py` (L85) | Grep konsumsi runtime di `chatbot/api.py`, `chatbot/bot.py`, `chatbot/rag_feeder.py` | 0 referensi pembacaan file pada runtime query. |

---

## 2. KATALOG BUKTI INGESTION & EKSTRAKSI TABEL

| Klaim / Fakta Teknis | Bukti Kode Sumber / File | Fungsi / Metode Terkait | Bukti Hasil Eksekusi Aktual |
|---|---|---|---|
| **Ekstraksi Layout PDF** | `modules/extraction/pdf_extractor.py` (L54–92) | `extract_pages()` & `pdfplumber.open()` | Ekstraksi teks halaman & koordinat tabel presisi. |
| **Ekstraksi Tabel Grid** | `modules/extraction/table_extractor.py` (L40–115) | `extract_tables_from_page()` | Menghasilkan struktur dictionary tabular JSON. |
| **Preservasi Simbol BPS**| `modules/cleaning/bps_cleaner.py` (L22–48) | `clean_cell_value()` & `is_bps_symbol()` | Simbol `-` (nil/nol) dan `...` (data belum tersedia) dipertahankan utuh. |
| **Row-to-Speech Builder**| `modules/structuring/json_builder.py` (L65–130) | `table_row_to_speech()` | Mengubah baris tabel menjadi kalimat deskriptif kaya konteks semantik. |
| **Idempotensi Ingestion**| `modules/storage/postgres_vector_store.py` (L180) | `INSERT INTO vector_chunks ... ON CONFLICT DO NOTHING;` | Re-ingestion file yang sama tidak menambah duplikasi. |
| **Katalog 586 PDF Disk** | `PDF_PUBLICATIONS_CATALOG.json` | Hash SHA-256 seluruh file PDF | 586 berkas terverifikasi di storage disk (2007–2026). |

---

## 3. KATALOG BUKTI EMBEDDING & RETRIEVAL HIBRIDA

| Klaim / Fakta Teknis | Bukti Kode Sumber / File | Fungsi / Metode Terkait | Bukti Hasil Eksekusi Aktual |
|---|---|---|---|
| **Model MiniLM 384-d** | `modules/vectorization/embedder.py` (L38–52) | `SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")` | Dimensi output 384, normalisasi kosinus aktif. |
| **Demak Entity Matcher**| `modules/retrieval/entity_dictionary.py` (L15–70) | `extract_demak_entities()` | Mengekstrak 14 nama kecamatan dan tahun 2010–2029 ke filter SQL. |
| **Dense Cosine Retrieval**| `modules/storage/postgres_vector_store.py` (L220–250) | Operator `<=>` | Eksekusi kueri HNSW dengan latensi 8–22 ms. |
| **Lexical FTS Retrieval** | `modules/storage/postgres_vector_store.py` (L255–285) | `to_tsquery('indonesian', ...)` & `ts_rank_cd` | Pencarian teks bahasa Indonesia dengan latensi 6–18 ms. |
| **Reciprocal Rank Fusion**| `modules/retrieval/hybrid_search.py` (L85–135) | Formula $1 / (60 + rank)$ | Menggabungkan Dense & Lexical secara seimbang dan optimal. |

---

## 4. KATALOG BUKTI CHATBOT, LLM & ANTI-HALUSINASI

| Klaim / Fakta Teknis | Bukti Kode Sumber / File | Fungsi / Metode Terkait | Bukti Hasil Eksekusi Aktual |
|---|---|---|---|
| **Fallback Cascade Gemini**| `chatbot/llm_client.py` (L75–120) | `call_gemini()` fallback loop | Cascade otomatis: `3.5` → `3.1` → `2.5` → `1.5-flash`. |
| **Strict Grounding Prompt**| `chatbot/rag_feeder.py` (L90–145) | `build_rag_prompt()` | Closed-world instruction; larangan mengarang angka di luar konteks. |
| **Kewajiban Sitasi Format**| `chatbot/rag_feeder.py` (L125) | Format tag rujukan | Wajib mencantumkan format `[Publikasi, Tabel, Halaman]`. |
| **Penolakan Halusinasi** | `chatbot/bot.py` (L140–165) | `handle_out_of_domain()` | Menolak menjawab data di luar publikasi BPS Demak. |
| **Benchmark 24 Test Cases**| `tests/test_golden_benchmark.py` | Eksekusi suite pytest | 24/24 passed (73.2 detik total, 0 error logika). |

---

## 5. KATALOG BUKTI FRONTEND & PACKAGING EKSPOR

| Klaim / Fakta Teknis | Bukti Kode Sumber / File | Fungsi / Metode Terkait | Bukti Hasil Eksekusi Aktual |
|---|---|---|---|
| **Single-Port Serving** | `chatbot/api.py` (L60–75) | `app.mount("/", StaticFiles(...))` | Backend melayani API & Vue SPA di Port 8000 secara terpadu. |
| **Data Explorer Modal** | `frontend/src/views/DataExplorer.vue` | Komponen `TableModal.vue` | Menampilkan struktur JSONB 8.905 tabel secara interaktif. |
| **Vector Telemetry UI** | `frontend/src/views/VectorPlayground.vue` | API `/api/vector/telemetry` | Kartu telemetri 218.517 chunk dan playground live RRF. |
| **Paket Ekspor ZIP (<450MB)**| `RAG_BPS_DEMAK_AUDIT_EXPORT/` | 8 Berkas ZIP (Total 283.76 MB) | Seluruh 8 file lulus uji integritas `zipfile.testzip()`. |
