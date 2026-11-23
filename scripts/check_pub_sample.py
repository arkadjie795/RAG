import os
import sys
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()
from config.database import get_db_cursor

with get_db_cursor() as cur:
    cur.execute("SELECT publication_id, title, release_date, total_tables_extracted, total_chunks_indexed, created_at FROM publications ORDER BY created_at DESC LIMIT 15;")
    rows = cur.fetchall()
    print("PUBLICATIONS SAMPLE (LATEST 15):")
    for r in rows:
        print(f" - {r[0]}: {r[1]} (date: {r[2]}, tables: {r[3]}, chunks: {r[4]}, created: {r[5]})")
        
    cur.execute("SELECT min(created_at), max(created_at) FROM publications;")
    print("Publications created range:", cur.fetchone())
    
    cur.execute("SELECT count(*) FROM publications WHERE total_chunks_indexed > 0;")
    print("Publications with indexed chunks:", cur.fetchone()[0])
