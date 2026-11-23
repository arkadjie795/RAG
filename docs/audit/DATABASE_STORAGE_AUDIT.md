# 🗄️ PHASE 5: DATABASE & STORAGE AUDIT
## Project: BPS Demak RAG Knowledge Base & AI Chatbot ("Sahabat Data BPS" / RAG3321)
**Auditor:** Multi-Disciplinary Forensic Engineering Team  
**Audit Date:** 2026-11-13  
**Classification:** Deep Persistence, Schema Integrity, Indexing, and Concurrency Review  

---

### 1. Inventarisasi Mesin Penyimpanan (Storage Engines)

Sistem RAG3321 menggunakan arsitektur penyimpanan hibrida multi-tier:

```
                    ┌──────────────────────────────────────────────┐
                    │          APLIKASI RAG (FASTAPI)              │
                    └──────┬──────────────┬──────────────┬─────────┘
                           │              │              │
              ┌────────────▼─────┐  ┌─────▼────────┐  ┌──▼───────────────┐
              │  PostgreSQL 16   │  │  SQLite DB   │  │   JSON Storage   │
              │   + pgvector     │  │  (Registry)  │  │   (NoSQL Tier)   │
              └──────────────────┘  └──────────────┘  └──────────────────┘
              - statistical_tables  - bps_registry.db - database/tables/
              - vector_chunks                         - database/documents/
              - embedding_cache                       - database/narratives/
              - publications
```

1. **Primary Enterprise Tier:** **PostgreSQL 16 Enterprise + pgvector v0.8.1**
   - Host: `10.133.21.24:5433` | Database: `bps_rag3321`
   - Menyimpan seluruh data relasional tabel statistik, chunk embedding vektor, indeks leksikal teks penuh, dan persistent embedding cache.
2. **Local Metadata Ingestion Tier:** **SQLite 3 (`database/bps_registry.db`)**
   - Melacak status deduplikasi unduhan berkas PDF BPS secara lokal.
3. **Granular File System NoSQL Tier:** **JSON Storage Files**
   - `database/tables/`: 466+ file JSON granular (1 file per tabel statistik).
   - `database/documents/`: 487 file JSON master metadata dokumen publikasi.
   - `database/narratives/`: 477 file JSON kumpulan teks narasi.
4. **Legacy Tier:** **ChromaDB Local Vector Store (`database/chroma_store/`)**
   - Berukuran 3.0 GB di disk; dipertahankan sebagai layer fallback jika koneksi PostgreSQL mengalami pemeliharaan.

---

### 2. Audit Skema & Integritas Relasional PostgreSQL

DDL skema terpusat didefinisikan pada [modules/storage/postgres_schema.sql](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/storage/postgres_schema.sql).

#### A. Tabel `publications` (Master Publikasi)
* **Struktur:** `publication_id` (PK, TEXT), `title` (TEXT NOT NULL), `release_date` (TEXT), `category` (TEXT), `pdf_url` (TEXT), `local_file_path` (TEXT), `file_size_bytes` (BIGINT), `download_status` (TEXT), `extraction_status` (TEXT), `total_tables_extracted` (INT), `total_chunks_indexed` (INT), `created_at` (TIMESTAMPTZ).
* **Indeks:** `idx_pub_status` on `(download_status, extraction_status)`, `idx_pub_category` on `(category)`.
* **Kondisi Data Aktual:** 11 publikasi resmi BPS Demak (tahun 2025/2026) tercatat lengkap dengan path absolut berkas PDF lokal.

#### B. Tabel `statistical_tables` (Penyimpanan Granular Tabel Statistik)
* **Struktur:** `table_id` (PK, TEXT), `doc_id` (FK ke `publications.publication_id`), `doc_title` (TEXT), `table_number` (TEXT), `table_title` (TEXT NOT NULL), `halaman` (INT), `kecamatan` (TEXT), `tahun` (TEXT), `satuan` (TEXT), `sumber` (TEXT), `catatan` (TEXT), `kolom` (JSONB), `records` (JSONB), `created_at` (TIMESTAMPTZ).
* **Indeks:** `idx_st_doc_id`, `idx_st_kecamatan`, `idx_st_tahun`.
* **Kondisi Data Aktual:** **524 tabel statistik** terindeks secara granular. Kolom `records` menyimpan seluruh baris tabel dalam format JSONB yang dapat di-query dengan efisien menggunakan operator JSONB PostgreSQL (`->`, `->>`, `@>`).

