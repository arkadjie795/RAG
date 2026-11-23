# 🏛️ PHASE 2: COMPLETE RAG ARCHITECTURE ANALYSIS
## Project: BPS Demak RAG Knowledge Base & AI Chatbot ("Sahabat Data BPS" / RAG3321)
**Auditor:** Multi-Disciplinary Forensic Engineering Team  
**Audit Date:** 2026-11-13  
**Classification:** Deep Architectural Deconstruction & Lifecycle Tracing  

---

### 1. Dekonstruksi Arsitektur Pipeline RAG

Arsitektur RAG3321 dirancang secara spesifik untuk memecahkan tantangan terbesar dokumen publikasi statistik: **data berbentuk tabel numerik padat dengan multi-level header yang sering kali rusak jika hanya menggunakan text parser generik biasa**.

Sistem ini terbagi ke dalam 5 pipeline utama:

```mermaid
flowchart TD
    subgraph INGEST["1. Ingestion Pipeline"]
        A["BPS Web API (webapi.bps.go.id)"] -->|JSON Metadata & PDF Stream| B["bps_api_client.py"]
        B -->|Deduplikasi SHA256/ID| C["registry.py (SQLite)"]
        B -->|Simpan PDF Utuh (100% Halaman)| D["data_publikasi/demak/"]
    end

    subgraph EXTRACT["2. Extraction & Sanitization"]
        D --> E["pdf_pipeline.py"]
        E -->|Scan Bounding Box Garis & Notasi BPS| F["table_extractor.py & table_cleaner.py"]
        E -->|Scan Paragraf Narasi (Filter Header/Footer)| G["text_extractor.py"]
        F -->|Preservasi Simbol '-' = NIL| H["Matriks Bersih & Flatten Headers"]
    end

    subgraph STRUCT["3. Structuring & Chunking"]
        H & G --> I["json_builder.py"]
        I -->|Row-to-Speech Formulation| J["RAG Chunks (representasi_teks)"]
        I -->|1 File JSON/Tabel| K["database/tables/"]
        I -->|1 File JSON/Dokumen| L["database/documents/"]
        I -->|1 File JSON/Narasi| M["database/narratives/"]
    end

    subgraph VEC["4. Vectorization & Storage"]
        J --> N["embedder.py (SentenceTransformer 384-d)"]
        N -->|Persistent Hash Cache| O["embedding_cache (PostgreSQL)"]
        N -->|Upsert Vektor & Metadata| P["postgres_store.py"]
        P -->|Indeks Cosine HNSW| Q["vector_chunks (pgvector)"]
        P -->|Indeks GIN Bahasa Indonesia| R["vector_chunks (tsvector FTS)"]
        K -->|Relational Tables JSONB| S["statistical_tables (PostgreSQL)"]
    end

    subgraph INFER["5. Dual-Mode Retrieval & LLM Generation"]
        T["Pengguna (Pertanyaan)"] --> U["bot.py (Intent Classifier)"]
        U -->|Salam / Obrolan Santai| V["Fast Conversational Mode (LLM Langsung)"]
        U -->|Pertanyaan Data Statistik| W["hybrid_search.py (Dense HNSW + Lexical FTS + RRF)"]
        Q & R --> W
        W -->|Top-K Chunks + Markdown Tables| X["rag_feeder.py (Context Formatter)"]
        X --> Y["llm_client.py (Google Gemini API REST)"]
        Y --> Z["Jawaban Terverifikasi + Kartu Sitasi Resmi"]
    end
```

---

### 2. Analisis Tahap per Tahap (Stage-by-Stage Forensic)

#### A. Document Ingestion Pipeline
1. **Mekanisme Pemasukan Dokumen:**
   - **Mode Resmi (Otomatis):** Menggunakan `BPSWebApiClient` yang menghubungi endpoint resmi BPS Web API (`https://webapi.bps.go.id/v1/api/`) dengan `domain: 3321` (Kabupaten Demak) dan API Key resmi. Ini mengeliminasi risiko pemblokiran WAF / F5 APM Bot Challenge yang kerap terjadi pada web scraper HTML biasa.
   - **Mode Manual (Lokal):** Operator dapat menaruh berkas PDF secara langsung di direktori `data_publikasi/demak/` atau memicu pengujian single dokumen.
