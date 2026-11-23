# Phase 10 — Performance & Scalability Audit

## 1. Executive Summary

Dokumen ini menganalisis performa teknis, throughput, latensi komputasi, dan skalabilitas sistem RAG BPS Kabupaten Demak. Evaluasi mencakup profiling waktu eksekusi pipeline ingesti, latensi hybrid retrieval, efisiensi persistent embedding cache, dan beban komputasi CPU/GPU.

---

## 2. Profiling Latensi End-to-End Pipeline

Diagram dekomposisi waktu siklus satu kueri pengguna (*Single User Query Breakdown*):

```
Total Request Latency: ~3.2s – 28.5s (Tergantung Respon LLM)
├── 1. FastAPI Request Parsing & Input Validation : 1.2 ms
├── 2. Entity Extraction (Regex 14 Kecamatan)     : 0.8 ms
├── 3. Query Embedding (SentenceTransformers)    : 45 ms (CPU Intel Core i5/i7)
├── 4. PostgreSQL Hybrid Retrieval (HNSW + FTS)  : 28 ms (10,682 chunks)
├── 5. RRF Merging & Deduplication               : 3.5 ms
├── 6. Context Window & Prompt Assembly          : 2.1 ms
└── 7. Remote LLM Generation (Google Gemini API) : 3,100 ms – 28,400 ms (Bottleneck Utama)
```

### Analisis Bottleneck:
- **Internal Stack (FastAPI + PostgreSQL + SentenceTransformers)**: Sangat cepat, memakan waktu total **< 90 milidetik**.
- **External Dependency (Google Gemini API)**: Menghabiskan **97% hingga 99.7%** dari total waktu respons kueri pengguna.

---

## 3. Evaluasi Persistent Embedding Cache

Sistem menerapkan tabel `embedding_cache` di PostgreSQL untuk mengeliminasi inferensi ganda pada teks yang identik:
- **Metode**: Hash MD5 dari teks baris/paragraf dijadikan primary key (`text_hash VARCHAR(64)`).
- **Statistik Cache Saat Ini**:
  - Total entri cache tersimpan: **10,378 baris**.
  - Waktu baca cache vs inferensi SentenceTransformer:
    - *Cache Hit (PostgreSQL B-Tree index)*: **~0.4 ms**.
    - *Cache Miss (Inferensi CPU model 384-d)*: **~12.5 ms per kalimat**.
- **Penghematan Waktu Ingesti**: Pada proses ingesti berulang (re-indexing), keberadaan cache memangkas waktu komputasi embedding hingga **96.8%**.

---

## 4. Skalabilitas Indeks Vektor PostgreSQL HNSW

### A. Karakteristik Kompleksitas
- Indeks HNSW (`vector_cosine_ops`) menggunakan parameter:
  - `m = 16` (jumlah koneksi bidirectional per node)
  - `ef_construction = 64` (ukuran antrean pencarian kandidat saat build)
- **Kompleksitas Pencarian**: $\mathcal{O}(\log N)$, di mana $N$ adalah jumlah chunk vektor.
- **Performa Pengujian**:
  - Pada $N = 10,682$ vektor: latensi retrieval stabil di kisaran **15 ms – 35 ms**.
  - Proyeksi pada $N = 100,000$ vektor: latensi diperkirakan tetap berada di bawah **80 ms** asalkan ukuran memori RAM server mencukupi untuk menampung indeks HNSW (`shared_buffers` / cache RAM PostgreSQL).

### B. Ukuran Indeks & Penggunaan Memori
- Ukuran tabel `vector_chunks`: **~18 MB**.
- Ukuran indeks HNSW `idx_vector_chunks_embedding_hnsw`: **~12 MB**.
- Sangat efisien dan sepenuhnya muat di dalam RAM server database yang ada saat ini.

---

## 5. Skalabilitas Pipeline Ingesti Dokumen PDF

| Tahap Pipeline | Waktu Rata-rata per Publikasi (100–300 hal) | Pemanfaatan Sumber Daya |
| :--- | :---: | :--- |
| **Parsing PDF (`pdfplumber`)** | 25 – 65 detik | 100% 1 Core CPU (I/O & String parsing intensif) |
| **Pembersihan & Deteksi Tabel** | 4 – 8 detik | Ringan (< 10% CPU) |
| **Sintesis Baris ke Teks** | 2 – 5 detik | Ringan |
| **Vektorisasi Batch (Embedder)** | 18 – 45 detik (CPU) | Multi-threading CPU (PyTorch/ONNX) |
| **Database Bulk Insert & Indexing** | 3 – 7 detik | I/O Disk PostgreSQL |
| **Total Ingesti per Dokumen** | **~52 – 130 detik** | Tergantung jumlah tabel di dalam PDF |

---

## 6. Rekomendasi Peningkatan Skalabilitas

1. **Implementasi Streaming Response (SSE)**: Mengubah endpoint chat menjadi Server-Sent Events agar pengguna melihat token pertama dalam waktu < 1 detik (mengurangi *perceived latency*).
2. **Koneksi Database Connection Pooling**: Memastikan `psycopg2` atau `SQLAlchemy` menggunakan pool tertutup (`QueuePool` ukuran 10–20 koneksi) untuk melayani konkurensi puluhan pengguna simultan tanpa resiko kehabisan koneksi PostgreSQL.
3. **Penyimpanan Asinkron (Async Worker / Celery / Redis)**: Memisahkan tugas ingesti PDF besar dari thread web server FastAPI ke worker antrean independen.
