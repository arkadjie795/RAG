"""
Vectorization and Embedding Module for BPS RAG Pipeline.
Generates 384-dimensional dense semantic embeddings using SentenceTransformers
with PostgreSQL persistent cache and batch processing.
"""
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger

from config.settings import settings


class VectorEmbedder:
    """Handles dense semantic embedding generation with persistent caching and batch inference."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None
        self._memory_cache: Dict[str, List[float]] = {}

    def _init_model(self):
        """Initializes the primary SentenceTransformer model."""
        if self._model is not None:
            return

        try:
            import os
            import warnings
            os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            warnings.filterwarnings("ignore")

            try:
                from transformers.utils import logging as tf_logging
                tf_logging.disable_progress_bar()
                tf_logging.set_verbosity_error()
            except Exception:
                pass

            try:
                from huggingface_hub.utils import disable_progress_bars, logging as hf_logging
                disable_progress_bars()
                hf_logging.set_verbosity_error()
            except Exception:
                pass

            logger.info(f"[Embedder] Loading SentenceTransformer model: '{self.model_name}'...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            logger.info("[Embedder] Successfully loaded SentenceTransformer model.")
        except Exception as e:
            logger.error(f"[Embedder] Critical error loading SentenceTransformer '{self.model_name}': {e}")
            raise RuntimeError(
                f"Embedding model '{self.model_name}' could not be loaded: {e}. "
                "Ensure sentence-transformers and PyTorch are properly installed."
            )

    def _compute_hash(self, text: str) -> str:
        """Computes deterministic MD5 hash of model + normalized text for cache key."""
        clean = text.strip()
        return hashlib.md5(f"{self.model_name}:{clean}".encode("utf-8")).hexdigest()

    def _get_cached_embeddings_pg(self, hashes: List[str]) -> Dict[str, List[float]]:
        """Fetches precomputed embeddings from PostgreSQL embedding_cache table."""
        if not hashes:
            return {}
        try:
            from config.database import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT text_hash, embedding FROM embedding_cache WHERE text_hash = ANY(%s);",
                        (hashes,)
                    )
                    rows = cur.fetchall()
                    result = {}
                    for h, emb in rows:
                        # pgvector returns string or list-like; parse to float list
                        if isinstance(emb, str):
                            clean_emb = [float(x) for x in emb.strip("[]").split(",") if x.strip()]
                            result[h] = clean_emb
                        elif isinstance(emb, (list, np.ndarray)):
                            result[h] = [float(x) for x in emb]
                    return result
        except Exception as e:
            logger.debug(f"[Embedder] Database cache lookup skipped or failed ({e}). Using in-memory cache.")
            return {}

    def _save_cached_embeddings_pg(self, records: List[Dict[str, Any]]) -> None:
        """Saves newly computed embeddings to PostgreSQL embedding_cache table."""
        if not records:
            return
        try:
            from config.database import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    for rec in records:
                        emb_literal = "[" + ",".join(str(x) for x in rec["embedding"]) + "]"
                        cur.execute(
                            """
                            INSERT INTO embedding_cache (text_hash, model_name, embedding)
                            VALUES (%s, %s, %s::vector)
                            ON CONFLICT (text_hash) DO NOTHING;
                            """,
                            (rec["text_hash"], self.model_name, emb_literal)
                        )
                conn.commit()
        except Exception as e:
            logger.debug(f"[Embedder] Failed to persist embeddings to database cache: {e}")

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generates normalized dense embeddings for textual chunks.
        Utilizes 2-tier caching:
        1. In-memory dictionary cache
        2. PostgreSQL persistent embedding_cache table
        Computes neural embeddings only for cache-miss chunks.
        """
        if not texts:
            return []

        sanitized_texts = [t.strip() if t and t.strip() else "Data Kosong" for t in texts]
        hashes = [self._compute_hash(t) for t in sanitized_texts]

        # 1. Check in-memory cache
        final_embeddings: List[Optional[List[float]]] = [self._memory_cache.get(h) for h in hashes]

        # 2. Check PostgreSQL cache for missing items
        missing_indices = [i for i, emb in enumerate(final_embeddings) if emb is None]
        if missing_indices:
            missing_hashes = [hashes[i] for i in missing_indices]
            pg_cached = self._get_cached_embeddings_pg(missing_hashes)
            for idx in missing_indices:
                h = hashes[idx]
                if h in pg_cached:
                    final_embeddings[idx] = pg_cached[h]
                    self._memory_cache[h] = pg_cached[h]

        # 3. Compute neural embeddings for remaining uncached items
        still_missing_indices = [i for i, emb in enumerate(final_embeddings) if emb is None]
        if still_missing_indices:
            self._init_model()
            texts_to_compute = [sanitized_texts[i] for i in still_missing_indices]

            computed: np.ndarray = self._model.encode(
                texts_to_compute,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=True,
                convert_to_numpy=True
            )

            to_persist_pg = []
            for sub_idx, orig_idx in enumerate(still_missing_indices):
                emb_list = [float(x) for x in computed[sub_idx].tolist()]
                final_embeddings[orig_idx] = emb_list
                h = hashes[orig_idx]
                self._memory_cache[h] = emb_list
                to_persist_pg.append({
                    "text_hash": h,
                    "embedding": emb_list
                })

            # Save newly computed embeddings to PostgreSQL
            self._save_cached_embeddings_pg(to_persist_pg)

        return [emb for emb in final_embeddings]

    def embed_rag_chunks(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """Attaches vector embeddings to RAG chunks."""
        if not chunks:
            return []

        texts_to_embed = [chunk["representasi_teks"] for chunk in chunks]
        embeddings = self.generate_embeddings(texts_to_embed, batch_size=batch_size)

        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb

        logger.info(f"[Embedder] Attached {len(embeddings)} embeddings to RAG chunks.")
        return chunks
