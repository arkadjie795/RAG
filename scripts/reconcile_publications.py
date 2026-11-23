import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()
from config.database import get_db_cursor

# 1. Disk PDFs
pdf_root = Path("data_publikasi/demak")
disk_pdfs = list(pdf_root.rglob("*.pdf"))
print(f"Total Disk PDFs: {len(disk_pdfs)}")
years_disk = {}
for p in disk_pdfs:
    yr = p.parts[2] if len(p.parts) > 2 else "Unknown"
    years_disk[yr] = years_disk.get(yr, 0) + 1

# 2. Database Publications
with get_db_cursor() as cur:
    cur.execute("SELECT count(*) FROM publications;")
    db_total = cur.fetchone()[0]
    
    cur.execute("SELECT download_status, count(*) FROM publications GROUP BY download_status;")
    status_counts = cur.fetchall()
    
    cur.execute("SELECT extraction_status, count(*) FROM publications GROUP BY extraction_status;")
    extract_counts = cur.fetchall()
    
    cur.execute("SELECT sum(total_tables_extracted), sum(total_chunks_indexed) FROM publications;")
    sums = cur.fetchone()
    
    cur.execute("SELECT substring(release_date from 1 for 4) as yr, count(*) FROM publications GROUP BY yr ORDER BY yr;")
    years_db = cur.fetchall()

print(f"Total Publications in DB: {db_total}")
print("Download status in DB:", status_counts)
print("Extraction status in DB:", extract_counts)
print(f"Total tables extracted across publications: {sums[0]}")
print(f"Total chunks indexed across publications: {sums[1]}")
print("\nDB breakdown by release year:")
for y, cnt in years_db:
    print(f"  {y}: {cnt}")

print("\nDisk breakdown by folder year:")
for y in sorted(years_disk.keys()):
    print(f"  {y}: {years_disk[y]}")
