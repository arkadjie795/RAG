"""
PostgreSQL Unified Vector and Metadata Store with pgvector HNSW Indexing.
Zero-dependency on C++ MSVC DLLs; high concurrency and ACID guarantees.
"""
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from config.database import get_db_connection


class PostgresVectorStore:
    """Manages Vector Storage and HNSW Semantic Search in PostgreSQL."""

    def __init__(self):
        pass

    def _sanitize_metadata(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Flattens and extracts metadata payload."""
        payload = {
            "dokumen_id": str(chunk.get("dokumen_id", "")),
            "dokumen_sumber": str(chunk.get("dokumen_sumber", "")),
            "daerah": str(chunk.get("daerah", "")),
            "kategori": str(chunk.get("kategori", "")),
            "tahun": str(chunk.get("tahun", "")),
            "tanggal_publikasi": str(chunk.get("tanggal_publikasi", "")),
            "halaman": int(chunk.get("halaman", 1)),
            "tipe_konten": str(chunk.get("tipe_konten", "")),
            "judul_tabel": str(chunk.get("judul_tabel", "")),
            "tabel_id": str(chunk.get("tabel_id", "")),
            "file_json_tabel": str(chunk.get("file_json_tabel", "")),
            "file_json_dokumen": str(chunk.get("file_json_dokumen", "")),
            "file_json_naratif": str(chunk.get("file_json_naratif", "")),
            "satuan": str(chunk.get("satuan", "")),
            "sumber": str(chunk.get("sumber", "")),
            "bab": str(chunk.get("bab", "")),
            "sub_bab": str(chunk.get("sub_bab", ""))
        }
        return {k: v for k, v in payload.items() if v != ""}

    def upsert_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100) -> int:
        """
        Upserts structured RAG chunks with 384-d pgvector embeddings and FTS tsvectors.
        """
        if not chunks:
            return 0

        total_upserted = 0
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    for c in batch:
                        meta = self._sanitize_metadata(c)
                        raw_emb = c.get("embedding", [])
                        emb_literal = "[" + ",".join(str(x) for x in raw_emb) + "]" if raw_emb else None

                        rep_text = c.get("representasi_teks", "")
                        halaman = c.get("halaman", 1)
                        try:
                            halaman = int(halaman)
                        except (ValueError, TypeError):
                            halaman = 1

                        cur.execute(
                            """
                            INSERT INTO vector_chunks (
                                chunk_id, doc_id, table_id, tipe_konten, daerah, kategori,
                                tahun, halaman, judul_tabel, satuan, sumber,
                                representasi_teks, metadata, embedding, tsv
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s,
                                %s, %s::jsonb, %s::vector, to_tsvector('indonesian', %s)
                            )
                            ON CONFLICT (chunk_id) DO UPDATE SET
                                doc_id = EXCLUDED.doc_id,
                                table_id = EXCLUDED.table_id,
                                tipe_konten = EXCLUDED.tipe_konten,
                                daerah = EXCLUDED.daerah,
                                kategori = EXCLUDED.kategori,
                                tahun = EXCLUDED.tahun,
                                halaman = EXCLUDED.halaman,
                                judul_tabel = EXCLUDED.judul_tabel,
                                satuan = EXCLUDED.satuan,
                                sumber = EXCLUDED.sumber,
                                representasi_teks = EXCLUDED.representasi_teks,
                                metadata = EXCLUDED.metadata,
                                embedding = EXCLUDED.embedding,
                                tsv = EXCLUDED.tsv;
                            """,
                            (
                                c["chunk_id"],
                                meta.get("dokumen_id", ""),
                                meta.get("tabel_id", ""),
                                meta.get("tipe_konten", "tabel_baris"),
                                meta.get("daerah", "Kabupaten Demak"),
                                meta.get("kategori", "Umum"),
                                str(meta.get("tahun", "")),
                                halaman,
                                meta.get("judul_tabel", ""),
                                meta.get("satuan", "N/A"),
                                meta.get("sumber", "BPS Kabupaten Demak"),
                                rep_text,
                                json.dumps(meta, ensure_ascii=False),
                                emb_literal,
                                rep_text
                            )
                        )
                    conn.commit()
                    total_upserted += len(batch)

        logger.info(f"[PostgresVectorStore] Upserted {total_upserted} chunks into PostgreSQL.")
        return total_upserted

    def search_with_prefilter(
        self,
        query_embedding: List[float],
        daerah: Optional[str] = None,
        tahun: Optional[str] = None,
        kategori: Optional[str] = None,
        tipe_konten: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Executes metadata-filtered dense cosine vector search using pgvector HNSW index.
        Returns top-N results with semantic similarity score (1 - cosine distance).
        """
        if not query_embedding:
            return []

        emb_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"

        where_clauses = ["embedding IS NOT NULL"]
        filter_params = []

        if daerah:
            where_clauses.append("daerah ILIKE %s")
            filter_params.append(f"%{daerah}%")
        if tahun:
            where_clauses.append("tahun = %s")
            filter_params.append(str(tahun))
        if kategori:
            where_clauses.append("kategori ILIKE %s")
            filter_params.append(f"%{kategori}%")
        if tipe_konten:
            where_clauses.append("tipe_konten = %s")
            filter_params.append(tipe_konten)

        where_sql = " AND ".join(where_clauses)
        params = [emb_literal] + filter_params + [emb_literal, n_results]

        sql = f"""
            SELECT 
                chunk_id,
                representasi_teks,
                metadata,
                (1.0 - (embedding <=> %s::vector)) AS score
            FROM vector_chunks
            WHERE {where_sql}
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
        """

        results = []
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
                for cid, rep_text, meta, score in rows:
                    results.append({
                        "chunk_id": cid,
                        "score": float(score) if score is not None else 0.0,
                        "representasi_teks": rep_text,
                        "metadata": meta if isinstance(meta, dict) else json.loads(meta or "{}")
                    })

        return results
