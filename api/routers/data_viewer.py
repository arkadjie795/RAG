"""
Publication and Granular Statistical Data Explorer Router for BPS Demak.
Serves interactive data grid, search/filter per kecamatan, and Proof of Data drawer.
"""
from typing import Dict, Any, Optional, List
import json
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from config.database import get_db_connection

router = APIRouter(prefix="/api/data", tags=["Publication & Data Explorer"])


@router.get("/publications")
def get_publications_list(
    tahun: Optional[str] = Query(None, description="Filter tahun rilis publikasi"),
    kategori: Optional[str] = Query(None, description="Filter kategori data"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Returns list of ingested official BPS publications."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                where_clauses = ["1=1"]
                params: List[Any] = []

                if tahun:
                    where_clauses.append("tahun = %s")
                    params.append(tahun)
                if kategori:
                    where_clauses.append("kategori ILIKE %s")
                    params.append(f"%{kategori}%")

                where_sql = " AND ".join(where_clauses)

                # Total count
                cur.execute(f"SELECT COUNT(*) FROM publications WHERE {where_sql}", tuple(params))
                total = cur.fetchone()[0]

                # Items query
                query = f"""
                    SELECT doc_id, judul, tahun, kategori, daerah, total_tabel, file_path, created_at
                    FROM publications
                    WHERE {where_sql}
                    ORDER BY tahun DESC, created_at DESC
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, tuple(params + [limit, offset]))
                rows = cur.fetchall()

                items = []
                for r in rows:
                    items.append({
                        "doc_id": r[0],
                        "judul": r[1],
                        "tahun": r[2],
                        "kategori": r[3],
                        "daerah": r[4],
                        "total_tabel": r[5] or 0,
                        "file_path": r[6] or "",
                        "created_at": r[7].isoformat() if r[7] else None
                    })

                return {
                    "success": True,
                    "total": total,
                    "items": items,
                    "limit": limit,
                    "offset": offset
                }
    except Exception as ex:
        logger.error(f"[DataViewerRouter] Error fetching publications: {ex}")
        # Return elegant empty list if database table is currently empty
        return {"success": True, "total": 0, "items": [], "error": str(ex)}


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
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                where_clauses = ["1=1"]
                params: List[Any] = []

                if search:
                    where_clauses.append("(judul_tabel ILIKE %s OR representasi_teks ILIKE %s)")
                    params.extend([f"%{search}%", f"%{search}%"])
                if kecamatan and kecamatan.lower() != "semua":
                    where_clauses.append("daerah ILIKE %s")
                    params.append(f"%{kecamatan}%")
                if tahun and tahun.lower() != "semua":
                    where_clauses.append("tahun = %s")
                    params.append(tahun)
                if kategori and kategori.lower() != "semua":
                    where_clauses.append("kategori ILIKE %s")
                    params.append(f"%{kategori}%")

                where_sql = " AND ".join(where_clauses)

                cur.execute(f"SELECT COUNT(*) FROM statistical_tables WHERE {where_sql}", tuple(params))
                total = cur.fetchone()[0]

                query = f"""
                    SELECT table_id, doc_id, judul_tabel, halaman, tahun, kategori, daerah,
                           row_count, column_count, satuan, sumber, created_at
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
        return {"success": True, "total": 0, "items": [], "error": str(ex)}


@router.get("/table/{table_id}")
def get_table_detail(table_id: str) -> Dict[str, Any]:
    """
    Returns full granular table data for Proof of Data Drawer.
    Includes headers, cell values with exact NIL vs 0 status, and natural language text.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_id, doc_id, judul_tabel, halaman, tahun, kategori, daerah,
                           row_count, column_count, headers, raw_data, representasi_teks,
                           satuan, sumber, catatan, created_at
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
                        "headers": headers_json,
                        "rows": raw_data_json,
                        "representasi_teks": row[11],
                        "satuan": row[12],
                        "sumber": row[13],
                        "catatan": row[14],
                        "created_at": row[15].isoformat() if row[15] else None
                    }
                }
    except HTTPException:
        raise
    except Exception as ex:
        logger.error(f"[DataViewerRouter] Error fetching table detail '{table_id}': {ex}")
        raise HTTPException(status_code=500, detail=str(ex))
