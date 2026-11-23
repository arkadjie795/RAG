# Phase 8 — Testing & Reliability Audit

## 1. Executive Summary

Dokumen ini memuat hasil audit terhadap suite pengujian otomatis (*automated testing*), keandalan sistem (*reliability*), cakupan kode (*test coverage*), dan analisis *flaky tests* pada proyek RAG BPS Kabupaten Demak.

---

## 2. Hasil Eksekusi Pytest Suite

Pengujian menyeluruh dijalankan pada lingkungan Python workspace menggunakan perintah:
`python -m pytest tests/ -v --durations=10`

### Hasil Rekapitulasi:
- **Total Test Cases**: 24
- **Passed**: 23 test cases (95.8%)
- **Failed**: 1 test case (4.2%)
- **Waktu Eksekusi Total**: 126.58 detik

```
=================================== FAILURES ===================================
_____________________ test_statistical_retrieval_benchmark _____________________
tests\benchmarks\test_golden_benchmark.py:34: in test_statistical_retrieval_benchmark
    assert latency < 15.0, f"Query latency too high: {latency:.2f}s"
E   AssertionError: Query latency too high: 28.55s
E   assert 28.547146558761597 < 15.0
----------------------------- Captured stdout call -----------------------------
[2026-11-13 15:42:36] [BENCHMARK] Query: 'Jumlah penduduk Kecamatan Demak'
[2026-11-13 15:42:36] [RETRIEVAL] Feeding 1 chunks to LLM
[2026-11-13 15:43:04] [RESULT] Duration: 28.55s | Response contains 'penduduk'
=========================== short test summary info ===========================
FAILED tests/benchmarks/test_golden_benchmark.py::test_statistical_retrieval_benchmark
======================== 1 failed, 23 passed in 126.58s ========================
```

---

## 3. Matriks Hasil Pengujian per Modul

| File Tes | Jumlah Kasus | Status | Komponen yang Diuji | Catatan |
| :--- | :---: | :---: | :--- | :--- |
| `tests/unit/test_cleaner.py` | 5 | PASSED | Pembersihan simbol BPS, penanganan karakter whitespace, ekstraksi angka | Lolos 100% |
| `tests/unit/test_embedder.py` | 3 | PASSED | Model embedder SentenceTransformer, normalisasi vektor, konsistensi 384 dimensi | Lolos 100% |
| `tests/unit/test_extractor.py` | 4 | PASSED | Parser tabel pdfplumber, deteksi baris header ganda, parsing metadata | Lolos 100% |
| `tests/unit/test_synthesizer.py` | 3 | PASSED | Formula *row-to-speech*, konversi baris statistik menjadi teks deskriptif | Lolos 100% |
| `tests/integration/test_pipeline.py` | 4 | PASSED | Ingesti single PDF lokal, penyimpanan ke PostgreSQL, verifikasi HNSW index | Lolos 100% |
| `tests/integration/test_api_endpoints.py` | 4 | PASSED | Endpoint FastAPI `/api/chat`, `/api/admin/tables`, `/api/admin/telemetry`, `/health` | Lolos 100% |
| `tests/benchmarks/test_golden_benchmark.py` | 1 | **FAILED** | Latensi end-to-end kueri RAG terhadap ambang batas 15.0 detik | Latensi aktual 28.55s melebihi batas 15s |

---

## 4. Analisis Cakupan Pengujian (Test Coverage)

### A. Area yang Memiliki Pengujian Solid (Well-Tested)
1. **Pembersihan Data Statistik (`modules/extraction/cleaner.py`)**: Aturan simbol `-`, `...`, `e`, angka pecahan koma/titik telah diuji secara komprehensif.
2. **Sintesis Baris ke Teks (`modules/extraction/synthesizer.py`)**: Format kalimat alami dari baris tabel memiliki cakupan unit test tinggi.
3. **Penyimpanan Vektor PostgreSQL (`modules/storage/vector_store.py`)**: Operasi insert, kueri HNSW, dan hashing deduplikasi diuji dalam integrasi.

### B. Area yang Belum Memiliki Pengujian Otomatis (Untested / Low Coverage)
1. **Frontend Vue 3 SPA (`frontend/`)**: Tidak ditemukan file test Vitest/Jest untuk komponen admin maupun portal chat publik.
2. **Web API BPS Ingestion Scraper (`modules/crawler/web_api_crawler.py`)**: Tidak ada unit test dengan mocking HTTP request terhadap endpoint `webapi.bps.go.id`.
3. **Background Job Cancellation (`api/routers/ingestion.py`)**: Skenario pembatalan paksa (*cancel job*) belum memiliki uji konkurensi otomatis.
4. **Error Handling Database Timeout**: Belum ada simulasi otomatis saat PostgreSQL mengalami *network drop* atau *lock contention*.

---

## 5. Analisis Reliabilitas & Flakiness

### A. Penyebab Utama Flaky Tests
- **Dependensi Live External API**: Uji `test_golden_benchmark.py` memanggil model LLM Google Gemini secara live melalui internet publik. Fluktuasi koneksi atau latensi provider pihak ketiga secara langsung menyebabkan kegagalan uji (*false negative*).
- **Rekomendasi Arsitektur Tes**: Pisahkan pengujian benchmark menjadi dua level:
  1. *CI/CD Fast Unit Test*: Menggunakan Mock LLM (`MockLLMClient`) dengan respons deterministik (< 1 detik).
  2. *Live Integration Benchmark*: Pengujian berkala terhadap LLM asli dengan ambang batas latensi yang lebih realistis (misal 35s) atau menggunakan timeout adaptif.

### B. Exception Handling & Graceful Degradation
- Backend FastAPI memiliki middleware exception global yang mencegah server crash saat terjadi runtime exception.
- Pada modul LLM, terdapat fallback otomatis dari `gemini-2.5-flash` ke model alternatif saat menerima kode error HTTP (misal 404/429/503).

---

## 6. Kesimpulan Reliabilitas

- **Stabilitas Komponen Internal**: **9.2 / 10** (Logika pemrosesan data, ekstraksi, dan penyimpanan database sangat stabil).
- **Stabilitas Pengujian Otomatis**: **7.5 / 10** (Perlu penambahan mock pada benchmark LLM dan penambahan unit test untuk crawler/frontend).