2. **Format Dokumen:** Dokumen PDF resmi publikasi BPS (seperti *Kabupaten Demak Dalam Angka*, *Statistik Daerah*, *PDRB Menurut Lapangan Usaha*, *Kecamatan Dalam Angka*).
3. **Penanganan Duplikasi:** Menggunakan tabel SQLite `publications` di `database/bps_registry.db`. Setiap publikasi dilacak berdasarkan `publication_id`, tanggal rilis, dan ukuran berkas. Berkas yang sudah berstatus `DOWNLOADED` atau `PROCESSED` tidak akan diunduh ulang.
4. **Cakupan Halaman:** Parameter `MAX_EXTRACT_PAGES` disetel ke `None` pada konfigurasi produksi, memastikan **100% seluruh halaman dokumen PDF dari cover hingga halaman terakhir dibaca dan diproses tanpa pemotongan**.

#### B. Chunking Strategy (Tabular & Narrative Decomposition)
* **Filosofi Chunking:** Tidak menggunakan pemotongan karakter atau token acak (*fixed-size chunking* seperti 500 karakter dengan overlap 50 karakter) karena akan memotong tabel statistik dan merusak relasi antara judul kolom dan baris data.
* **Strategi Chunking Baris Tabel (*Row-Level Semantic Chunking*):**
  Setiap baris data tabel statistik diubah menjadi satu chunk independen yang menyertakan konteks lengkap secara hierarkis:
  Contoh representasi teks yang dihasilkan `json_builder.py`:
  > *"Berdasarkan Tabel: 'Jumlah Penduduk Menurut Kecamatan dan Jenis Kelamin di Kabupaten Demak' (Kabupaten Demak Dalam Angka 2026, Tahun 2026): Pada Kecamatan Mranggen, nilai Jumlah Penduduk Laki-laki adalah 105.432 Jiwa, nilai Jumlah Penduduk Perempuan adalah 104.521 Jiwa, nilai Total adalah 209.953 Jiwa."*
* **Strategi Chunking Narasi (*Paragraph-Level Semantic Chunking*):**
  Teks narasi diekstrak per paragraf logis, dilengkapi dengan metadata bab dan sub-bab, dengan margin filter yang membuang running header, nomor halaman, dan watermark BPS.
* **ID Chunk Deterministik:** Setiap chunk diberi ID unik menggunakan hashing MD5 dari teks konten dan ID dokumen (misal: `tbl_33210_2026_01_a9f8b2c1`), menjamin idempotensi saat proses re-indexing.

#### C. Embedding Pipeline & Persistent Caching
* **Model Embedding:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dimensi, float32, cosine similarity).
* **Mekanisme Caching Cerdas:**
  Sebelum memanggil model neural network, teks masukan dihitung MD5 hash-nya (`f"{model_name}:{clean_text}"`). Sistem mengecek tabel `embedding_cache` di PostgreSQL. Jika ditemukan (*cache hit*), vektor diambil langsung dari database (0.1 ms). Jika belum (*cache miss*), SentenceTransformer menghitung vektor secara batch lalu menyimpannya ke `embedding_cache`. Saat ini terdapat **10.378 embedding ter-cache**, menghemat 95%+ waktu komputasi ingestion berulang.
* **Ketiadaan Random Fallback:** Kode berbahaya warisan (`_generate_random_hash_vectors`) yang dahulu menghasilkan angka acak saat PyTorch gagal telah **dihapus total**. Jika model gagal dimuat, sistem melempar `RuntimeError` secara eksplisit demi integritas data.

#### D. Retrieval Pipeline (Native Hybrid Search & RRF)
Engine pencarian di [modules/retrieval/hybrid_search.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/modules/retrieval/hybrid_search.py) menggunakan kueri SQL tunggal di PostgreSQL yang menggabungkan dua metode komplementer:

1. **Dense Vector Search:**
   Menggunakan indeks HNSW pgvector dengan operator jarak Cosine:
   $$\text{dense\_sim} = 1.0 - (\text{embedding} \Leftrightarrow \text{query\_vector})$$
   Mengambil 30 kandidat teratas berdasarkan kedekatan semantik makna.
2. **Lexical Full-Text Search (BM25 / tsvector):**
   Menggunakan GIN index dengan parser bahasa Indonesia:
   $$\text{lex\_rank} = \text{ts\_rank\_cd}(\text{tsv}, \text{plainto\_tsquery}('\text{indonesian}', \text{query}))$$
   Mengambil 30 kandidat teratas berdasarkan kecocokan kata kunci eksak (misal: "PDRB", "Sayung", "2024", "Gabah").
