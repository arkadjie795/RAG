# Phase 17 — RAG Development Roadmap (Levels 0–5)

## 1. Executive Summary

Roadmap pengembangan ini menyajikan panduan terstruktur langkah demi langkah untuk menyempurnakan sistem RAG BPS Kabupaten Demak dari level fungsional saat ini hingga mencapai kapabilitas *Autonomous Agentic & Graph RAG* tingkat lanjut. Setiap tugas dilengkapi dengan ID tugas (*Task ID*), tingkat prioritas, file yang terdampak, dan kriteria keberhasilan.

---

## 2. Peta Tahapan Pengembangan (Levels 0 to 5)

```
[Level 0: Fondasi & Stabilisasi] ──> Selesai (100%)
[Level 1: Hybrid Retrieval & Data Ingestion] ──> Selesai (95%)
[Level 2: Dual Portal & Unified Serving] ──> Selesai (92%)
[Level 3: Streaming UX & Security Hardening] ──> Prioritas Utama Berikutnya (Dalam Rencana)
[Level 4: Advanced Cross-Encoder & Temporal Guard] ──> Tahap Menengah
[Level 5: Agentic Multi-Hop & Graph RAG] ──> Visi Masa Depan
```

---

## 3. Rincian Rencana Tindakan per Level

### Level 3: Streaming UX & Security Hardening (Target Segera / Prioritas Tinggi)

| Task ID | Nama Tugas | Prioritas | File yang Terdampak | Kriteria Selesai (Definition of Done) |
| :---: | :--- | :---: | :--- | :--- |
| **TSK-301** | Implementasi Server-Sent Events (SSE) Streaming | **CRITICAL** | `api/routers/chat.py`, `chatbot/bot.py`, `frontend/src/views/ChatView.vue` | Endpoint `/api/chat/stream` mengembalikan token teks secara real-time via `EventSource`; UI menampilkan efek mengetik tanpa jeda. |
| **TSK-302** | Pengamanan Backend Ingestion Endpoint | **HIGH** | `api/routers/ingestion.py`, `api/dependencies.py` | Seluruh request ke `POST /api/ingestion/run` menolak akses jika tidak menyertakan Bearer Token valid. |
| **TSK-303** | Pembatasan Origin CORS Terkendali | **MEDIUM** | `api/main.py` | `allow_origins` dibatasi hanya ke hostname yang diizinkan (bukan wildcard `*`). |
| **TSK-304** | Validasi Magic Bytes & Kuota Upload PDF | **MEDIUM** | `api/routers/ingestion.py` | Upload file menolak ekstensi palsu (validasi `%PDF-`) dan payload melebihi 50 MB. |

---

### Level 4: Advanced Reranking & Temporal Reasoning (Tahap Menengah)

| Task ID | Nama Tugas | Prioritas | File yang Terdampak | Kriteria Selesai (Definition of Done) |
| :---: | :--- | :---: | :--- | :--- |
| **TSK-401** | Integrasi Neural Cross-Encoder Reranker | **HIGH** | `chatbot/rag_feeder.py`, `requirements.txt` | Top-15 kandidat dari RRF dinilai ulang menggunakan model Cross-Encoder (misal `BAAI/bge-reranker-base`) sebelum diserahkan ke LLM. |
| **TSK-402** | Ekstraksi Filter Temporal (Tahun Rujukan) | **HIGH** | `chatbot/rag_feeder.py` | Regex mendeteksi 4 digit tahun (2015–2026) pada kueri untuk menginjeksi filter `metadata->>'year' = :year` ke SQL. |
| **TSK-403** | Dynamic Query Rewriting / Expansion | **MEDIUM** | `chatbot/bot.py` | LLM melakukan dekomposisi kueri pengguna menjadi 2 varian sinonim statistik sebelum proses retrieval. |

---

### Level 5: Agentic Multi-Hop & Graph Reasoning (Visi Jangka Panjang)

| Task ID | Nama Tugas | Prioritas | File yang Terdampak | Kriteria Selesai (Definition of Done) |
| :---: | :--- | :---: | :--- | :--- |
| **TSK-501** | Multi-Table Aggregation Agent | **LOW** | `chatbot/agent/` | Kemampuan membandingkan tren data antar 3 publikasi berbeda dalam satu siklus penalaran otonom (*autonomous reasoning loop*). |
| **TSK-502** | Knowledge Graph Traversal (Apache AGE / Neo4j) | **LOW** | `modules/storage/graph_store.py` | Menghubungkan entitas kecamatan, komoditas, dan indikator kemiskinan dalam format graf berarah. |
| **TSK-503** | Otomasi Cron Sync Web API BPS | **MEDIUM** | `scripts/cron_sync.py` | Penjadwalan mingguan otomatis untuk memeriksa rilis publikasi baru tanpa intervensi manual operator. |

---

## 4. Estimasi Alokasi Sumber Daya

- **Penyelesaian Level 3 (Streaming & Security)**: Membutuhkan estimasi waktu 2–3 hari kerja pengembang.
- **Penyelesaian Level 4 (Cross-Encoder & Temporal)**: Membutuhkan waktu 3–5 hari kerja pengembang.
- **Penyelesaian Level 5 (Agentic RAG)**: Membutuhkan waktu 2–3 minggu riset dan implementasi.
