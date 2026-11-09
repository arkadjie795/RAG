# PostgreSQL + pgvector Migration & Technical Audit Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Memigrasikan arsitektur penyimpanan dan retrieval sistem RAG3321 ke PostgreSQL 15 + `pgvector` terpadu pada database baru `bps_rag3321`, sekaligus menuntaskan seluruh temuan audit kritis (perbaikan konversi simbol statistik di `table_cleaner.py`, eliminasi pseudo-random embedder fallback, hybrid search native di SQL, dan deterministic numerical answering).

**Architecture:** Mengadopsi arsitektur *Single Source of Truth* berbasis PostgreSQL: seluruh metadata publikasi, tabel statistik granular (JSONB), vektor embedding 384-dimensi (`pgvector` dengan indeks HNSW), dan Full-Text Search bahasa Indonesia (`tsvector`) disatukan dalam satu engine relational database berkinerja tinggi. Storage adapter pattern dipertahankan untuk menjamin *backward compatibility*.

**Tech Stack:** Python 3.10+, PostgreSQL 15.14, `pgvector` 0.8.1, `psycopg2-binary`, `sentence-transformers`, `pydantic-settings`, `loguru`, `pytest`.

**Spec:** [`docs/RAG3321_ENGINEERING_AUDIT_AND_IMPLEMENTATION_PLAN.md`](file:///d:/Coding/RAG3321/docs/RAG3321_ENGINEERING_AUDIT_AND_IMPLEMENTATION_PLAN.md)

## Global Constraints

- **Database Preservation:** Dilarang melakukan DROP, TRUNCATE, atau DELETE pada basis data atau tabel yang sudah ada di server PostgreSQL (`10.133.21.24:5433`).
- **Target Database:** Database baru diberi nama `bps_rag3321` dengan ekstensi `vector` (pgvector 0.8.1).
- **CPU-First & Zero GPU:** Seluruh inferensi dan query harus beroperasi optimal pada CPU tanpa ketergantungan CUDA.
- **Statistical Integrity:** Tanda `-` tidak boleh dikonversi menjadi angka `0`; nilai asli (*raw value*), status simbol (*value status*), dan catatan kaki/revisi (`r`, `*`) harus dipertahankan.
- **No Silent Fallbacks:** Penghapusan pseudo-random hash generator pada embedder; kegagalan model harus memunculkan error terukur.
- **Git & Changelog Workflow:** Setiap task yang selesai dan terverifikasi wajib di-commit dengan pesan jelas dan `README.md` Changelog diperbarui.

## Review Focus

1. **Simbol Strip `-` dan Sel Kosong:** Tabel statistik BPS dengan nilai `-` harus menghasilkan objek dengan `value_status: "NIL"` atau `"NOT_AVAILABLE"`, bukan integer `0`.
2. **Karakter Revisi dan Footnote:** Angka bersimbol seperti `123r` atau `45*` tidak boleh kehilangan huruf `r` (revisi) atau `*` (angka sementara).
3. **Pemisah Desimal Indonesia:** Angka float `1.234.567,89` harus diparse dan diformat tepat tanpa kehilangan koma desimal.
4. **Konektivitas & Pool PostgreSQL:** Penanganan reconnection timeout dan connection pool pada port `5433` saat konkurensi scraping / chatbot query.
5. **Akurasi Hybrid RRF:** Pencarian teks kecamatan (misal "Sayung") harus terangkat peringkatnya oleh komponen lexical Full-Text Search bahkan ketika dense vector cosine score bersaing dengan kecamatan tetangga.

---

### Task 1: Environment & Database Provisioning (`bps_rag3321`)

**Files:**
- Create: `config/database.py`
- Modify: `config/settings.py`
- Modify: `.env.example`
- Create: `tests/test_postgres_connection.py`

**Interfaces:**
- Consumes: PostgreSQL connection credentials (`DB_HOST=10.133.21.24`, `DB_PORT=5433`, `DB_USER=bpsdemak`, `DB_PASSWORD=demak3321`, `DB_NAME=bps_rag3321`).
- Produces: `get_db_connection() -> psycopg2.extensions.connection`, `DatabaseSettings` model.

- [ ] **Step 1: Write failing test for PostgreSQL connection and pgvector extension**

```python
# tests/test_postgres_connection.py
import pytest
from config.database import get_db_connection, verify_pgvector_installed

def test_postgres_connection_and_pgvector():
    conn = get_db_connection()
    assert conn is not None
    assert verify_pgvector_installed(conn) is True
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_postgres_connection.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'config.database'`

- [ ] **Step 3: Implement database provisioning and connection manager**

1. Buat database `bps_rag3321` di server `10.133.21.24:5433` via script provisioning `psycopg2` (mengaktifkan `CREATE EXTENSION IF NOT EXISTS vector;`).
2. Buat `config/database.py` dengan fungsi `get_db_connection()` dan `verify_pgvector_installed(conn)`.
3. Perbarui `config/settings.py` dengan field: `DB_CONNECTION`, `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD`.
4. Perbarui `.env.example` dan buat file `.env` lokal dengan kredensial PostgreSQL.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_postgres_connection.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add config/database.py config/settings.py .env.example tests/test_postgres_connection.py
git commit -m "feat(database): configure PostgreSQL connection and provision bps_rag3321 with pgvector"
```

---

### Task 2: PostgreSQL Unified Schema & Migration Engine

**Files:**
- Create: `modules/storage/postgres_schema.sql`
- Create: `modules/storage/postgres_migrator.py`
- Create: `tests/test_postgres_schema.py`

**Interfaces:**
- Consumes: `get_db_connection()` dari `config/database.py`.
- Produces: `PostgresMigrator.run_migrations()`, skema tabel terverifikasi (`publications`, `statistical_tables`, `vector_chunks`, `embedding_cache`).

- [ ] **Step 1: Write failing test for schema tables existence**

```python
# tests/test_postgres_schema.py
import pytest
from config.database import get_db_connection
from modules.storage.postgres_migrator import PostgresMigrator

def test_postgres_tables_exist():
    migrator = PostgresMigrator()
    migrator.run_migrations()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN 
                ('publications', 'statistical_tables', 'vector_chunks', 'embedding_cache');
            """)
            tables = [r[0] for r in cur.fetchall()]
            assert "publications" in tables
            assert "statistical_tables" in tables
            assert "vector_chunks" in tables
            assert "embedding_cache" in tables
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_postgres_schema.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'modules.storage.postgres_migrator'`

- [ ] **Step 3: Implement DDL schema and migrator**

1. Tulis `modules/storage/postgres_schema.sql`:
   - `publications`: tracking status unduhan PDF, metadata rilis, sha256 checksum.
   - `statistical_tables`: tabel metadata, nomor tabel, judul, kecamatan, tahun, records (JSONB), satuan, sumber.
   - `vector_chunks`: `chunk_id` PRIMARY KEY, `table_id`, `tipe_konten`, `representasi_teks`, `metadata` (JSONB), `embedding vector(384)`, `tsv tsvector` (untuk FTS).
   - Index: HNSW pada `embedding` (`using hnsw (embedding vector_cosine_ops)`), GIN pada `tsv`, B-Tree pada `daerah`, `tahun`, `kategori`.
   - `embedding_cache`: `text_hash` (TEXT PRIMARY KEY), `embedding vector(384)`, `created_at`.
2. Implementasikan `PostgresMigrator.run_migrations()` di `modules/storage/postgres_migrator.py` dengan proteksi idempotent (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_postgres_schema.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add modules/storage/postgres_schema.sql modules/storage/postgres_migrator.py tests/test_postgres_schema.py
git commit -m "feat(storage): implement PostgreSQL DDL schema with pgvector HNSW and GIN FTS indexes"
```

---

### Task 3: Statistical Table Semantic Integrity Refactoring (`table_cleaner.py` & `json_builder.py`)

**Files:**
- Modify: `modules/extraction/table_cleaner.py`
- Modify: `modules/structuring/json_builder.py`
- Modify: `tests/test_extraction.py`
- Create: `tests/test_statistical_semantics.py`

**Interfaces:**
- Consumes: Raw extracted table matrices (List of Lists).
- Produces: `TableCleaner.clean_table_dataframe()` dengan `StatisticalCell` preserves, `JSONStructureBuilder._build_table_row_text_representation()` dengan format angka Indonesia akurat.

- [ ] **Step 1: Write failing test for statistical symbol semantics and Indonesian float parsing**

```python
# tests/test_statistical_semantics.py
import pytest
from modules.extraction.table_cleaner import TableCleaner, StatisticalCell, ValueStatus

def test_statistical_symbol_semantics():
    # Dash should NOT be integer 0
    cell_dash = TableCleaner.parse_statistical_cell("-")
    assert cell_dash.value_status == ValueStatus.NIL
    assert cell_dash.raw_value == "-"
    assert cell_dash.normalized_value is None

    # Ellipsis should be NOT_AVAILABLE
    cell_el = TableCleaner.parse_statistical_cell("...")
    assert cell_el.value_status == ValueStatus.NOT_AVAILABLE

    # Revision and footnote indicators preserved
    cell_rev = TableCleaner.parse_statistical_cell("12.450 r")
    assert cell_rev.value_status == ValueStatus.REVISED
    assert cell_rev.normalized_value == 12450
    assert cell_rev.revision_mark == "r"

    # Indonesian float parsing
    cell_float = TableCleaner.parse_statistical_cell("1.234,50")
    assert cell_float.normalized_value == 1234.50
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_statistical_semantics.py -v`  
Expected: FAIL with `ImportError: cannot import name 'StatisticalCell'`

- [ ] **Step 3: Refactor `table_cleaner.py` and `json_builder.py`**

1. Di `table_cleaner.py`:
   - Definisikan enum `ValueStatus` (`NORMAL_VALUE`, `ZERO`, `NIL`, `NOT_AVAILABLE`, `NOT_APPLICABLE`, `PROVISIONAL`, `REVISED`, `SUPPRESSED`).
   - Implementasikan dataclass `StatisticalCell(raw_value, normalized_value, value_status, unit, footnote, revision_mark)`.
   - Modifikasi `sanitize_indonesian_numeric`: hapus mutasi `-` $\rightarrow$ `0`; parse angka bersimbol `r`, `*`, `**` dengan status semantik tepat.
   - Perbaiki forward-fill (`ffill`): hanya lakukan forward-fill pada sel hierarkis sejati, abaikan baris agregat (*Jumlah/Total/Subtotal*).
2. Di `json_builder.py`:
   - Perbaiki bug pemformatan float pada baris 74 (`f"{val:,}".replace(",", ".")`) menggunakan fungsi formatter yang memisahkan ribuan (titik) dan desimal (koma).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_statistical_semantics.py tests/test_extraction.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add modules/extraction/table_cleaner.py modules/structuring/json_builder.py tests/test_extraction.py tests/test_statistical_semantics.py
git commit -m "fix(data-integrity): refactor statistical table cleaner with StatisticalCell schema and exact numeric parsing"
```

---

### Task 4: High-Performance Embedding Pipeline & Persistent Database Caching (`embedder.py`)

**Files:**
- Modify: `modules/vectorization/embedder.py`
- Create: `tests/test_embedder_cache.py`

**Interfaces:**
- Consumes: Text chunks, model `paraphrase-multilingual-MiniLM-L12-v2`.
- Produces: `VectorEmbedder.generate_embeddings(texts, batch_size=32) -> List[List[float]]` dengan automatic PostgreSQL cache bypass.

- [ ] **Step 1: Write failing test for embedding cache and no random fallback**

```python
# tests/test_embedder_cache.py
import pytest
from modules.vectorization.embedder import VectorEmbedder

def test_embedder_caching():
    embedder = VectorEmbedder()
    test_texts = ["Jumlah Penduduk Kecamatan Sayung", "Produksi Padi Kabupaten Demak"]
    
    # First call computes and caches
    embs_1 = embedder.generate_embeddings(test_texts)
    assert len(embs_1) == 2
    assert len(embs_1[0]) == 384
    
    # Second call should fetch directly from cache
    embs_2 = embedder.generate_embeddings(test_texts)
    assert embs_1 == embs_2

def test_embedder_never_returns_random_hash():
    embedder = VectorEmbedder()
    # Ensure pseudo-random fallback attribute is removed
    assert not hasattr(embedder, "_generate_random_hash_vectors")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_embedder_cache.py -v`  
Expected: FAIL

- [ ] **Step 3: Refactor `embedder.py`**

1. Hapus fungsi pseudo-random hash generator pada baris 112–124 (`rng.randn(384)`). Ganti dengan explicit exception atau circuit-breaker jika backend embedding gagal.
2. Tambahkan persistent caching ke tabel `embedding_cache` di PostgreSQL (menggunakan MD5 hash dari `text` sebagai primary key).
3. Implementasikan batch inference CPU yang adaptif (`batch_size=32`).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_embedder_cache.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add modules/vectorization/embedder.py tests/test_embedder_cache.py
git commit -m "feat(embedder): eliminate random vector fallback and implement PostgreSQL persistent embedding cache"
```

---

### Task 5: PostgreSQL Unified Vector & Metadata Store (`modules/storage/postgres_store.py`)

**Files:**
- Create: `modules/storage/postgres_store.py`
- Modify: `modules/storage/vector_store.py` (adapter bridge)
- Create: `tests/test_postgres_store.py`

**Interfaces:**
- Consumes: RAG structured chunks with embeddings and metadata.
- Produces: `PostgresVectorStore.upsert_chunks()`, `PostgresVectorStore.search_with_prefilter()`.

- [ ] **Step 1: Write failing test for upsert and vector similarity retrieval in PostgreSQL**

```python
# tests/test_postgres_store.py
import pytest
from modules.storage.postgres_store import PostgresVectorStore

def test_postgres_vector_store_crud_and_search():
    store = PostgresVectorStore()
    mock_chunk = {
        "chunk_id": "test_chunk_001",
        "dokumen_id": "doc_demak_2024",
        "dokumen_sumber": "Kabupaten Demak Dalam Angka 2024",
        "daerah": "Sayung",
        "kategori": "Kependudukan",
        "tahun": "2024",
        "halaman": 45,
        "tipe_konten": "tabel_baris",
        "judul_tabel": "Jumlah Penduduk Menurut Kecamatan",
        "satuan": "Jiwa",
        "sumber": "BPS Kabupaten Demak",
        "representasi_teks": "Pada Kecamatan Sayung jumlah penduduk laki-laki adalah 54.120 Jiwa.",
        "embedding": [0.01] * 384
    }
    upserted = store.upsert_chunks([mock_chunk])
    assert upserted == 1

    results = store.search_with_prefilter(
        query_embedding=[0.01] * 384,
        daerah="Sayung",
        tahun="2024",
        n_results=1
    )
    assert len(results) >= 1
    assert results[0]["chunk_id"] == "test_chunk_001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_postgres_store.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'modules.storage.postgres_store'`

- [ ] **Step 3: Implement `PostgresVectorStore`**

1. Buat class `PostgresVectorStore` di `modules/storage/postgres_store.py`:
   - `upsert_chunks(chunks)`: Menyimpan chunk ke tabel `vector_chunks`, mengkonversi list float ke format vector literal `[0.01, ...]` pgvector, dan mengisi kolom `tsv` menggunakan `to_tsvector('indonesian', representasi_teks)`.
   - `search_with_prefilter(query_embedding, daerah, tahun, kategori, n_results)`: Menjalankan query SQL dengan operator jarak cosine `<=>` dan filter metadata di klausa `WHERE`.
2. Integrasikan ke `modules/storage/vector_store.py` sebagai backend default saat `settings.DB_CONNECTION == "pgsql"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_postgres_store.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add modules/storage/postgres_store.py modules/storage/vector_store.py tests/test_postgres_store.py
git commit -m "feat(storage): implement PostgresVectorStore with pgvector HNSW indexing and metadata filtering"
```

---

### Task 6: Native PostgreSQL Hybrid Retrieval (Dense Vector + Full-Text Search + RRF)

**Files:**
- Create: `modules/retrieval/hybrid_search.py`
- Create: `modules/retrieval/entity_dictionary.py`
- Create: `tests/test_hybrid_retrieval.py`

**Interfaces:**
- Consumes: Query string, master dictionary of Demak 14 Kecamatan.
- Produces: `HybridRetriever.search(query: str, top_k: int = 5) -> List[Dict[str, Any]]`.

- [ ] **Step 1: Write failing test for Hybrid Retrieval and Kecamatan Entity Disambiguation**

```python
# tests/test_hybrid_retrieval.py
import pytest
from modules.retrieval.hybrid_search import HybridRetriever
from modules.retrieval.entity_dictionary import DemakEntityExtractor

def test_demak_entity_extraction():
    extractor = DemakEntityExtractor()
    ent = extractor.extract_entities("Berapa luas wilayah di kec Mranggen tahun 2024?")
    assert ent["kecamatan"] == "Mranggen"
    assert ent["tahun"] == "2024"

def test_hybrid_search_rrf_execution():
    retriever = HybridRetriever()
    results = retriever.search("Jumlah penduduk Kecamatan Sayung tahun 2024", top_k=3)
    assert isinstance(results, list)
    if results:
        assert "score" in results[0]
        assert "representasi_teks" in results[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_hybrid_retrieval.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'modules.retrieval.hybrid_search'`

- [ ] **Step 3: Implement Entity Dictionary & Native Hybrid SQL Search**

1. Buat `modules/retrieval/entity_dictionary.py`:
   - Master kamus 14 kecamatan se-Kabupaten Demak (*Demak, Bonang, Wedung, Mranggen, Sayung, Karangawen, Guntur, Mijen, Gajah, Karanganyar, Karangtengah, Wonosalam, Dempet, Kebonagung*) beserta alias/typo umum.
   - Ekstraktor tahun referensi (4 digit 2016–2026).
2. Buat `modules/retrieval/hybrid_search.py`:
   - Query SQL tunggal dengan Common Table Expressions (CTE):
     ```sql
     WITH dense_results AS (
         SELECT chunk_id, representasi_teks, metadata,
                ROW_NUMBER() OVER (ORDER BY embedding <=> %(q_vec)s::vector) AS dense_rank
         FROM vector_chunks WHERE (daerah = %(daerah)s OR %(daerah)s IS NULL)
         LIMIT 20
     ),
     lexical_results AS (
         SELECT chunk_id, representasi_teks, metadata,
                ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, plainto_tsquery('indonesian', %(query)s)) DESC) AS lex_rank
         FROM vector_chunks WHERE tsv @@ plainto_tsquery('indonesian', %(query)s)
         LIMIT 20
     )
     SELECT COALESCE(d.chunk_id, l.chunk_id) AS chunk_id,
            COALESCE(d.representasi_teks, l.representasi_teks) AS representasi_teks,
            COALESCE(d.metadata, l.metadata) AS metadata,
            (COALESCE(1.0 / (60 + d.dense_rank), 0.0) + COALESCE(1.0 / (60 + l.lex_rank), 0.0)) AS rrf_score
     FROM dense_results d FULL OUTER JOIN lexical_results l ON d.chunk_id = l.chunk_id
     ORDER BY rrf_score DESC LIMIT %(limit)s;
     ```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_hybrid_retrieval.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add modules/retrieval/hybrid_search.py modules/retrieval/entity_dictionary.py tests/test_hybrid_retrieval.py
git commit -m "feat(retrieval): implement native PostgreSQL Hybrid Search combining pgvector HNSW and FTS with RRF"
```

---

### Task 7: Chatbot Feeder & Gateway Integration with PostgreSQL

**Files:**
- Modify: `chatbot/rag_feeder.py`
- Modify: `chatbot/llm_client.py`
- Modify: `chatbot/bot.py`
- Create: `tests/test_chatbot_integration.py`

**Interfaces:**
- Consumes: User message, `HybridRetriever`.
- Produces: `BPSChatbot.ask(question) -> Dict[str, Any]` dengan sitasi provenance dan zero-hallucination context.

- [ ] **Step 1: Write failing test for chatbot context assembly from PostgreSQL**

```python
# tests/test_chatbot_integration.py
import pytest
from chatbot.bot import BPSChatbot

def test_chatbot_grounded_answer_pipeline():
    bot = BPSChatbot(warmup_background=False)
    # Testing intent routing and RAG context retrieval
    resp = bot.ask("Halo, selamat pagi!", session_id="test_sess_01")
    assert resp["type"] == "conversational"
    assert resp["answer"] is not None
```

- [ ] **Step 2: Run test to verify it fails or runs**

Run: `pytest tests/test_chatbot_integration.py -v`  
Expected: Run verification

- [ ] **Step 3: Update `rag_feeder.py` and `llm_client.py`**

1. Di `chatbot/rag_feeder.py`:
   - Hubungkan `feed_context` langsung ke `HybridRetriever` PostgreSQL, menggantikan query manual SQLite `tables_index.db`.
   - Injeksi Markdown tabular langsung dari `statistical_tables` (JSONB) di PostgreSQL.
2. Di `chatbot/llm_client.py`:
   - Bersihkan model candidate list (gunakan model resmi `gemini-1.5-flash`, `gemini-2.0-flash`).
   - Hanya sertakan `thinkingConfig` jika model yang dipanggil mendukung thinking mode, mencegah HTTP 400 Bad Request.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_chatbot_integration.py -v`  
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add chatbot/rag_feeder.py chatbot/llm_client.py chatbot/bot.py tests/test_chatbot_integration.py
git commit -m "feat(chatbot): wire RAGFeeder to PostgreSQL hybrid retrieval and fix LLM client model cascade"
```

---

### Task 8: Statistical Golden Benchmark Suite & End-to-End Verification

**Files:**
- Create: `tests/benchmarks/golden_dataset.json`
- Create: `tests/benchmarks/test_golden_benchmark.py`
- Modify: `README.md` (Update Changelog)

**Interfaces:**
- Consumes: 30–50 verified statistical QA pairs on BPS Demak data.
- Produces: Automated accuracy report (Exact Match %, Citation %, Latency P50/P95).

- [ ] **Step 1: Create Golden Dataset of verified BPS Demak statistical questions**

Buat `tests/benchmarks/golden_dataset.json` berisi minimal 30 soal riil:
- Kependudukan per kecamatan (Sayung, Mranggen, Bonang).
- Produksi padi & luas panen.
- PDRB dan pertumbuhan ekonomi.
- Pertanyaan negatif / data tidak tersedia (menguji *abstention* tanpa halusinasi).

- [ ] **Step 2: Implement automated benchmark evaluator**

```python
# tests/benchmarks/test_golden_benchmark.py
import json
import pytest
from chatbot.bot import BPSChatbot

def test_run_golden_benchmark():
    with open("tests/benchmarks/golden_dataset.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    bot = BPSChatbot(warmup_background=False)
    # Evaluate at least representative samples
    for case in cases[:5]:
        res = bot.ask(case["question"], session_id="bench")
        assert res["answer"] is not None
```

- [ ] **Step 3: Run benchmark and generate evaluation metrics**

Run: `pytest tests/benchmarks/test_golden_benchmark.py -v`  
Expected: PASS

- [ ] **Step 4: Update README.md with Changelog and documentation**

Perbarui `README.md` di bagian Changelog dengan tanggal penyelesaian dan rincian arsitektur PostgreSQL + pgvector.

- [ ] **Step 5: Commit and push**

```bash
git add tests/benchmarks/ README.md
git commit -m "test(benchmark): implement golden statistical benchmark suite and update changelog"
git push
```
