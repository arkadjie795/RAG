"""
Native PostgreSQL Hybrid Retrieval Engine.
Fuses pgvector HNSW dense cosine similarity with PostgreSQL Full-Text Search (tsvector)
using Reciprocal Rank Fusion (RRF).
"""
import json
import re
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

        # Extract specific desa/kelurahan if explicitly mentioned
        desa_match = re.search(r'\b(?:desa|kelurahan)\s+([a-zA-Z]+)', query, re.IGNORECASE)
        target_desa = desa_match.group(1) if desa_match else None
        desa_pattern = f"%{target_desa}%" if target_desa else None

        # 2. Compute query dense embedding
        query_vector = self.embedder.generate_embeddings([query])[0]
        emb_literal = "[" + ",".join(str(x) for x in query_vector) + "]"

        daerah_pattern = f"%{target_daerah}%" if target_daerah else None
        tahun_pattern = f"%{target_tahun}%" if target_tahun else None
        is_specific_kecamatan = bool(target_daerah and "kabupaten" not in target_daerah.lower())

        # Clean conversational query into salient keywords for lexical FTS
        stopwords = {
            'berapa', 'berapakah', 'apakah', 'apa', 'bagaimana', 'sebutkan', 'tampilkan',
            'menurut', 'publikasi', 'buku', 'dokumen', 'dalam', 'angka', 'data', 'tahun',
            'bps', 'di', 'pada', 'ke', 'dari', 'yang', 'ini', 'itu', 'tersebut', 'ada',
            'kabupaten', 'kecamatan', 'desa', 'kelurahan'
        }
        tokens = list(dict.fromkeys([
            w for w in re.findall(r'\b[a-zA-Z0-9]+\b', query.lower()) 
            if w not in stopwords and len(w) > 2
        ]))
        lexical_ts_query = " | ".join(tokens) if tokens else query

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
                  AND (%s::text IS NULL OR daerah ILIKE %s OR (NOT %s::boolean AND daerah ILIKE '%%Kabupaten Demak%%') OR representasi_teks ILIKE %s)
                  AND (%s::text IS NULL OR tahun = %s OR representasi_teks ILIKE %s)
                LIMIT 50
            ),
            lexical_candidates AS (
                SELECT 
                    chunk_id, 
                    representasi_teks, 
                    metadata,
                    ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, to_tsquery('indonesian', %s)) DESC) AS lex_rank
                FROM vector_chunks
                WHERE tsv @@ to_tsquery('indonesian', %s)
                  AND (%s::text IS NULL OR daerah ILIKE %s OR (NOT %s::boolean AND daerah ILIKE '%%Kabupaten Demak%%') OR representasi_teks ILIKE %s)
                  AND (%s::text IS NULL OR tahun = %s OR representasi_teks ILIKE %s)
                LIMIT 50
            )
            SELECT 
                COALESCE(d.chunk_id, l.chunk_id) AS chunk_id,
                COALESCE(d.representasi_teks, l.representasi_teks) AS representasi_teks,
                COALESCE(d.metadata, l.metadata) AS metadata,
                (
                    COALESCE(1.0 / ({rrf_k} + d.dense_rank), 0.0) + 
                    COALESCE(1.0 / ({rrf_k} + l.lex_rank), 0.0) +
                    CASE WHEN %s::text IS NOT NULL AND COALESCE(d.representasi_teks, l.representasi_teks) ILIKE %s THEN 0.05 ELSE 0.0 END
                ) AS score
            FROM dense_candidates d
            FULL OUTER JOIN lexical_candidates l ON d.chunk_id = l.chunk_id
            ORDER BY score DESC
            LIMIT %s;
        """

        params = (
            emb_literal, emb_literal,
            target_daerah, daerah_pattern, is_specific_kecamatan, daerah_pattern,
            target_tahun, target_tahun, tahun_pattern,
            lexical_ts_query, lexical_ts_query,
            target_daerah, daerah_pattern, is_specific_kecamatan, daerah_pattern,
            target_tahun, target_tahun, tahun_pattern,
            target_desa, desa_pattern,
            top_k
        )

        results = []
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL hnsw.ef_search = 300;")
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
