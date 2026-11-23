import os
import sys
import sqlite3
import json
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))
from config.settings import settings

report_data = {}

# ================= 1. SQLITE INSPECTION =================
sqlite_info = {}
sqlite_files = []
for root, dirs, files in os.walk("."):
    if any(x in root for x in [".venv", "venv", "node_modules", ".git"]):
        continue
    for f in files:
        if f.endswith((".db", ".sqlite", ".sqlite3")):
            sqlite_files.append(os.path.join(root, f))

for db_file in sqlite_files:
    db_rel = os.path.relpath(db_file).replace("\\", "/")
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        t_data = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t};")
            count = cur.fetchone()[0]
            cur.execute(f"PRAGMA table_info({t});")
            cols = cur.fetchall()
            cur.execute(f"PRAGMA index_list({t});")
            idxs = cur.fetchall()
            t_data[t] = {
                "count": count,
                "columns": [{"cid": c[0], "name": c[1], "type": c[2], "notnull": c[3], "pk": c[5]} for c in cols],
                "indexes": idxs
            }
        conn.close()
        sqlite_info[db_rel] = {
            "size_bytes": os.path.getsize(db_file),
            "tables": t_data
        }
    except Exception as e:
        sqlite_info[db_rel] = {"error": str(e)}

report_data["sqlite"] = sqlite_info

# ================= 2. CHROMADB INSPECTION =================
chroma_info = {}
chroma_path = "database/chroma_store"
if os.path.exists(chroma_path):
    chroma_info["exists"] = True
    chroma_info["size_mb"] = round(sum(os.path.getsize(os.path.join(r, f)) for r, d, files in os.walk(chroma_path) for f in files) / (1024*1024), 2)
    try:
        import chromadb
        client = chromadb.PersistentClient(path=chroma_path)
        collections = client.list_collections()
        colls_data = {}
        for col in collections:
            colls_data[col.name] = {
                "count": col.count(),
                "metadata": col.metadata
            }
        chroma_info["collections"] = colls_data
    except Exception as e:
        chroma_info["load_error"] = str(e)
else:
    chroma_info["exists"] = False

report_data["chroma"] = chroma_info

# ================= 3. POSTGRESQL INSPECTION =================
pg_info = {}
try:
    import psycopg2
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_DATABASE,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
        connect_timeout=settings.DB_TIMEOUT
    )
    cur = conn.cursor()
    
    cur.execute("SELECT version();")
    pg_info["version"] = cur.fetchone()[0]
    
    cur.execute("SELECT extname, extversion FROM pg_extension;")
    pg_info["extensions"] = cur.fetchall()
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]
    
    t_stats = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cur.fetchone()[0]
        
        cur.execute(f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = '{t}'
            ORDER BY ordinal_position;
        """)
        cols = cur.fetchall()
        
        cur.execute(f"""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE schemaname = 'public' AND tablename = '{t}'
            ORDER BY indexname;
        """)
        idxs = cur.fetchall()
        
        t_stats[t] = {
            "count": cnt,
            "columns": [{"name": c[0], "type": c[1], "max_len": c[2], "nullable": c[3], "default": c[4]} for c in cols],
            "indexes": [{"name": i[0], "def": i[1]} for i in idxs]
        }
    pg_info["tables"] = t_stats
    
    cur.close()
    conn.close()
except Exception as e:
    pg_info["error"] = str(e)

report_data["postgresql"] = pg_info

# ================= 4. DATASET & DISK INSPECTION =================
data_info = {}
pdf_files = []
pdf_years = {}
data_dir = "data_publikasi"
if os.path.exists(data_dir):
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            if f.endswith(".pdf"):
                full_p = os.path.join(root, f)
                pdf_files.append(full_p)
                # check year from path
                parts = Path(full_p).parts
                year = "unknown"
                for p in parts:
                    if p.isdigit() and len(p) == 4 and (2000 <= int(p) <= 2030):
                        year = p
                        break
                pdf_years[year] = pdf_years.get(year, 0) + 1

data_info["total_pdfs"] = len(pdf_files)
data_info["pdf_years_breakdown"] = dict(sorted(pdf_years.items()))
data_info["total_pdf_size_mb"] = round(sum(os.path.getsize(p) for p in pdf_files) / (1024*1024), 2) if pdf_files else 0

# Check tables folder
tables_dir = "database/tables"
if os.path.exists(tables_dir):
    json_tables = [os.path.join(r, f) for r, d, files in os.walk(tables_dir) for f in files if f.endswith(".json")]
    data_info["total_json_tables"] = len(json_tables)
    data_info["total_json_tables_size_mb"] = round(sum(os.path.getsize(p) for p in json_tables) / (1024*1024), 2) if json_tables else 0

# Check documents folder
docs_dir = "database/documents"
if os.path.exists(docs_dir):
    json_docs = [os.path.join(r, f) for r, d, files in os.walk(docs_dir) for f in files if f.endswith(".json")]
    data_info["total_json_documents"] = len(json_docs)
    data_info["total_json_documents_size_mb"] = round(sum(os.path.getsize(p) for p in json_docs) / (1024*1024), 2) if json_docs else 0

report_data["dataset_stats"] = data_info

# ================= 5. API ROUTE INSPECTION =================
api_info = []
try:
    from chatbot.api import app
    for route in app.routes:
        if hasattr(route, "path"):
            methods = list(route.methods) if hasattr(route, "methods") else ["GET"]
            api_info.append({
                "path": route.path,
                "name": getattr(route, "name", ""),
                "methods": methods
            })
except Exception as e:
    api_info.append({"error": str(e)})

report_data["api_routes"] = api_info

with open("scripts/full_system_audit_data.json", "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2)

print("AUDIT INSPECTION COMPLETED SUCCESSFULLY!")