3. **Reciprocal Rank Fusion (RRF):**
   Menggabungkan kedua daftar kandidat menggunakan rumus RRF standar industri:
   $$\text{RRF Score} = \frac{1}{k + \text{rank}_{\text{dense}}} + \frac{1}{k + \text{rank}_{\text{lexical}}} \quad (\text{dengan } k = 60.0)$$
4. **Dynamic Entity Pre-Filtering:**
   Sebelum kueri dikirim, `DemakEntityExtractor` mendeteksi entitas wilayah (14 kecamatan) dan tahun 4-digit secara otomatis dari kueri pengguna untuk mengisolasi partisi data yang relevan.

#### E. Generation Pipeline (Prompting & Grounding)
* **Prompt Construction:** Menggunakan template [chatbot/prompt_templates.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/prompt_templates.py).
* **Injeksi Markdown Tabel:** Selain representasi kalimat, jika chunk berasal dari tabel, [chatbot/rag_feeder.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/rag_feeder.py) membaca file JSON tabel granular asli dari disk dan menyusun tabel Markdown 20 baris pertama untuk diberikan kepada LLM sebagai *ground truth* tabular visual.
* **Pencegahan Halusinasi & Aturan Notasi Statistik:**
  Prompt sistem secara eksplisit mewajibkan LLM:
  1. Hanya menjawab berdasarkan data yang ada pada konteks yang diinjeksikan.
  2. Jika data tidak ada dalam tabel, katakan dengan sopan bahwa data belum tercatat dalam publikasi resmi BPS Demak yang terindeks (*strict abstention*).
  3. Memahami arti tanda minus (`-` = tidak ada data / nihil), bukan mengartikannya sebagai angka nol jika keterangannya berbeda.
  4. Selalu menyertakan nama publikasi, tahun rilis, dan nomor halaman sebagai sitasi resmi.

---

### 3. Lifecycle Permintaan Pengguna (End-to-End Request Trace)

```
USER QUERY: "Berapa jumlah penduduk Kecamatan Sayung tahun 2024?"
       │
       ▼
1. INPUT VALIDATION: Memeriksa panjang string dan karakter kueri
       │
       ▼
2. INTENT CLASSIFICATION (`is_conversational_or_greeting()`):
   - Apakah salam santai ("Halo", "Terima kasih")? TIDAK.
   - Mengandung entitas data statistik ("jumlah penduduk", "Sayung", "2024").
   - Diarahkan ke: MODE RAG DATA TERSTRUKTUR.
       │
       ▼
3. QUERY EXPANSION & FOLLOW-UP RESOLUTION (`_resolve_followup_query()`):
   - Menggabungkan konteks percakapan sebelumnya jika pengguna bertanya tindak lanjut (misal: "kalau yang perempuan?").
       │
       ▼
4. ENTITY EXTRACTION (`DemakEntityExtractor`):
   - Terdeteksi: `kecamatan = "Sayung"`, `tahun = "2024"`.
       │
       ▼
5. HYBRID RETRIEVAL (`HybridRetriever.search()`):
   - Dense Vector HNSW: Menghitung jarak embedding ke 10.682 chunk pgvector.
   - Lexical FTS: Menghitung skor `ts_rank_cd` pada indeks teks penuh Bahasa Indonesia.
   - RRF Merging: Mengurutkan kandidat terbaik berdasarkan bobot gabungan dense + leksikal.
       │
       ▼
6. CONTEXT SYNTHESIS (`RAGFeeder.feed_context()`):
   - Membaca file JSON granular tabel `database/tables/...`.
   - Mengompilasi format markdown tabel dan ringkasan kalimat semantik.
   - Mengompilasi kartu metadata sitasi (dokumen, halaman, tahun).
       │
       ▼
7. PROMPT INJECTION (`DATA_QUERY_PROMPT_TEMPLATE`):
   - Menggabungkan System Persona BPS + Riwayat Sesi (3 turn terakhir) + Konteks Data Tabel + Pertanyaan Pengguna.
       │
       ▼
8. LLM INVOCATION (`LLMClient.generate()`):
   - Mengirim payload ke Google Gemini REST API (`gemini-3.1-flash-lite`, temp: 0.2).
   - Menghasilkan jawaban faktual dan presisi.
       │
       ▼
9. CITATION COMPILATION & RESPONSE BUNDLING:
   - Output JSON: `{ "answer": "...", "citations": [...], "chunks": [...], "type": "rag_data" }`.
       │
       ▼
10. FINAL DISPLAY (Vue 3 / Streamlit):
    - Teks jawaban terformat rapi + Badge Sitasi Resmi BPS Demak + Drawer Proof of Data.
```
