import json

with open("scripts/full_system_audit_data.json", "r", encoding="utf-8") as f:
    d = json.load(f)

print("=== 1. SQLITE DATABASES ===")
for db, v in d.get("sqlite", {}).items():
    print(f"Path: {db} (Size: {v.get('size_bytes', 0):,} bytes)")
    for t, tv in v.get("tables", {}).items():
        print(f"  Table '{t}': {tv['count']} rows")
        cols = [c['name'] for c in tv.get('columns', [])]
        print(f"    Columns ({len(cols)}): {cols}")

print("\n=== 2. CHROMADB STATUS ===")
chroma = d.get("chroma", {})
print(f"Exists: {chroma.get('exists')}, Size: {chroma.get('size_mb')} MB")
if "collections" in chroma:
    for c_name, c_data in chroma["collections"].items():
        print(f"  Collection '{c_name}': {c_data['count']} embeddings, metadata: {c_data.get('metadata')}")

print("\n=== 3. POSTGRESQL 15.14 + PGVECTOR ===")
pg = d.get("postgresql", {})
print("Version:", pg.get("version"))
print("Extensions:", pg.get("extensions"))
for t, tv in pg.get("tables", {}).items():
    print(f"  Table '{t}': {tv['count']:,} rows, {len(tv['columns'])} columns, {len(tv['indexes'])} indexes")
    cols = [f"{c['name']} ({c['type']})" for c in tv.get('columns', [])]
    print(f"    Columns: {', '.join(cols[:8])}...")

print("\n=== 4. DATASET & PHYSICAL ARTIFACTS ===")
ds = d.get("dataset_stats", {})
print("Total PDFs in data_publikasi:", ds.get("total_pdfs"))
print("Total PDF size:", ds.get("total_pdf_size_mb"), "MB")
print("PDF Years breakdown:", ds.get("pdf_years_breakdown"))
print("Total JSON tables on disk:", ds.get("total_json_tables"), f"({ds.get('total_json_tables_size_mb')} MB)")
print("Total JSON documents on disk:", ds.get("total_json_documents"), f"({ds.get('total_json_documents_size_mb')} MB)")

print("\n=== 5. FASTAPI ROUTES ===")
routes = d.get("api_routes", [])
print(f"Total API Routes: {len(routes)}")
for r in routes:
    print(f"  {','.join(r.get('methods', [])):<12} {r.get('path')}")
