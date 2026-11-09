-- ==============================================================================
-- BPS RAG3321 Unified PostgreSQL & pgvector Schema
-- ==============================================================================

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Publication Registry Table
CREATE TABLE IF NOT EXISTS publications (
    publication_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    release_date TEXT,
    category TEXT DEFAULT 'Umum',
    pdf_url TEXT,
    local_file_path TEXT,
    file_size_bytes BIGINT DEFAULT 0,
    checksum_sha256 TEXT,
    download_status TEXT DEFAULT 'PENDING',
    extraction_status TEXT DEFAULT 'PENDING',
    total_tables_extracted INTEGER DEFAULT 0,
    total_chunks_indexed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pub_status ON publications (download_status, extraction_status);
CREATE INDEX IF NOT EXISTS idx_pub_category ON publications (category);

-- 2. Statistical Tables Granular Storage Table
CREATE TABLE IF NOT EXISTS statistical_tables (
    table_id TEXT PRIMARY KEY,
    doc_id TEXT REFERENCES publications(publication_id) ON DELETE CASCADE,
    doc_title TEXT,
    table_number TEXT,
    table_title TEXT NOT NULL,
    halaman INTEGER DEFAULT 1,
    kecamatan TEXT DEFAULT 'Kabupaten Demak',
    tahun TEXT,
    satuan TEXT DEFAULT 'N/A',
    sumber TEXT DEFAULT 'BPS Kabupaten Demak',
    catatan TEXT,
    kolom JSONB DEFAULT '[]'::jsonb,
    records JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_st_doc_id ON statistical_tables (doc_id);
CREATE INDEX IF NOT EXISTS idx_st_kecamatan ON statistical_tables (kecamatan);
CREATE INDEX IF NOT EXISTS idx_st_tahun ON statistical_tables (tahun);

-- 3. Vector Chunks Storage with pgvector & Full-Text Search
CREATE TABLE IF NOT EXISTS vector_chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT,
    table_id TEXT,
    tipe_konten TEXT DEFAULT 'tabel_baris',
    daerah TEXT DEFAULT 'Kabupaten Demak',
    kategori TEXT DEFAULT 'Umum',
    tahun TEXT,
    halaman INTEGER DEFAULT 1,
    judul_tabel TEXT,
    satuan TEXT DEFAULT 'N/A',
    sumber TEXT DEFAULT 'BPS Kabupaten Demak',
    representasi_teks TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(384),
    tsv tsvector
);

-- HNSW Vector Index for Cosine Similarity Search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
ON vector_chunks USING hnsw (embedding vector_cosine_ops);

-- GIN Index for Indonesian Lexical Full-Text Search
CREATE INDEX IF NOT EXISTS idx_chunks_tsv 
ON vector_chunks USING gin (tsv);

-- B-Tree Filter Indexes
CREATE INDEX IF NOT EXISTS idx_chunks_daerah ON vector_chunks (daerah);
CREATE INDEX IF NOT EXISTS idx_chunks_tahun ON vector_chunks (tahun);
CREATE INDEX IF NOT EXISTS idx_chunks_kategori ON vector_chunks (kategori);
CREATE INDEX IF NOT EXISTS idx_chunks_tipe ON vector_chunks (tipe_konten);

-- 4. Persistent Embedding Cache Table
CREATE TABLE IF NOT EXISTS embedding_cache (
    text_hash TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emb_cache_model ON embedding_cache (model_name);
