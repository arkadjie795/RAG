import os
import sys
import ast
import json
from pathlib import Path

# Ensure root is in path
sys.path.insert(0, os.path.abspath("."))

facts = {}

# 1. Requirements
req_file = Path("requirements.txt")
if req_file.exists():
    with open(req_file, "r", encoding="utf-8") as f:
        facts["requirements"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# 2. Frontend package.json
pkg_file = Path("frontend/package.json")
if pkg_file.exists():
    with open(pkg_file, "r", encoding="utf-8") as f:
        pkg_data = json.load(f)
        facts["frontend_deps"] = pkg_data.get("dependencies", {})
        facts["frontend_dev_deps"] = pkg_data.get("devDependencies", {})

# 3. Source folders scan
source_folders = ["chatbot", "api", "modules", "frontend/src", "scripts", "tests"]
code_files = []

for s_folder in source_folders:
    if not os.path.exists(s_folder):
        continue
    for root, dirs, files in os.walk(s_folder):
        dirs[:] = [d for d in dirs if d not in {"node_modules", "__pycache__", ".git", "dist"}]
        for file in files:
            if file.endswith((".py", ".vue", ".js", ".ts", ".css", ".html")):
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 2 * 1024 * 1024:
                        continue
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        loc = len(lines)
                except Exception:
                    loc = 0
                
                classes = []
                functions = []
                if file.endswith(".py"):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                classes.append(node.name)
                            elif isinstance(node, ast.FunctionDef):
                                functions.append(node.name)
                    except Exception:
                        pass
                
                code_files.append({
                    "path": file_path.replace("\\", "/"),
                    "loc": loc,
                    "classes": classes,
                    "functions": functions
                })

facts["code_inventory"] = code_files

# 4. Storage sizes and file counts
disk_stats = {}

def get_dir_stats(path_str):
    p = Path(path_str)
    if not p.exists():
        return {"exists": False, "files": 0, "size_mb": 0}
    count = 0
    total_bytes = 0
    try:
        for root, dirs, files in os.walk(path_str):
            for f in files:
                count += 1
                try:
                    total_bytes += os.path.getsize(os.path.join(root, f))
                except Exception:
                    pass
    except Exception:
        pass
    return {"exists": True, "files": count, "size_mb": round(total_bytes / (1024 * 1024), 2)}

folders_to_check = [
    "data_publikasi",
    "database",
    "database/chroma_store",
    "database/documents",
    "database/tables",
    "chatbot/static"
]

for folder in folders_to_check:
    disk_stats[folder] = get_dir_stats(folder)

# Check single files
for single_file in [
    "database/bps_documents.json",
    "RAG_BPS_DEMAK_AUDIT_EXPORT/PDF_PUBLICATIONS_CATALOG.json"
]:
    sf = Path(single_file)
    if sf.exists():
        disk_stats[single_file] = {
            "exists": True,
            "size_mb": round(sf.stat().st_size / (1024 * 1024), 2)
        }
    else:
        disk_stats[single_file] = {"exists": False, "size_mb": 0}

facts["disk_stats"] = disk_stats

# 5. Database live inspection via psycopg2
try:
    import psycopg2
    from modules.core.config import settings
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        connect_timeout=5
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]
    
    table_stats = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        count = cur.fetchone()[0]
        
        cur.execute(f"""
            SELECT column_name, data_type, character_maximum_length, is_nullable
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
        
        table_stats[t] = {
            "row_count": count,
            "columns": [{"name": c[0], "type": c[1], "len": c[2], "nullable": c[3]} for c in cols],
            "indexes": [{"name": i[0], "def": i[1]} for i in idxs]
        }
    
    facts["db_stats"] = table_stats
    
    cur.execute("SELECT extname, extversion FROM pg_extension;")
    facts["pg_extensions"] = cur.fetchall()
    
    cur.execute("SELECT version();")
    facts["pg_version"] = cur.fetchone()[0]
    
    cur.close()
    conn.close()
except Exception as e:
    facts["db_error"] = str(e)

with open("scripts/audit_workspace_facts.json", "w", encoding="utf-8") as f:
    json.dump(facts, f, indent=2)

print("SUCCESS: Real audit facts collected cleanly!")
