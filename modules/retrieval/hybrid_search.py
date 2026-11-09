"""
Native PostgreSQL Hybrid Retrieval Engine.
Fuses pgvector HNSW dense cosine similarity with PostgreSQL Full-Text Search (tsvector)
using Reciprocal Rank Fusion (RRF).
"""
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from config.database import get_db_connection
from modules.vectorization.embedder import VectorEmbedder
from modules.retrieval.entity_dictionary import DemakEntityExtractor


class HybridRetriever:
    """Orchestrates Hybrid Semantic and Lexical Retrieval with RRF."""

    def __init__(self, embedder: Optional[VectorEmbedder] = None):
        self.embedder = embedder or VectorEmbedder()
        self.entity_extractor = DemakEntityExtractor()

    def search(
        self,
        query: str,
        top_k: int = 5,
        daerah: Optional[str] = None,
        tahun: Optional[str] = None,
        kategori: Optional[str] = None,
        rrf_k: float = 60.0
    ) -> List[Dict[str, Any]]:
        """
        Executes a single-query PostgreSQL Hybrid Search (Dense HNSW + Lexical FTS + RRF).
        """
        if not query or not query.strip():
            return []

        # 1. Extract entities if not explicitly passed
        detected = self.entity_extractor.extract_entities(query)
        target_daerah = daerah or detected.get("kecamatan")
        target_tahun = tahun or detected.get("tahun")

        # 2. Compute query dense embedding
        query_vector = self.embedder.generate_embeddings([query])[0]
        emb_literal = "[" + ",".join(str(x) for x in query_vector) + "]"

        daerah_pattern = f"%{target_daerah}%" if target_daerah else None

        sql = f"""
            WITH dense_candidates AS (
                SELECT 
                    chunk_id, 
                    representasi_teks, 
                    metadata,
                    (1.0 - (embedding <=> %s::vector)) AS dense_sim,
                    ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector ASC) AS dense_rank
                FROM vector_chunks
                WHERE embedding IS NOT NULL
                  AND (%s::text IS NULL OR daerah ILIKE %s)
                  AND (%s::text IS NULL OR tahun = %s)
                LIMIT 30
            ),
            lexical_candidates AS (
                SELECT 
                    chunk_id, 
                    representasi_teks, 
                    metadata,
                    ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, plainto_tsquery('indonesian', %s)) DESC) AS lex_rank
                FROM vector_chunks
                WHERE tsv @@ plainto_tsquery('indonesian', %s)
                  AND (%s::text IS NULL OR daerah ILIKE %s)
                  AND (%s::text IS NULL OR tahun = %s)
                LIMIT 30
            )
            SELECT 
                COALESCE(d.chunk_id, l.chunk_id) AS chunk_id,
                COALESCE(d.representasi_teks, l.representasi_teks) AS representasi_teks,
                COALESCE(d.metadata, l.metadata) AS metadata,
                (COALESCE(1.0 / ({rrf_k} + d.dense_rank), 0.0) + COALESCE(1.0 / ({rrf_k} + l.lex_rank), 0.0)) AS score
            FROM dense_candidates d
            FULL OUTER JOIN lexical_candidates l ON d.chunk_id = l.chunk_id
            ORDER BY score DESC
            LIMIT %s;
        """

        params = (
            emb_literal, emb_literal,
            target_daerah, daerah_pattern,
            target_tahun, target_tahun,
            query, query,
            target_daerah, daerah_pattern,
            target_tahun, target_tahun,
            top_k
        )

        results = []
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    for cid, rep_text, meta, score in rows:
                        meta_dict = meta if isinstance(meta, dict) else json.loads(meta or "{}")
                        results.append({
                            "chunk_id": cid,
                            "score": float(score) if score is not None else 0.0,
                            "representasi_teks": rep_text,
                            "metadata": meta_dict
                        })
        except Exception as e:
            logger.warning(f"[HybridRetriever] Native PostgreSQL hybrid query failed ({e}). Falling back to dense search.")
            from modules.storage.postgres_store import PostgresVectorStore
            store = PostgresVectorStore()
            results = store.search_with_prefilter(
                query_embedding=query_vector,
                daerah=target_daerah,
                tahun=target_tahun,
                n_results=top_k
            )

        return results
