import os
import sys
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()
from config.database import get_db_cursor

with get_db_cursor() as cur:
    cur.execute("SELECT pub_id, title, release_date, total_tables FROM publications ORDER BY created_at DESC LIMIT 15;")
    rows = cur.fetchall()
    print("PUBLICATIONS SAMPLE:")
    for r in rows:
        print(f" - {r[0]}: {r[1]} (date: {r[2]}, tables: {r[3]})")
        
    cur.execute("SELECT count(DISTINCT table_id) FROM statistical_tables;")
    distinct_tables = cur.fetchone()[0]
    print(f"\nDISTINCT table_id: {distinct_tables}")
    
    cur.execute("SELECT min(created_at), max(created_at) FROM vector_chunks;")
    t_min, t_max = cur.fetchone()
    print(f"vector_chunks timestamps: {t_min} to {t_max}")
