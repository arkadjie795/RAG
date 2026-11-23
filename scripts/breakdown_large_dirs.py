from pathlib import Path

for target_dir in ["database", "data_publikasi", "frontend"]:
    p = Path(target_dir)
    print(f"\n=== BREAKDOWN FOR {target_dir} ===")
    if not p.exists():
        continue
    for sub in p.iterdir():
        if sub.is_dir():
            size = sum(f.stat().st_size for f in sub.rglob("*") if f.is_file())
            count = sum(1 for f in sub.rglob("*") if f.is_file())
            print(f"  [DIR]  {sub.name:25} | {count:8} files | {size / (1024*1024):8.2f} MB")
        else:
            print(f"  [FILE] {sub.name:25} | {1:8} files | {sub.stat().st_size / (1024*1024):8.2f} MB")
