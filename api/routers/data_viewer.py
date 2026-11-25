"""
Publication and Granular Statistical Data Explorer Router for BPS Demak.
Serves interactive data grid, search/filter per kecamatan, and Proof of Data drawer.
"""
import os
import hashlib
import re
from typing import Dict, Any, Optional, List
import json
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from config.database import get_db_connection, get_db_cursor

router = APIRouter(prefix="/api/data", tags=["Publication & Data Explorer"])


KECAMATAN_NAMES = [
    'Sayung', 'Karangtengah', 'Bonang', 'Wonosalam',
    'Dempet', 'Gajah', 'Karanganyar', 'Mijen', 'Wedung',
    'Guntur', 'Karangawen', 'Mranggen', 'Kebonagung'
]

def _clean_param(val: Any) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, "default"):
        val = val.default
        if val is None:
            return None
    s = str(val).strip()
    if s.lower() in ("", "none", "null", "undefined", "semua"):
        return None
    return s

def detect_daerah_from_title(title: str) -> str:
    if not title:
        return "Kabupaten Demak"
    t_lower = title.lower()
    for kec in KECAMATAN_NAMES:
        if kec.lower() in t_lower:
            return f"Kecamatan {kec}"
    if "kecamatan demak" in t_lower:
        return "Kecamatan Demak"
    return "Kabupaten Demak"

def is_valid_statistical_table(
    title: str, 
    row_count: int = 1, 
    col_count: int = 1,
    cols: Optional[List[Any]] = None,
    records: Optional[List[Any]] = None
) -> bool:
    """
    Validates whether a table record is a real statistical table or a false-positive narrative fragment.
    Filters out prose sentences, headings, glossaries, and tables of contents accidentally parsed by OCR.
    """
    if not title or len(title.strip()) < 5:
        return False
    s = title.strip()

    # 1. Reject sentence fragments starting with lowercase
    if s[0].islower():
        return False

    # 2. Reject sentence fragments ending with trailing hyphen, comma, slash, or conjunction
    if re.search(r'[\-\,\/]$', s):
        return False
    if re.search(r'\b(yaitu|sebagai|adalah|bahwa|sehingga|namun|dengan|untuk|yang)\s*$', s, re.IGNORECASE):
        return False

    # 3. Reject glossary / concept definitions (e.g. "10. Tidak Punya Ijazah SD adalah jika...")
    if re.search(r'\b(adalah|merupakan|yaitu|diartikan|didefinisikan)\b', s, re.IGNORECASE):
        return False

    # 4. Reject Table of Contents dots in title (e.g. "Tabel 17. ... ...... 53")
    if re.search(r'\.{3,}', s):
        return False

    # 5. Reject document headings, preamble, and non-table metadata
    reject_patterns = [
        r'^(assalamu|bupati|halaman|daftar|bab\s+[ivxlcdm]+|kata\s+pengantar|puji\s+syukur|issn|undang-undang|gambar\s+\d+)',
        r'^\d+\.\d+\.?\s*(latar|maksud|tujuan|metodologi|ruang\s+lingkup|sistematika|kesimpulan|saran)',
        r'badan pusat statistik',
        r'sistematika penulisan',
        r'tim penyusun',
        r'berakhlak'
    ]
    for p in reject_patterns:
        if re.search(p, s, re.IGNORECASE):
            return False

    # 6. Reject Table of Contents (Daftar Tabel) parsed as table:
    # A Table of Contents contains leader dots like '......' in row cells
    if records:
        recs_str = json.dumps(records)
        if re.search(r'\.{3,}', recs_str):
            return False

    if cols:
        cols_str = " ".join(str(c) for c in cols).lower()
        if 'daftar_tabel' in cols_str:
            return False

    # 7. Positive match: Standard official BPS table numbering (Tabel 1, Table 2.1, 3.15.)
    # Strictly requires 'Tabel' or 'Table'. Bare numbers like "10. " are REJECTED!
    if re.search(r'^(tabel|table)\s+[\d\.]*', s, re.IGNORECASE):
        return True

    # Positive match 2: Clean statistical titles without sentence punctuation in middle
    if not re.search(r'[a-zA-Z]\.\s+[a-zA-Z]', s):
        if re.search(r'^(jumlah|luas|banyaknya|persentase|produksi|populasi|rata-rata|distribusi|indikator|perkembangan|proyeksi)\s+', s, re.IGNORECASE):
            return True

    return False


