import os
from pathlib import Path

root = Path(".")
dir_sizes = {}
dir_files = {}

for p in root.iterdir():
    if p.name.startswith(".git") or p.name == "RAG_BPS_DEMAK_AUDIT_EXPORT":
        continue
    try:
        if p.is_dir():
            total_size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            file_count = sum(1 for f in p.rglob("*") if f.is_file())
            dir_sizes[p.name] = total_size
            dir_files[p.name] = file_count
        else:
            dir_sizes[p.name] = p.stat().st_size
            dir_files[p.name] = 1
    except Exception as e:
        print(f"Error reading {p}: {e}")

print(f"{'Name':35} | {'Files':8} | {'Size (MB)':10}")
print("-" * 60)
total_bytes = 0
total_all_files = 0
for k, v in sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True):
    print(f"{k:35} | {dir_files[k]:8} | {v / (1024*1024):10.2f} MB")
    total_bytes += v
    total_all_files += dir_files[k]

print("-" * 60)
print(f"{'TOTAL (excluding .git)':35} | {total_all_files:8} | {total_bytes / (1024*1024):10.2f} MB")
