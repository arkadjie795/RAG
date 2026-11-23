import os
import sys
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()
from config.database import get_db_cursor

try:
    with get_db_cursor() as cur:
        cur.execute("SELECT version();")
        pg_ver = cur.fetchone()[0]
        print(f"PG_VERSION: {pg_ver}")
        
        cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
        ext = cur.fetchone()
        print(f"PGVECTOR: {ext[1] if ext else 'NOT FOUND'}")
        
        cur.execute("SELECT count(*) FROM vector_chunks;")
        chunks = cur.fetchone()[0]
        print(f"VECTOR_CHUNKS_COUNT: {chunks}")
        
        cur.execute("SELECT count(*) FROM statistical_tables;")
        tables = cur.fetchone()[0]
        print(f"STATISTICAL_TABLES_COUNT: {tables}")
        
        cur.execute("SELECT count(*) FROM embedding_cache;")
        cache = cur.fetchone()[0]
        print(f"EMBEDDING_CACHE_COUNT: {cache}")
        
        cur.execute("SELECT count(*) FROM publications;")
        pubs = cur.fetchone()[0]
        print(f"PUBLICATIONS_COUNT: {pubs}")
        
        # Check index types
        cur.execute("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'vector_chunks';
        """)
        indexes = cur.fetchall()
        print("\nINDEXES ON vector_chunks:")
        for idx in indexes:
            print(f" - {idx[0]}: {idx[1]}")
            
        # Check dimensionality of embedding column
        cur.execute("""
            SELECT atttypmod 
            FROM pg_attribute 
            WHERE attrelid = 'vector_chunks'::regclass AND attname = 'embedding';
        """)
        dim = cur.fetchone()
        print(f"\nEMBEDDING_DIMENSION_TYPMOD: {dim[0] if dim else 'Unknown'}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
