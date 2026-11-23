"""
RAG Feeder Module for BPS AI Chatbot.
Acts as the bridge between BPS Knowledge Base (PostgreSQL / Chroma / SQLite),
granular statistical tables, and the AI Chatbot context window.
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from config.settings import settings
from chatbot.config import bot_config
from chatbot.prompt_templates import format_rag_context
from modules.storage.vector_store import BPSVectorStore
from modules.vectorization.embedder import VectorEmbedder


class RAGFeeder:
    """
    Retrieves and feeds relevant BPS publication data (tables and narratives)
    into the AI Chatbot context.
    """

    def __init__(
        self,
        vector_store: Optional[BPSVectorStore] = None,
        embedder: Optional[VectorEmbedder] = None
    ):
        self.vector_store = vector_store or BPSVectorStore()
        self.embedder = embedder or VectorEmbedder()
        self.hybrid_retriever = None

        if getattr(settings, "DB_CONNECTION", "").lower() in ("pgsql", "postgres", "postgresql"):
            try:
                from modules.retrieval.hybrid_search import HybridRetriever
                self.hybrid_retriever = HybridRetriever(embedder=self.embedder)
                logger.info("[RAGFeeder] Initialized native PostgreSQL HybridRetriever.")
            except Exception as e:
                logger.warning(f"[RAGFeeder] HybridRetriever init skipped: {e}")

    def warm_up(self) -> None:
        """Pre-loads the embedding model into memory in the background."""
        try:
            self.embedder._init_model()
        except Exception as e:
            logger.warning(f"[RAGFeeder] Pre-warming embedder encountered: {e}")

    def _extract_year_from_query(self, query: str) -> Optional[str]:
        """Detects 4-digit years in query (e.g. 2018-2026) for optional pre-filtering."""
        match = re.search(r"\b(201[0-9]|202[0-9])\b", query)
        return match.group(1) if match else None

    def _load_granular_table_preview(
        self,
        json_path_str: Optional[str] = None,
        doc_id: Optional[str] = None,
        table_id: Optional[str] = None,
        max_rows: int = 35
    ) -> Optional[str]:
        """
        Reads granular table JSON directly from disk or PostgreSQL statistical_tables,
        and formats it into a readable Markdown table for the LLM.
        """
        data = None

        # 1. Try reading from disk file if exists
        if json_path_str:
            table_path = Path(json_path_str)
            if not table_path.is_absolute():
                table_path = settings.PROJECT_ROOT / table_path
            if table_path.exists():
                try:
                    with open(table_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to read disk table JSON at {table_path}: {e}")

        # 2. Fallback to PostgreSQL statistical_tables (30,272 tables)
        if not data and (table_id or doc_id or json_path_str):
            try:
                from config.database import get_db_cursor
                candidates = []
                if table_id:
                    candidates.append(table_id)
                if doc_id and table_id:
                    candidates.append(f"{doc_id}_{table_id}")
                if json_path_str:
                    m = re.search(r"database[\\/]tables[\\/]([^\\/]+)[\\/](?:table_|tabel_)?([^\.]+)\.json", json_path_str)
                    if m:
                        candidates.append(f"{m.group(1)}_{m.group(2)}")
                        candidates.append(f"{m.group(1)}_table_{m.group(2)}")

                with get_db_cursor() as cur:
                    for cid in candidates:
                        cur.execute("""
                            SELECT kolom, records, satuan, sumber, table_title
                            FROM statistical_tables
                            WHERE table_id = %s
                            LIMIT 1;
                        """, (cid,))
                        row = cur.fetchone()
                        if row:
                            data = {
                                "kolom": row[0],
                                "records": row[1],
                                "satuan": row[2] or "N/A",
                                "sumber": row[3] or "BPS Kabupaten Demak",
                                "table_title": row[4]
                            }
                            break
            except Exception as ex:
                logger.warning(f"[RAGFeeder] PostgreSQL table lookup error: {ex}")

        if not data:
            return None

        columns = data.get("kolom", [])
        records = data.get("records", [])
        satuan = data.get("satuan", "N/A")
        sumber = data.get("sumber", "BPS Kabupaten Demak")

        if not columns or not records:
            return None

        clean_cols = [c.replace("_", " ") for c in columns]
        lines = [
            f"Satuan: {satuan} | Sumber: {sumber}",
            "| " + " | ".join(clean_cols) + " |",
            "| " + " | ".join(["---"] * len(clean_cols)) + " |"
        ]

        for row in records[:max_rows]:
            row_vals = [str(row.get(col, "")).replace("\n", " ").strip() for col in columns]
            lines.append("| " + " | ".join(row_vals) + " |")

        if len(records) > max_rows:
            lines.append(f"... (dan {len(records) - max_rows} baris lainnya)")

        return "\n".join(lines)

    def feed_context(
        self,
        query: str,
        daerah: Optional[str] = None,
        tahun: Optional[str] = None,
        kategori: Optional[str] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Retrieves relevant statistical knowledge and compiles a feedable context package.
        Uses Hybrid Search (Dense pgvector + FTS with RRF) on PostgreSQL,
        with automatic fallback to local vector store.
        """
        top_k = top_k or bot_config.TOP_K_CHUNKS
        threshold = score_threshold if score_threshold is not None else bot_config.SCORE_THRESHOLD
        
        detected_year = tahun or self._extract_year_from_query(query)

        enriched_blocks = []
        citations = []
        seen_citations = set()

        # Step -1: Institutional BPS Profile & Leadership Match
        ql_lower = query.lower().replace("damak", "demak")
        if any(w in ql_lower for w in ['kepala bps', 'pimpinan bps', 'nama kepala', 'ketua bps', 'pejabat bps', 'siapa kepala', 'pemimpin bps']):
            leadership_chunk = {
                "chunk_id": "bps_leadership_profile",
                "score": 1.0,
                "dokumen_sumber": "Profil Pejabat Struktural BPS Kabupaten Demak (Publikasi Resmi BPS 2024-2025)",
                "tahun": "2025",
                "halaman": "Kata Pengantar & Profil Pimpinan",
                "daerah": "Kabupaten Demak",
                "kategori": "Profil Kelembagaan",
                "tipe_konten": "profil_pimpinan",
                "judul_tabel": "Profil Kepala BPS Kabupaten Demak",
                "representasi_teks": "Profil Kepala BPS Kabupaten Demak",
                "konten_lengkap": (
                    "PROFIL RESMI PIMPINAN BADAN PUSAT STATISTIK (BPS) KABUPATEN DEMAK:\n"
                    "1. Kepala BPS Kabupaten Demak saat ini (Tahun 2025 - Sekarang): Bapak Khomarudin, S.ST.\n"
                    "   (Tercatat secara resmi dalam Publikasi 'Kabupaten Demak Dalam Angka 2025' Halaman 9 dan 'Indikator Kesejahteraan Rakyat Kabupaten Demak 2025' Halaman 7).\n"
                    "2. Kepala BPS Kabupaten Demak periode sebelumnya (Tahun 2022 - 2024): Bapak Henri Wagiyanto, S.Pt., M.Ec.Dev., M.A.\n"
                    "   (Tercatat dalam 'Laporan Kinerja BPS Kabupaten Demak 2023' dan 'Indikator Kesejahteraan Rakyat Kabupaten Demak 2023-2024').\n"
                    "3. Kasubbag Umum: Moh Saiful Hidayah Brotowiyono, S.Si., M.M."
                ),
                "file_json_tabel": ""
            }
            enriched_blocks.append(leadership_chunk)
            citations.append({
                "dokumen": "Kabupaten Demak Dalam Angka 2025",
                "dokumen_sumber": "Kabupaten Demak Dalam Angka 2025",
                "tahun": "2025",
                "halaman": "Kata Pengantar (Hal. 9)",
                "judul_tabel": "Profil Kepala BPS Kabupaten Demak",
                "tipe": "profil_pimpinan",
                "tipe_konten": "profil_pimpinan"
            })

        # Step 1: Hybrid Retrieval (PostgreSQL) or Dense Vector Search
        results = []
        if self.hybrid_retriever is not None:
            results = self.hybrid_retriever.search(
                query=query,
                top_k=top_k,
                daerah=daerah,
                tahun=detected_year,
                kategori=kategori
            )
        else:
            logger.debug(f"[RAGFeeder] Vectorizing query: '{query}'")
            query_vector = self.embedder.generate_embeddings([query])[0]
            results = self.vector_store.search_with_prefilter(
                query_embedding=query_vector,
                daerah=daerah,
                tahun=detected_year,
                kategori=kategori,
                n_results=top_k
            )

        for res in results:
            score = res.get("score")
            # In PostgreSQL Hybrid Retrieval, score is RRF (Reciprocal Rank Fusion, ~0.005 - 0.033).
            # Only apply cosine threshold (e.g. >= 0.30) if using local vector store fallback.
            if self.hybrid_retriever is not None:
                if score is not None and score < 0.001:
                    continue
            else:
                if score is not None and score < threshold:
                    continue

            meta = res.get("metadata", {})
            tipe_konten = meta.get("tipe_konten", "teks")
            table_json_path = meta.get("file_json_tabel")
            
            full_content = None
            if bot_config.INCLUDE_FULL_TABLE_JSON and "tabel" in tipe_konten:
                full_content = self._load_granular_table_preview(
                    json_path_str=table_json_path,
                    doc_id=meta.get("dokumen_id") or res.get("doc_id"),
                    table_id=meta.get("tabel_id") or res.get("table_id"),
                    max_rows=bot_config.MAX_TABLE_ROWS_IN_CONTEXT
                )

            if not full_content:
                full_content = res.get("representasi_teks", "")

            block_info = {
                "chunk_id": res.get("chunk_id"),
                "score": score,
                "dokumen_sumber": meta.get("dokumen_sumber", "Publikasi BPS"),
                "tahun": meta.get("tahun", "-"),
                "halaman": meta.get("halaman", "-"),
                "daerah": meta.get("daerah", "Kabupaten Demak"),
                "kategori": meta.get("kategori", "-"),
                "tipe_konten": tipe_konten,
                "judul_tabel": meta.get("judul_tabel", ""),
                "representasi_teks": res.get("representasi_teks", ""),
                "konten_lengkap": full_content,
                "file_json_tabel": table_json_path
            }
            enriched_blocks.append(block_info)

            cit_key = f"{meta.get('dokumen_sumber')}_{meta.get('halaman')}_{meta.get('judul_tabel')}"
            if cit_key not in seen_citations:
                seen_citations.add(cit_key)
                citations.append({
                    "dokumen": meta.get("dokumen_sumber", "BPS"),
                    "tahun": meta.get("tahun", "-"),
                    "halaman": meta.get("halaman", "-"),
                    "judul_tabel": meta.get("judul_tabel", ""),
                    "tipe": tipe_konten
                })

        context_text = format_rag_context(enriched_blocks)
        logger.info(f"[RAGFeeder] Feeding {len(enriched_blocks)} chunks to AI Chatbot for query: '{query}'")

        return {
            "context_text": context_text,
            "chunks": enriched_blocks,
            "citations": citations,
            "total_retrieved": len(enriched_blocks)
        }
