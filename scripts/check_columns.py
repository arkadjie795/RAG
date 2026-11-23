import os
import sys
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()
from config.database import get_db_cursor

with get_db_cursor() as cur:
    for table in ['publications', 'statistical_tables', 'vector_chunks', 'embedding_cache']:
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}';
        """)
        cols = cur.fetchall()
        print(f"\nTABLE {table}:")
        for c in cols:
            print(f"  - {c[0]}: {c[1]}")
