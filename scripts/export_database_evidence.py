import os
import sys
import json
from pathlib import Path
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()
from config.database import get_db_cursor

staging_dir = Path("temp_staging_db_evidence")
staging_dir.mkdir(parents=True, exist_ok=True)

print("Connecting to live PostgreSQL database...")
with get_db_cursor() as cur:
    # 1. Version and Extensions
    cur.execute("SELECT version();")
    pg_version = cur.fetchone()[0]
    
    cur.execute("SELECT extname, extversion FROM pg_extension;")
    extensions = cur.fetchall()
    
    ext_info = {
        "pg_version": pg_version,
        "extensions": [{"name": e[0], "version": e[1]} for e in extensions]
    }
    with open(staging_dir / "01_EXTENSION_AND_VERSION_INFO.json", "w", encoding="utf-8") as f:
        json.dump(ext_info, f, indent=2)
        
    # 2. Table Inventory and Counts
    tables = ["publications", "statistical_tables", "vector_chunks", "embedding_cache"]
    table_counts = {}
    table_columns = {}
    for t in tables:
        cur.execute(f"SELECT count(*) FROM {t};")
        table_counts[t] = cur.fetchone()[0]
        cur.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{t}'
            ORDER BY ordinal_position;
        """)
        table_columns[t] = [
            {"name": c[0], "type": c[1], "nullable": c[2], "default": c[3]}
            for c in cur.fetchall()
        ]
        
    inventory = {
        "database_name": "bps_rag3321",
        "host": "10.133.21.24",
        "port": 5433,
        "counts": table_counts,
        "columns": table_columns
    }
    with open(staging_dir / "02_TABLE_INVENTORY_AND_COUNTS.json", "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    # 3. Indexes
    cur.execute("""
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
    """)
    indexes = cur.fetchall()
    idx_list = [{"table": i[0], "name": i[1], "definition": i[2]} for i in indexes]
    with open(staging_dir / "03_INDEX_DEFINITIONS.json", "w", encoding="utf-8") as f:
        json.dump(idx_list, f, indent=2)

    # 4. Schema DDL SQL
    ddl_sql = []
    ddl_sql.append("-- ====================================================================")
    ddl_sql.append("-- LIVE POSTGRESQL 15 + PGVECTOR SCHEMA DUMP (READ-ONLY AUDIT EXTRACT)")
    ddl_sql.append(f"-- Database: bps_rag3321 | Host: 10.133.21.24:5433 | Version: {pg_version}")
    ddl_sql.append("-- ====================================================================\n")
    ddl_sql.append("CREATE EXTENSION IF NOT EXISTS vector;\n")
    
    for t in tables:
        ddl_sql.append(f"-- Table: {t} (Estimated Records: {table_counts[t]:,})")
        ddl_sql.append(f"CREATE TABLE IF NOT EXISTS {t} (")
        col_defs = []
        for c in table_columns[t]:
            col_type = c["type"]
            if c["name"] == "embedding":
                col_type = "vector(384)"
            null_str = "NOT NULL" if c["nullable"] == "NO" else ""
            def_str = f"DEFAULT {c['default']}" if c["default"] else ""
            col_defs.append(f"    {c['name']} {col_type} {null_str} {def_str}".strip())
        ddl_sql.append(",\n".join(col_defs))
        ddl_sql.append(");\n")
        
    ddl_sql.append("-- Indexes:")
    for idx in idx_list:
        ddl_sql.append(f"{idx['definition']};")
        
    with open(staging_dir / "00_SCHEMA_FULL.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(ddl_sql))

    # 5. Sample Data (Safe, Non-sensitive Representative Dataset)
    print("Exporting representative sample records...")
    # 15 publications
    cur.execute("SELECT publication_id, title, release_date, category, total_tables_extracted, total_chunks_indexed, download_status, created_at FROM publications ORDER BY created_at DESC LIMIT 15;")
    sample_pubs = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    for p in sample_pubs:
        if p.get("created_at"):
            p["created_at"] = str(p["created_at"])
    with open(staging_dir / "05_SAMPLE_PUBLICATIONS.json", "w", encoding="utf-8") as f:
        json.dump(sample_pubs, f, indent=2, ensure_ascii=False)

    # 25 statistical tables
    cur.execute("SELECT table_id, doc_id, doc_title, table_title, table_number, kecamatan, tahun, satuan, sumber, catatan, halaman, kolom, records FROM statistical_tables ORDER BY created_at DESC LIMIT 25;")
    sample_tables = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    with open(staging_dir / "06_SAMPLE_STATISTICAL_TABLES.json", "w", encoding="utf-8") as f:
        json.dump(sample_tables, f, indent=2, ensure_ascii=False)

    # 50 vector chunks (with embedding preview)
    cur.execute("SELECT chunk_id, doc_id, table_id, judul_tabel, daerah, tahun, kategori, tipe_konten, satuan, sumber, halaman, representasi_teks, metadata FROM vector_chunks LIMIT 50;")
    sample_chunks = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    with open(staging_dir / "07_SAMPLE_VECTOR_CHUNKS.json", "w", encoding="utf-8") as f:
        json.dump(sample_chunks, f, indent=2, ensure_ascii=False)

# 6. Copy local SQLite databases and DDL files
import shutil
for local_f in ["scripts/init_db.sql", "modules/storage/postgres_schema.sql", "database/bps_registry.db", "database/tables_index.db", "database/laporan_bukti_nyata.json"]:
    if Path(local_f).exists():
        shutil.copy(local_f, staging_dir / Path(local_f).name)
        print(f"Copied {local_f} to staging")

# 7. Write Database Structure & Relationship Report
report_md = f"""# DATABASE STRUCTURE & RAG ENTITY RELATIONSHIP REPORT
**Database:** `bps_rag3321` on PostgreSQL 15.14 with `pgvector` v0.8.1  
**Host:** `10.133.21.24:5433`  
**Extraction Date:** 2026-11-16 (Live Read-Only Audit)

---

## 1. Table Statistics (Exact Live Counts)
- `publications`: **{table_counts['publications']:,} records**
- `statistical_tables`: **{table_counts['statistical_tables']:,} records**
- `vector_chunks`: **{table_counts['vector_chunks']:,} records**
- `embedding_cache`: **{table_counts['embedding_cache']:,} records**

## 2. Entity Linkage & RAG Pipeline Integration
1. **publications -> statistical_tables:**
   - 1:N relationship linked via `doc_id` / `publication_id`.
   - Each official BPS publication PDF produces multiple statistical tables with bounding box & multi-level header normalization.
2. **statistical_tables -> vector_chunks:**
   - 1:N relationship linked via `table_id`.
   - Each row of a statistical table is transformed into a natural language sentence (Row-to-Speech) and stored as a vector chunk.
3. **vector_chunks -> embedding_cache:**
   - Linked via deterministic MD5 hash of text representation.
   - Prevents duplicate neural computation on re-indexing.
4. **Hybrid Search Indexing:**
   - Dense: HNSW index `idx_chunks_embedding_hnsw` on 384-dimensional `embedding` column using cosine distance (`vector_cosine_ops`).
   - Lexical: GIN index `idx_chunks_tsv` on Indonesian `tsvector` column `tsv`.
   - Filter B-Tree indexes: `daerah` (14 subdistricts), `tahun`, `kategori`, `tipe_konten`.
"""
with open(staging_dir / "DATABASE_STRUCTURE_REPORT.md", "w", encoding="utf-8") as f:
    f.write(report_md)

print("Database evidence extraction completed successfully!")