#### C. Tabel `vector_chunks` (Penyimpanan Vektor pgvector & Full-Text Search)
* **Struktur:** `chunk_id` (PK, TEXT), `doc_id` (TEXT), `table_id` (TEXT), `tipe_konten` (TEXT), `daerah` (TEXT), `kategori` (TEXT), `tahun` (TEXT), `halaman` (INT), `judul_tabel` (TEXT), `satuan` (TEXT), `sumber` (TEXT), `representasi_teks` (TEXT NOT NULL), `metadata` (JSONB), `embedding` (`vector(384)`), `tsv` (`tsvector`).
* **Indeks Vektor HNSW:**
  ```sql
  CREATE INDEX idx_chunks_embedding_hnsw 
  ON vector_chunks USING hnsw (embedding vector_cosine_ops);
  ```
  *Parameter HNSW:* `m = 16`, `ef_construction = 64`. Menyediakan kompleksitas pencarian $O(\log N)$ yang sangat cepat bahkan ketika jumlah vektor mencapai ratusan ribu.
* **Indeks Leksikal GIN:**
  ```sql
  CREATE INDEX idx_chunks_tsv ON vector_chunks USING gin (tsv);
  ```
  Menggunakan parser konfigurasi bahasa Indonesia (`to_tsvector('indonesian', representasi_teks)`).
* **Indeks Partisi / B-Tree:** `daerah`, `tahun`, `kategori`, `tipe_konten`.
* **Kondisi Data Aktual:** **10.682 vector chunks** aktif dan terindeks penuh.

#### D. Tabel `embedding_cache` (Persistent Cache)
* **Struktur:** `text_hash` (PK, TEXT), `model_name` (TEXT NOT NULL), `embedding` (`vector(384)` NOT NULL), `created_at` (TIMESTAMPTZ).
* **Indeks:** `idx_emb_cache_model` on `(model_name)`.
* **Kondisi Data Aktual:** **10.378 vektor ter-cache**. Memastikan bahwa setiap teks tabel yang pernah diproses sebelumnya tidak akan pernah membebani komputasi CPU lagi.

---

### 3. Audit Pengelolaan Koneksi (Connection Leak Prevention)

Pada audit sebelumnya, teridentifikasi potensi *connection leak* di mana endpoint API membuka koneksi `psycopg2.connect()` namun tidak selalu mengeksekusi `conn.close()` di dalam blok `finally`.

**Hasil Audit Implementasi Aktual Saat Ini:**
Pada [config/database.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/config/database.py), masalah tersebut telah **dimitigasi secara tuntas** melalui context manager aman:

```python
@contextmanager
def get_db_cursor(database: str = None, commit: bool = False):
    conn = get_db_connection(database=database)
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass
```

Setiap endpoint di `api/routers/data_viewer.py`, `system_telemetry.py`, dan `ingestion.py` sekarang menggunakan konstruksi `with get_db_cursor() as cur:` yang menjamin koneksi selalu ditutup bahkan jika terjadi exception SQL, mencegah kehabisan pool koneksi pada peladen PostgreSQL.

---

### 4. Konsistensi Data & Risiko Orphan Records

* **Foreign Key Constraints:** Tabel `statistical_tables` memiliki constraint foreign key `doc_id REFERENCES publications(publication_id) ON DELETE CASCADE`. Jika satu publikasi dihapus, seluruh tabel turunannya akan terhapus secara otomatis.
* **Tabel `vector_chunks`:** Kolom `doc_id` pada `vector_chunks` saat ini berstatus *unconstrained TEXT* (tidak memiliki foreign key keras).
  * *Risiko:* Jika sebuah publikasi dihapus dari tabel `publications`, baris vektornya di `vector_chunks` berpotensi menjadi *orphan chunks*.
  * *Rekomendasi:* Tambahkan foreign key constraint atau cascading trigger pada `vector_chunks.doc_id` pada rilis skema berikutnya.
* **Persistensi Data:** Data diuji tetap bertahan utuh setelah peladen web FastAPI di-restart berulang kali, membuktikan bahwa data sepenuhnya tersimpan pada disk PostgreSQL dan bukan sekadar in-memory state.
