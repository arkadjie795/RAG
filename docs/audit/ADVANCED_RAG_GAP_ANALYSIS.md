# Phase 13 — Advanced RAG Gap Analysis

## 1. Executive Summary

Dokumen ini memetakan posisi teknologi RAG BPS Kabupaten Demak saat ini terhadap paradigma dan teknik mutakhir dalam ekosistem *State-of-the-Art* (SOTA) Retrieval-Augmented Generation. Analisis ini menyoroti kapabilitas yang telah berhasil diimplementasikan serta celah (*gaps*) yang dapat diintegrasikan pada iterasi berikutnya.

---

## 2. Matriks Komparasi Teknologi RAG (Current vs Advanced SOTA)

| Teknik / Paradigma RAG | Status Implementasi | Implementasi Aktual Saat Ini | Celah Teknis (Gap) & Dampak | Tingkat Prioritas |
| :--- | :---: | :--- | :--- | :---: |
| **Row-to-Speech Tabular Synthesis** | **IMPLEMENTED** | Mengonversi baris tabel statistik PDF menjadi kalimat alami terstruktur dengan preserve simbol NIL. | Tidak ada. Merupakan salah satu keunggulan terbesar arsitektur ini. | - |
| **Hybrid Search (Dense + Sparse)** | **IMPLEMENTED** | Dense vector cosine (HNSW) digabung dengan PostgreSQL Full-Text Search Bahasa Indonesia via RRF. | Skor RRF bersifat statis ($k=60$), belum menerapkan *learned weighting* adaptif. | Low |
| **Dynamic Entity Pre-filtering** | **IMPLEMENTED** | Regex 14 kecamatan Kabupaten Demak mengekstrak entitas kueri untuk menginjeksi klausa SQL WHERE. | Baru terbatas pada dimensi kecamatan; belum mengekstrak dimensi tahun rujukan (misal 2023) secara otomatis. | Medium |
| **Server-Sent Events (SSE) Streaming** | **NOT IMPLEMENTED** | Endpoint `/api/chat` mengembalikan full response secara sinkron (blocking hingga LLM selesai). | Pengguna harus menunggu 3–10 detik dalam keadaan layar diam sebelum teks muncul sekaligus. | **HIGH** |
| **Cross-Encoder Neural Reranking** | **NOT IMPLEMENTED** | Reranking hanya menggunakan algoritma matematis Reciprocal Rank Fusion (RRF). | Pada kueri yang sangat ambigu, RRF tidak mempertimbangkan interaksi semantik mendalam antara query dan passage seperti halnya model Cross-Encoder (misal `bge-reranker-base`). | Medium |
| **Hypothetical Document Embeddings (HyDE)** | **NOT IMPLEMENTED** | Kueri pengguna langsung di-embed tanpa transformasi. | Kueri singkat pengguna terkadang memiliki representasi vektor yang jauh dari teks tabel statistik formal. HyDE dapat membuat draf hipotetis sebelum embedding. | Low |
| **Query Expansion / Multi-Query** | **NOT IMPLEMENTED** | Hanya 1 representasi vektor per pertanyaan pengguna. | Istilah lokal atau singkatan (misal: "sawah bengkok", "IPM", "TPAK") berisiko miss jika tidak cocok dengan frasa publikasi. | Medium |
| **Graph RAG / Knowledge Graph** | **NOT IMPLEMENTED** | Penyimpanan berbasis relasional dan vektor chunk independen. | Tidak dapat menelusuri hubungan hierarkis antar-sektor (misal pengaruh gagal panen padi terhadap garis kemiskinan per kecamatan) secara graph traversal. | Low |
| **Agentic RAG / Multi-Hop Reasoning** | **PARTIAL** | Pipeline bersifat sequential linear (Query -> Retrieve -> Generate). | Tidak dapat melakukan query ulang secara otonom jika kueri pertama belum mendapatkan data yang memadai (*no reflection/retry loop*). | Medium |

---

## 3. Detail Analisis Celah Kritis

### A. Ketiadaan Streaming Response (SSE)
- **Kondisi Saat Ini**: Klien frontend Vue 3 mengirim request HTTP POST ke `/api/chat`. Backend menunggu panggilan LLM eksternal (Google Gemini) yang memakan waktu 3–15 detik, baru kemudian mengembalikan JSON lengkap.
- **Dampak UX**: Memberikan ilusi sistem "stuck" atau lambat bagi pengguna awam, terutama pada perangkat seluler atau jaringan lambat.
- **Rencana Peningkatan**: Ubah controller FastAPI menggunakan `StreamingResponse` dengan media type `text/event-stream` dan yield token dari client LLM secara asinkron.

### B. Ketiadaan Ekstraksi Temporal (Year Extraction)
- **Kondisi Saat Ini**: Kueri seperti *"Berapa jumlah penduduk Demak tahun 2020?"* hanya memicu pre-filter `district='Demak'`, sementara filter `year=2020` tidak terinjeksi ke SQL. Akibatnya, tabel tahun 2024 atau 2023 berpotensi ditarik ke dalam Top-5 chunk karena kemiripan semantik topik kependudukan.
- **Dampak Akurasi**: Mengharuskan LLM melakukan penalaran eliminasi tahun sendiri di dalam context prompt.

---

## 4. Kesimpulan Kematangan Arsitektur RAG

- **Level RAG Saat Ini**: **Level 3 (Advanced Modular RAG)**.
  - Sudah melampaui Naive RAG standar (berkat adanya pembersihan data tabular BPS, *row-to-speech*, PostgreSQL HNSW ganda, dan RRF).
  - Belum mencapai **Level 4 (Agentic & Graph RAG)** karena belum mendukung multi-agent loop, query rewriting iteratif, dan neural cross-reranker.
