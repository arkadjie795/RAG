import os
import sys
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()
from config.database import get_db_cursor

with get_db_cursor() as cur:
    print("=== DATABASE INTEGRITY & CONSISTENCY AUDIT ===")
    
    # 1. Null embeddings or tsv
    cur.execute("SELECT count(*) FROM vector_chunks WHERE embedding IS NULL;")
    null_emb = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM vector_chunks WHERE tsv IS NULL;")
    null_tsv = cur.fetchone()[0]
    print(f"Null embeddings in vector_chunks: {null_emb}")
    print(f"Null tsv in vector_chunks: {null_tsv}")
    
    # 2. Duplicate chunk_id
    cur.execute("SELECT chunk_id, count(*) FROM vector_chunks GROUP BY chunk_id HAVING count(*) > 1;")
    dupe_chunks = cur.fetchall()
    print(f"Duplicate chunk_id count: {len(dupe_chunks)}")
    
    # 3. Orphan chunks (chunks whose doc_id is not in publications)
    cur.execute("""
        SELECT count(*) FROM vector_chunks vc
        LEFT JOIN publications p ON vc.doc_id = p.publication_id
        WHERE p.publication_id IS NULL;
    """)
    orphan_chunks = cur.fetchone()[0]
    print(f"Orphan chunks (no matching publication_id): {orphan_chunks}")
    
    # 4. Orphan tables (tables whose doc_id is not in publications)
    cur.execute("""
        SELECT count(*) FROM statistical_tables st
        LEFT JOIN publications p ON st.doc_id = p.publication_id
        WHERE p.publication_id IS NULL;
    """)
    orphan_tables = cur.fetchone()[0]
    print(f"Orphan tables (no matching publication_id): {orphan_tables}")
    
    # 5. Null or empty text representation
    cur.execute("SELECT count(*) FROM vector_chunks WHERE representasi_teks IS NULL OR trim(representasi_teks) = '';")
    empty_text = cur.fetchone()[0]
    print(f"Empty text representations in vector_chunks: {empty_text}")
    
    # 6. JSONB validity
    cur.execute("SELECT count(*) FROM statistical_tables WHERE jsonb_typeof(records) != 'array';")
    invalid_records = cur.fetchone()[0]
    print(f"Invalid JSONB records in statistical_tables: {invalid_records}")
