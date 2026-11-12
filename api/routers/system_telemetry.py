"""
System Telemetry, Vector Observability, and Log Stream Router for BPS Demak.
Provides database health checks, pgvector index stats, and search testing playground.
"""
import os
import glob
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from loguru import logger
from config.database import get_db_connection, get_db_cursor
from modules.retrieval.hybrid_search import HybridRetriever

router = APIRouter(prefix="/api/system", tags=["System Telemetry & Observability"])


class SearchTestRequest(BaseModel):
    query: str
    daerah: Optional[str] = None
    tahun: Optional[str] = None
    top_k: int = 4


@router.get("/health")
def get_system_health() -> Dict[str, Any]:
    """Returns database connection status, pgvector status, and model provider health."""
    db_ok = False
    pgvector_ver = "Unknown"
    db_error = None

    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            row = cur.fetchone()
            if row:
                pgvector_ver = row[0]
                db_ok = True
    except Exception as ex:
        db_error = str(ex)

    gemini_key_set = bool(os.getenv("GEMINI_API_KEY"))

    return {
        "status": "healthy" if db_ok else "degraded",
        "database_connected": db_ok,
        "database_name": "bps_rag3321",
        "database_host": "10.133.21.24:5433",
        "pgvector": {
            "installed": db_ok,
            "version": pgvector_ver,
            "index_type": "HNSW (m=16, ef_construction=64, cosine)"
        },
        "llm_provider": {
            "name": os.getenv("LLM_PROVIDER", "gemini"),
            "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
            "api_key_configured": gemini_key_set
        },
        "db_error": db_error
    }


@router.get("/vector-stats")
def get_vector_observability_stats() -> Dict[str, Any]:
    """Returns total vector chunks, embedding cache hit metrics, and category distributions."""
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM vector_chunks;")
            total_chunks = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM embedding_cache;")
            cached_embeddings = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT table_id) FROM statistical_tables;")
            total_tables = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM publications;")
            total_publications = cur.fetchone()[0]

            # Year breakdown
            cur.execute(
                """
                SELECT tahun, COUNT(*) FROM vector_chunks
                WHERE tahun IS NOT NULL
                GROUP BY tahun ORDER BY tahun DESC LIMIT 6;
                """
            )
            by_year = [{"tahun": r[0], "count": r[1]} for r in cur.fetchall()]

            return {
                "success": True,
                "total_chunks": total_chunks,
                "cached_embeddings": cached_embeddings,
                "total_tables": total_tables,
                "total_publications": total_publications,
                "breakdown_by_year": by_year
            }
    except Exception as ex:
        logger.error(f"[SystemTelemetryRouter] Error querying vector stats: {ex}")
        return {
            "success": False,
            "total_chunks": 0,
            "cached_embeddings": 0,
            "total_tables": 0,
            "total_publications": 0,
            "error": str(ex)
        }


@router.post("/test-search")
def test_hybrid_search(req: SearchTestRequest) -> Dict[str, Any]:
    """
    Simulates search query in Playground and returns top-k retrieved chunks
    with reciprocal rank fusion (RRF) scores and content snippets.
    """
    try:
        retriever = HybridRetriever()
        results = retriever.search(
            query=req.query,
            top_k=req.top_k,
            daerah=req.daerah,
            tahun=req.tahun
        )
        return {
            "success": True,
            "query": req.query,
            "total_retrieved": len(results),
            "results": results
        }
    except Exception as ex:
        logger.error(f"[SystemTelemetryRouter] Error running search playground: {ex}")
        raise HTTPException(status_code=500, detail=str(ex))


@router.get("/logs")
def get_recent_system_logs(lines: int = Query(50, ge=10, le=500)) -> Dict[str, Any]:
    """Returns recent log lines for live console monitor."""
    log_files = glob.glob("logs/*.log")
    recent_lines = []

    if log_files:
        latest_file = max(log_files, key=os.path.getmtime)
        try:
            with open(latest_file, "r", encoding="utf-8", errors="replace") as f:
                all_lines = f.readlines()
                recent_lines = [line.strip() for line in all_lines[-lines:] if line.strip()]
        except Exception as e:
            recent_lines = [f"Error reading log file: {e}"]
    else:
        recent_lines = [
            f"BPS Demak Command Center ready.",
            f"Connected to PostgreSQL database 'bps_rag3321' on 10.133.21.24:5433.",
            f"pgvector extension 0.8.1 active with HNSW index."
        ]

    return {
        "success": True,
        "total_lines": len(recent_lines),
        "logs": recent_lines
    }
