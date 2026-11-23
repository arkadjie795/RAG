import os
import sys
import json
import math
import psycopg2
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))
from config.settings import settings

def clean_json_obj(item):
    if isinstance(item, str):
        return item.replace("\x00", "")
    if isinstance(item, float):
        if math.isnan(item) or math.isinf(item):
            return None
        return item
    if isinstance(item, dict):
        return {str(k).replace("\x00", ""): clean_json_obj(v) for k, v in item.items()}
    if isinstance(item, list):
        return [clean_json_obj(x) for x in item]
    return item

def run_table_migration():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_DATABASE,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD
    )
    cur = conn.cursor()

    cur.execute("SELECT publication_id FROM publications;")
    valid_pub_ids = {r[0] for r in cur.fetchall()}
    print(f"Total valid publications in PostgreSQL: {len(valid_pub_ids)}")

    cur.execute("SELECT table_id FROM statistical_tables;")
    existing_table_ids = {r[0] for r in cur.fetchall()}
    print(f"Existing tables in PostgreSQL: {len(existing_table_ids)}")

    tables_root = Path("database/tables")
    if not tables_root.exists():
        print("database/tables does not exist!")
        return

    doc_dirs = [d for d in tables_root.iterdir() if d.is_dir()]
    print(f"Scanning {len(doc_dirs)} document directories in database/tables...")

    batch = []
    batch_size = 200
    inserted_total = 0
    skipped_total = 0

    insert_sql = """
        INSERT INTO statistical_tables (
            table_id, doc_id, doc_title, table_number, table_title,
            halaman, kecamatan, tahun, satuan, sumber, catatan, kolom, records
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
        ON CONFLICT (table_id) DO NOTHING;
    """

    for d_idx, doc_dir in enumerate(doc_dirs):
        t_files = list(doc_dir.glob("*.json"))
        for t_file in t_files:
            try:
                with open(t_file, "r", encoding="utf-8") as f:
                    t_data = json.load(f)

                raw_t_id = t_data.get("tabel_id", "t1")
                doc_id = t_data.get("dokumen_id", doc_dir.name)

                if doc_id not in valid_pub_ids:
                    matched = False
                    for pub in valid_pub_ids:
                        if doc_id in pub or pub in doc_id:
                            doc_id = pub
                            matched = True
                            break
                    if not matched:
                        skipped_total += 1
                        continue

                table_pk = f"{doc_id}_{raw_t_id}"
                if table_pk in existing_table_ids:
                    continue

                doc_title = str(t_data.get("dokumen_sumber", "")).replace("\x00", "")
                table_title = str(t_data.get("judul_tabel", "Tabel Statistik")).replace("\x00", "")
                halaman = t_data.get("halaman", 1)
                try:
                    halaman = int(halaman)
                except (ValueError, TypeError):
                    halaman = 1

                kecamatan = str(t_data.get("daerah", "Kabupaten Demak")).replace("\x00", "")
                tahun = str(t_data.get("tahun", "2026")).replace("\x00", "")
                satuan = str(t_data.get("satuan", "N/A")).replace("\x00", "")
                sumber = str(t_data.get("sumber", "BPS Kabupaten Demak")).replace("\x00", "")
                catatan = str(t_data.get("catatan", "")).replace("\x00", "")
                clean_kolom = clean_json_obj(t_data.get("kolom", []))
                clean_records = clean_json_obj(t_data.get("records", []))

                batch.append((
                    table_pk,
                    doc_id,
                    doc_title,
                    str(t_data.get("nomor_tabel", "")).replace("\x00", ""),
                    table_title,
                    halaman,
                    kecamatan,
                    tahun,
                    satuan,
                    sumber,
                    catatan,
                    json.dumps(clean_kolom, ensure_ascii=False),
                    json.dumps(clean_records, ensure_ascii=False)
                ))

                existing_table_ids.add(table_pk)

                if len(batch) >= batch_size:
                    try:
                        cur.executemany(insert_sql, batch)
                        conn.commit()
                        inserted_total += len(batch)
                    except Exception as b_err:
                        conn.rollback()
                        for single_item in batch:
                            try:
                                cur.execute(insert_sql, single_item)
                                conn.commit()
                                inserted_total += 1
                            except Exception:
                                conn.rollback()
                    batch = []

            except Exception:
                pass

    if batch:
        try:
            cur.executemany(insert_sql, batch)
            conn.commit()
            inserted_total += len(batch)
        except Exception:
            conn.rollback()
            for single_item in batch:
                try:
                    cur.execute(insert_sql, single_item)
                    conn.commit()
                    inserted_total += 1
                except Exception:
                    conn.rollback()

    cur.execute("SELECT count(*) FROM statistical_tables;")
    final_count = cur.fetchone()[0]
    print(f"DONE: Successfully migrated {inserted_total} additional tables!")
    print(f"Final count in statistical_tables: {final_count} tables")
    print(f"Skipped invalid/missing doc_id: {skipped_total}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_table_migration()