@router.get("/publications")
def get_publications_list(
    search: Optional[str] = Query(None, description="Pencarian judul atau ID publikasi"),
    kecamatan: Optional[str] = Query(None, description="Filter nama kecamatan"),
    tahun: Optional[str] = Query(None, description="Filter tahun rilis publikasi"),
    kategori: Optional[str] = Query(None, description="Filter kategori data"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Returns list of official BPS publications with metadata,
    file verification info (size, sha256 checksum, local path), and extracted table count.
    """
    try:
        limit_val = getattr(limit, "default", limit) if hasattr(limit, "default") else limit
        offset_val = getattr(offset, "default", offset) if hasattr(offset, "default") else offset
        if not isinstance(limit_val, int):
            limit_val = 50
        if not isinstance(offset_val, int):
            offset_val = 0

        clean_search = _clean_param(search)
        clean_kecamatan = _clean_param(kecamatan)
        clean_tahun = _clean_param(tahun)
        clean_kategori = _clean_param(kategori)

        with get_db_cursor() as cur:
            where_clauses = ["1=1"]
            params: List[Any] = []

            if clean_search:
                where_clauses.append("(p.title ILIKE %s OR p.publication_id ILIKE %s)")
                params.extend([f"%{clean_search}%", f"%{clean_search}%"])
            if clean_kecamatan:
                where_clauses.append("p.title ILIKE %s")
                params.append(f"%{clean_kecamatan}%")
            if clean_tahun:
                where_clauses.append("(p.release_date ILIKE %s OR p.title ILIKE %s)")
                params.extend([f"%{clean_tahun}%", f"%{clean_tahun}%"])
            if clean_kategori:
                where_clauses.append("p.category ILIKE %s")
                params.append(f"%{clean_kategori}%")

            where_sql = " AND ".join(where_clauses)

            # CTE for deduplicated publications (unifies slug and hex duplicate rows)
            cte_sql = f"""
                WITH ranked_pubs AS (
                    SELECT 
                        p.publication_id, 
                        p.title, 
                        p.release_date, 
                        p.category, 
                        COALESCE(s.t_count, p.total_tables_extracted, 0) AS table_count, 
                        p.total_chunks_indexed,
                        p.local_file_path, 
                        p.file_size_bytes, 
                        p.checksum_sha256, 
                        p.download_status, 
                        p.extraction_status, 
                        p.pdf_url,
                        p.created_at,
                        ROW_NUMBER() OVER (
                            PARTITION BY LOWER(TRIM(p.title)), p.release_date 
                            ORDER BY 
                                CASE WHEN p.publication_id ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}' THEN 0 ELSE 1 END,
                                COALESCE(s.t_count, p.total_tables_extracted, 0) DESC,
                                p.total_chunks_indexed DESC,
                                p.created_at DESC
                        ) as rn
                    FROM publications p
                    LEFT JOIN (
                        SELECT doc_id, COUNT(*) AS t_count
                        FROM statistical_tables
                        WHERE table_title ~* '^(tabel|table)\\s+[\\d\\.]*'
                          AND table_title !~* '\\b(adalah|merupakan|yaitu|diartikan|didefinisikan)\\b'
                          AND table_title !~ '\\.{3,}'
                          AND table_title !~* '^(assalamu|bupati|halaman|daftar|bab|kata\\s+pengantar|puji\\s+syukur|tim\\s+penyusun|gambar|berakhlak)'
                          AND table_title !~ '[\\-\\,\\/]$'
                          AND table_title !~ '^[a-z]'
                        GROUP BY doc_id
                    ) s ON p.publication_id = s.doc_id
                    WHERE {where_sql}
                )
            """

            # Total matching unique publications
            cur.execute(f"{cte_sql} SELECT COUNT(*) FROM ranked_pubs WHERE rn = 1", tuple(params))
            total = cur.fetchone()[0]

            # Overall total valid tables across the database
            cur.execute("""
                SELECT COUNT(*) FROM statistical_tables
                WHERE table_title ~* '^(tabel|table)\\s+[\\d\\.]*'
                  AND table_title !~* '\\b(adalah|merupakan|yaitu|diartikan|didefinisikan)\\b'
                  AND table_title !~ '\\.{3,}'
                  AND table_title !~* '^(assalamu|bupati|halaman|daftar|bab|kata\\s+pengantar|puji\\s+syukur|tim\\s+penyusun|gambar|berakhlak)'
                  AND table_title !~ '[\\-\\,\\/]$'
                  AND table_title !~ '^[a-z]';
            """)
            total_tables_overall = cur.fetchone()[0]

            # Query publications with table count from statistical_tables (using COALESCE)
            query = f"""
                {cte_sql}
                SELECT 
                    publication_id, 
                    title, 
                    release_date, 
                    category, 
                    table_count, 
                    total_chunks_indexed,
                    local_file_path, 
                    file_size_bytes, 
                    checksum_sha256, 
                    download_status, 
                    extraction_status, 
                    pdf_url,
                    created_at
                FROM ranked_pubs
                WHERE rn = 1
                ORDER BY release_date DESC NULLS LAST, created_at DESC NULLS LAST
                LIMIT %s OFFSET %s
            """
            cur.execute(query, tuple(params + [limit_val, offset_val]))
            rows = cur.fetchall()

            items = []
            for r in rows:
                daerah = detect_daerah_from_title(r[1])
                items.append({
                    "doc_id": r[0],
                    "publication_id": r[0],
                    "judul": r[1],
                    "tahun": r[2] or "-",
                    "kategori": r[3] or "Umum",
                    "daerah": daerah,
                    "total_tabel": r[4] or 0,
                    "total_chunks": r[5] or 0,
                    "file_path": r[6] or "",
                    "file_size_bytes": r[7] or 0,
                    "checksum_sha256": r[8] or "",
                    "download_status": r[9] or "completed",
                    "extraction_status": r[10] or "completed",
                    "pdf_url": r[11] or "",
                    "created_at": r[12].isoformat() if r[12] else None
                })

            return {
                "success": True,
                "total": total,
                "total_tables_overall": total_tables_overall,
                "items": items,
                "limit": limit_val,
                "offset": offset_val
            }
    except Exception as ex:
        logger.error(f"[DataViewerRouter] Error fetching publications: {ex}")
        return {"success": False, "total": 0, "total_tables_overall": 0, "items": [], "error": str(ex)}


@router.get("/publication/{doc_id}/tables")
def get_publication_tables(doc_id: str) -> Dict[str, Any]:
    """
    Returns list of granular statistical tables belonging to a specific publication.
    Sorted by page number (halaman).
    Filters out false-positive narrative fragments.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT table_id, doc_id, table_title, halaman, tahun, kecamatan,
                       jsonb_array_length(records) AS row_count, jsonb_array_length(kolom) AS column_count,
                       satuan, sumber, created_at, kolom, records
                FROM statistical_tables
                WHERE doc_id = %s
                ORDER BY halaman ASC, table_id ASC;
            """, (doc_id,))
            rows = cur.fetchall()

            items = []
            for r in rows:
                title = r[2] or ""
                # Strict statistical table validation filter
                if not is_valid_statistical_table(title, r[6] or 0, r[7] or 0, cols=r[11], records=r[12]):
                    continue

                items.append({
                    "table_id": r[0],
                    "doc_id": r[1],
                    "judul_tabel": title,
                    "halaman": r[3],
                    "tahun": r[4],
                    "daerah": r[5] or "Kabupaten Demak",
                    "row_count": r[6] or 0,
                    "column_count": r[7] or 0,
                    "satuan": r[8] or "",
                    "sumber": r[9] or "BPS Kabupaten Demak",
                    "created_at": r[10].isoformat() if r[10] else None
                })

            return {
                "success": True,
                "doc_id": doc_id,
                "total": len(items),
                "items": items
            }
    except Exception as ex:
        logger.error(f"[DataViewerRouter] Error fetching tables for publication {doc_id}: {ex}")
        return {"success": False, "doc_id": doc_id, "total": 0, "items": [], "error": str(ex)}


@router.get("/publication/{doc_id}/verify")
def verify_publication(doc_id: str) -> Dict[str, Any]:
    """
    Verifies the physical publication file on disk, its checksum, page count,
    and PostgreSQL ingestion completeness.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 
                    p.publication_id, p.title, p.release_date, p.category, 
                    p.local_file_path, p.file_size_bytes, p.checksum_sha256,
                    p.download_status, p.extraction_status, p.pdf_url,
                    COALESCE(s.t_count, p.total_tables_extracted, 0) AS total_tables,
                    p.total_chunks_indexed, p.created_at
                FROM publications p
                LEFT JOIN (
                    SELECT doc_id, COUNT(*) AS t_count
                    FROM statistical_tables
                    WHERE table_title ~* '^(tabel|table)\\s+[\\d\\.]*'
                      AND table_title !~* '\\b(adalah|merupakan|yaitu|diartikan|didefinisikan)\\b'
                      AND table_title !~ '\\.{3,}'
                      AND table_title !~* '^(assalamu|bupati|halaman|daftar|bab|kata\\s+pengantar|puji\\s+syukur|tim\\s+penyusun|gambar|berakhlak)'
                      AND table_title !~ '[\\-\\,\\/]$'
                      AND table_title !~ '^[a-z]'
                    GROUP BY doc_id
                ) s ON p.publication_id = s.doc_id
                WHERE p.publication_id = %s
            """, (doc_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Publikasi '{doc_id}' tidak ditemukan di database.")

            file_path = row[4] or ""
            file_exists = False
            actual_size = row[5] or 0
            sha256_hash = row[6] or ""
            page_count = None

            if file_path and os.path.exists(file_path):
                file_exists = True
                actual_size = os.path.getsize(file_path)
                
                # Compute SHA256 if missing
                if not sha256_hash:
                    h = hashlib.sha256()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            h.update(chunk)
                    sha256_hash = h.hexdigest()

                # Get page count using PyMuPDF if possible
                try:
                    import pymupdf
                    doc = pymupdf.open(file_path)
                    page_count = len(doc)
                    doc.close()
                except Exception:
                    pass

            daerah = detect_daerah_from_title(row[1])

            return {
                "success": True,
                "data": {
                    "doc_id": row[0],
                    "title": row[1],
                    "release_date": row[2] or "-",
                    "category": row[3] or "Umum",
                    "daerah": daerah,
                    "local_file_path": file_path,
                    "file_exists": file_exists,
                    "file_size_bytes": actual_size,
                    "file_size_formatted": f"{actual_size / (1024*1024):.2f} MB" if actual_size > 0 else "0 MB",
                    "checksum_sha256": sha256_hash,
                    "page_count": page_count,
                    "download_status": row[7] or "PROCESSED",
                    "extraction_status": row[8] or "PROCESSED",
                    "pdf_url": row[9] or "",
                    "total_tables": row[10] or 0,
                    "total_chunks": row[11] or 0,
                    "created_at": row[12].isoformat() if row[12] else None
                }
            }
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"[DataViewerRouter] Error verifying publication {doc_id}: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@router.get("/tables")
def get_statistical_tables(
    search: Optional[str] = Query(None, description="Pencarian judul atau topik tabel"),
    kecamatan: Optional[str] = Query(None, description="Filter nama kecamatan"),
    tahun: Optional[str] = Query(None, description="Filter tahun rujukan"),
    kategori: Optional[str] = Query(None, description="Filter kategori data"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Returns granular statistical tables extracted from BPS publications.
    Supports filtering by kecamatan, year, category, and keyword search.
    """
    try:
        limit_val = getattr(limit, "default", limit) if hasattr(limit, "default") else limit
        offset_val = getattr(offset, "default", offset) if hasattr(offset, "default") else offset
        if not isinstance(limit_val, int):
            limit_val = 20
        if not isinstance(offset_val, int):
            offset_val = 0

        clean_search = _clean_param(search)
        clean_kecamatan = _clean_param(kecamatan)
        clean_tahun = _clean_param(tahun)
        clean_kategori = _clean_param(kategori)

        with get_db_cursor() as cur:
            where_clauses = ["1=1"]
            params: List[Any] = []

            if clean_search:
                where_clauses.append("(table_title ILIKE %s OR catatan ILIKE %s)")
                params.extend([f"%{clean_search}%", f"%{clean_search}%"])
            if clean_kecamatan:
                where_clauses.append("kecamatan ILIKE %s")
                params.append(f"%{clean_kecamatan}%")
            if clean_tahun:
                where_clauses.append("tahun = %s")
                params.append(clean_tahun)
            if clean_kategori:
                where_clauses.append("doc_title ILIKE %s")
                params.append(f"%{clean_kategori}%")

            # Exclude false-positive narrative text paragraphs that were accidentally parsed
            where_clauses.append("""
                (
                    table_title !~ '^[a-z]'
                    AND table_title !~ '[\\-\\,\\/]$'
                    AND table_title !~ '\\.{3,}'
                    AND table_title !~* '\\b(adalah|merupakan|yaitu|diartikan|didefinisikan)\\b'
                    AND table_title !~* '^(assalamu|bupati|halaman|daftar|bab\\s+[ivxlcdm]+|kata\\s+pengantar|puji\\s+syukur|issn|undang-undang|gambar\\s+\\d+|tim\\s+penyusun|berakhlak)'
                    AND table_title !~* '^\\d+\\.\\d+\\.?\\s*(latar|maksud|tujuan|metodologi|ruang\\s+lingkup|sistematika|kesimpulan|saran)'
                    AND table_title !~* 'badan pusat statistik'
                    AND (
                        table_title ~* '^(tabel|table)\\s+[\\d\\.]*'
                        OR (
                            table_title ~* '^(jumlah|luas|banyaknya|persentase|produksi|populasi|rata-rata|distribusi|indikator|perkembangan|proyeksi)\\s+'
                            AND table_title !~* '[a-zA-Z]\\.\\s+[a-zA-Z]'
                        )
                    )
                )
            """)

            where_sql = " AND ".join(where_clauses)

            cur.execute(f"SELECT COUNT(*) FROM statistical_tables WHERE {where_sql}", tuple(params))
            total = cur.fetchone()[0]

            query = f"""
                SELECT table_id, doc_id, table_title, halaman, tahun, 'Umum' AS kategori, kecamatan AS daerah,
                       jsonb_array_length(records) AS row_count, jsonb_array_length(kolom) AS column_count,
                       satuan, sumber, created_at
                FROM statistical_tables
                WHERE {where_sql}
                ORDER BY tahun DESC, created_at DESC
                LIMIT %s OFFSET %s
            """
            cur.execute(query, tuple(params + [limit, offset]))
            rows = cur.fetchall()

            items = []
            for r in rows:
                items.append({
                    "table_id": r[0],
                    "doc_id": r[1],
                    "judul_tabel": r[2],
                    "halaman": r[3],
                    "tahun": r[4],
                    "kategori": r[5],
                    "daerah": r[6],
                    "row_count": r[7] or 0,
                    "column_count": r[8] or 0,
                    "satuan": r[9] or "",
                    "sumber": r[10] or "BPS Kabupaten Demak",
                    "created_at": r[11].isoformat() if r[11] else None
                })

            return {
                "success": True,
                "total": total,
                "items": items,
                "limit": limit,
                "offset": offset
            }
    except Exception as ex:
        logger.error(f"[DataViewerRouter] Error fetching statistical tables: {ex}")
        return {"success": False, "total": 0, "items": [], "error": str(ex)}


@router.get("/table/{table_id}")
def get_table_detail(table_id: str) -> Dict[str, Any]:
    """
    Returns full granular table data for Proof of Data Drawer.
    Includes headers, cell values with exact NIL vs 0 status, and natural language text.
    """
    try:
        with get_db_cursor() as cur:
            cur.execute(
                """
                SELECT table_id, doc_id, table_title, halaman, tahun, 'Umum' AS kategori, kecamatan AS daerah,
                       jsonb_array_length(records) AS row_count, jsonb_array_length(kolom) AS column_count,
                       kolom, records, satuan, sumber, catatan, created_at
                FROM statistical_tables
                WHERE table_id = %s
                """,
                (table_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail=f"Tabel '{table_id}' tidak ditemukan.")

            headers_json = row[9] if isinstance(row[9], list) else (json.loads(row[9]) if row[9] else [])
            raw_data_json = row[10] if isinstance(row[10], list) else (json.loads(row[10]) if row[10] else [])

            # Format headers cleanly without ugly concatenated underscores
            clean_headers = []
            for h in headers_json:
                h_str = str(h or "").strip()
                h_clean = re.sub(r'__+', ' ', h_str).replace('_', ' ').strip()
                clean_headers.append(h_clean if h_clean else "Kolom")

            # Fetch natural language representation from vector_chunks
            cur.execute(
                """
                SELECT representasi_teks FROM vector_chunks 
                WHERE doc_id = %s AND (table_id ILIKE %s OR halaman = %s)
                ORDER BY CASE WHEN table_id ILIKE %s THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (row[1], f"%{row[0].split('_p')[-1]}%", row[3], f"%{row[0].split('_p')[-1]}%")
            )
            rep_row = cur.fetchone()
            representasi_teks = rep_row[0] if (rep_row and rep_row[0]) else f"Tabel Statistik: {row[2]} (Halaman {row[3]}, Tahun {row[4]}). Memuat {row[7]} baris data."

            return {
                "success": True,
                "data": {
                    "table_id": row[0],
                    "doc_id": row[1],
                    "judul_tabel": row[2],
                    "halaman": row[3],
                    "tahun": row[4],
                    "kategori": row[5],
                    "daerah": row[6],
                    "row_count": row[7],
                    "column_count": row[8],
                    "headers": clean_headers,
                    "rows": raw_data_json,
                    "representasi_teks": representasi_teks,
                    "satuan": row[11],
                    "sumber": row[12],
                    "catatan": row[13],
                    "created_at": row[14].isoformat() if row[14] else None
                }
            }
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"[DataViewerRouter] Error fetching table detail '{table_id}': {ex}")
        raise HTTPException(status_code=500, detail=str(ex))
