# 🧪 TEST EVIDENCE & EMPIRICAL RELIABILITY AUDIT

Dokumen ini memuat bukti empiris (*empirical evidence*) dari pelaksanaan pengujian otomatis (*automated test suite*), klasifikasi tipe pengujian (Unit, Integrasi Riil, Mocked), analisis *flaky tests*, serta dekonstruksi mendalam atas klaim "100% Akurasi".

---

## 1. Bukti Log Eksekusi Pengujian Aktual (Pytest Console Output)

Perintah yang dijalankan pada terminal:
`python -m pytest tests/ -v`

### Output Konsol Asli:
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\arkadjie\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\arkadjie\Documents\Documents\MAGANG BOSSS\IT\RAG
plugins: anyio-4.14.2, Faker-40.40.0
collecting ... collected 24 items

tests/benchmarks/test_golden_benchmark.py::test_golden_dataset_structure PASSED [  4%]
tests/benchmarks/test_golden_benchmark.py::test_conversational_and_abstention_benchmark PASSED [  8%]
tests/benchmarks/test_golden_benchmark.py::test_statistical_retrieval_benchmark PASSED [ 12%]
tests/test_backend_api_routers.py::test_public_chat_health PASSED        [ 16%]
tests/test_backend_api_routers.py::test_auth_status_and_login PASSED     [ 20%]
tests/test_backend_api_routers.py::test_sipetra_redirect_endpoint PASSED [ 25%]
tests/test_backend_api_routers.py::test_ingestion_status_and_run PASSED  [ 29%]
tests/test_backend_api_routers.py::test_data_viewer_endpoints PASSED     [ 33%]
tests/test_backend_api_routers.py::test_system_telemetry_endpoints PASSED [ 37%]
tests/test_chatbot_integration.py::test_chatbot_grounded_answer_pipeline PASSED [ 41%]
tests/test_chatbot_integration.py::test_rag_feeder_hybrid_retrieval_routing PASSED [ 45%]
tests/test_embedder_cache.py::test_embedder_caching_and_deterministic_storage PASSED [ 50%]
tests/test_embedder_cache.py::test_embedder_never_returns_random_hash PASSED [ 54%]
tests/test_extraction.py::TestTableCleaner::test_clean_table_dataframe_with_ffill PASSED [ 58%]
tests/test_extraction.py::TestTableCleaner::test_flatten_multi_index_headers PASSED [ 62%]
tests/test_extraction.py::TestTableCleaner::test_indonesian_numeric_sanitization PASSED [ 66%]
tests/test_hybrid_retrieval.py::test_demak_entity_extraction PASSED      [ 70%]
tests/test_hybrid_retrieval.py::test_hybrid_search_rrf_execution PASSED  [ 75%]
tests/test_pipeline_e2e.py::TestStructuringAndDocStore::test_table_json_structuring_and_text_representation PASSED [ 79%]
tests/test_postgres_connection.py::test_postgres_connection_and_pgvector PASSED [ 83%]
tests/test_postgres_schema.py::test_postgres_tables_exist PASSED         [ 87%]
tests/test_postgres_store.py::test_postgres_vector_store_crud_and_search PASSED [ 91%]
tests/test_statistical_semantics.py::test_statistical_symbol_semantics PASSED [ 95%]
tests/test_statistical_semantics.py::test_clean_table_dataframe_preserves_semantics PASSED [100%]

============================== warnings summary ===============================
  C:\Users\arkadjie\Documents\Documents\MAGANG BOSSS\IT\RAG\chatbot\config.py:10: PydanticDeprecatedSince20
  C:\Users\arkadjie\Documents\Documents\MAGANG BOSSS\IT\RAG\config\settings.py:9: PydanticDeprecatedSince20
  FastAPI TestClient StarletteDeprecationWarning

================== 24 passed, 4 warnings in 73.28s (0:01:13) ==================
```

---

## 2. Klasifikasi Tipe Pengujian (Unit vs Real Integration vs Mocked)

Untuk memastikan keabsahan teknis, seluruh 24 kasus uji diklasifikasikan berdasarkan mekanisme eksekusinya:

| Nama Modul Pengujian | Kasus Uji | Tipe Pengujian | Komponen Nyata yang Terlibat | Status |
| :--- | :--- | :---: | :--- | :---: |
| `test_golden_benchmark.py` | `test_golden_dataset_structure` | **Unit Test** | Memvalidasi integritas 30 baris skema JSON | **PASSED** |
| | `test_conversational_and_abstention_benchmark` | **Real Integration** | Memanggil model live LLM Google Gemini via internet | **PASSED** |
| | `test_statistical_retrieval_benchmark` | **Real Integration** | Query PostgreSQL HNSW + panggilan live Google Gemini | **PASSED** |
| `test_backend_api_routers.py` | `test_public_chat_health` | **Integration** | FastAPI TestClient HTTP call | **PASSED** |
| | `test_auth_status_and_login` | **Integration** | FastAPI TestClient + auth router | **PASSED** |
| | `test_sipetra_redirect_endpoint` | **Integration** | FastAPI TestClient + OAuth redirect builder | **PASSED** |
| | `test_ingestion_status_and_run` | **Integration** | Ingestion state machine + thread runner | **PASSED** |
| | `test_data_viewer_endpoints` | **Real Integration** | Membaca data langsung dari tabel PostgreSQL | **PASSED** |
| | `test_system_telemetry_endpoints` | **Real Integration** | Menghitung statistik live PostgreSQL `vector_chunks` | **PASSED** |
| `test_chatbot_integration.py` | `test_chatbot_grounded_answer_pipeline` | **Real Integration** | RAG Feeder + PostgreSQL + Google Gemini | **PASSED** |
| | `test_rag_feeder_hybrid_retrieval_routing` | **Real Integration** | Hybrid retriever HNSW + FTS RRF | **PASSED** |
| `test_embedder_cache.py` | `test_embedder_caching_and_deterministic_storage` | **Real Integration** | SentenceTransformer MiniLM + DB `embedding_cache` | **PASSED** |
| | `test_embedder_never_returns_random_hash` | **Unit Test** | Uji determinisme algoritma hash MD5 | **PASSED** |
| `test_extraction.py` | `test_clean_table_dataframe_with_ffill` | **Unit Test** | Logika manipulasi DataFrame pandas | **PASSED** |
| | `test_flatten_multi_index_headers` | **Unit Test** | Algoritma pemipihan header bertingkat | **PASSED** |
| | `test_indonesian_numeric_sanitization` | **Unit Test** | Parser angka titik/koma Indonesia | **PASSED** |
| `test_hybrid_retrieval.py` | `test_demak_entity_extraction` | **Unit Test** | Regex matcher 14 kecamatan Demak & tahun | **PASSED** |
| | `test_hybrid_search_rrf_execution` | **Real Integration** | Eksekusi kueri SQL CTE RRF pada PostgreSQL aktif | **PASSED** |
| `test_pipeline_e2e.py` | `test_table_json_structuring_and_text_representation` | **Unit Test** | Sintesis *Row-to-Speech* menjadi kalimat alami | **PASSED** |
| `test_postgres_connection.py` | `test_postgres_connection_and_pgvector` | **Real Integration** | Handshake TCP ke `10.133.21.24:5433` & cek pgvector | **PASSED** |
| `test_postgres_schema.py` | `test_postgres_tables_exist` | **Real Integration** | Query `information_schema.tables` di PostgreSQL | **PASSED** |
| `test_postgres_store.py` | `test_postgres_vector_store_crud_and_search` | **Real Integration** | CRUD dan kueri operator `<=>` di PostgreSQL aktif | **PASSED** |
| `test_statistical_semantics.py` | `test_statistical_symbol_semantics` | **Unit Test** | Evaluasi preservasi simbol BPS (`-`, `...`, `e`) | **PASSED** |
| | `test_clean_table_dataframe_preserves_semantics` | **Unit Test** | Verifikasi kolom angka tidak tercemar saat cleaning | **PASSED** |

### Rekapitulasi Tipe:
- **Unit Tests (Logika Murni Tanpa I/O Luar):** 9 tests (37.5%)
- **Real Integration Tests (PostgreSQL / LLM Live):** 15 tests (62.5%)
- **Mocked Tests:** 0 tests (0.0% — tidak ada mocking tiruan pada pengujian utama).
- **Skipped / Not Executed:** 0 tests.

---

## 3. Analisis Uji Flaky (Flaky Test Analysis)

Pengujian `test_statistical_retrieval_benchmark` dalam `tests/benchmarks/test_golden_benchmark.py` menunjukkan perilaku **flaky** (tidak deterministik terhadap waktu):
- Pada uji tanggal 13 November 2026: **FAILED** (Latensi 28.55s > batas toleransi 15.0s).
- Pada uji tanggal 16 November 2026: **PASSED** (Latensi berada di bawah 15.0s).

### Akar Penyebab:
Batas waktu `assert latency < 15.0` menggabungkan waktu pencarian lokal (< 30 ms) dengan panggilan internet ke Google AI Studio (`generativelanguage.googleapis.com`). Karena server Google Gemini terkadang mengalami antrean jaringan dan latensi inferensi variatif, unit test dapat gagal semata-mata karena gangguan jaringan trans-Pasifik, meskipun algoritma sistem bekerja 100% benar.

---

## 4. Dekonstruksi Kritis Klaim "100% Akurasi" (100% Accuracy Deconstruction)

Laporan awal mengklaim sistem memiliki akurasi 100%. Setelah diaudit secara teknis dan ilmiah:

### A. Isi Dataset Uji Aktual (`tests/benchmarks/golden_dataset.json`)
Dataset memuat 30 pertanyaan dengan struktur:
```json
{
  "id": "demak_pop_01",
  "question": "Berapa jumlah penduduk di Kecamatan Sayung pada tahun 2024?",
  "indicator": "Jumlah Penduduk",
  "region": "Sayung",
  "reference_year": "2024",
  "unit": "Jiwa",
  "answerable": true
}
```
**Perhatikan ketiadaan kolom:** `expected_answer`, `expected_numeric_value`, atau `ground_truth_text`.

### B. Implementasi Logika Uji pada `test_statistical_retrieval_benchmark`
```python
resp = bot.ask(case["question"], session_id=f"bench_{case['id']}")
assert resp["mode"] in ("rag_data", "conversational")
assert resp["answer"] is not None
assert latency < 15.0
```

### C. Kesimpulan Verifikasi:
Pengujian ini **HANYA MEMBUKTIKAN BAHWA**:
1. Pipeline tidak crash saat memproses kueri statistik.
2. Router berhasil mengklasifikasikan kueri ke mode `rag_data`.
3. LLM mengembalikan teks respons yang tidak kosong (`is not None`).

Pengujian ini **TIDAK PERNAH MEMVERIFIKASI BAHWA ANGKA YANG DIJAWAB OLEH LLM PERSIS SAMA DENGAN ANGKA TABEL RESMI BPS**. Jika LLM berhalusinasi menyebut angka yang salah, pengujian ini **TETAP AKAN DINYATAKAN LULUS (PASSED)**.

> **VONIS AUDITOR:**  
> **Klaim "Akurasi 100%" adalah KLAIM YANG TIDAK DAPAT DIPERTANGGUNGJAWABKAN SECARA ILMIAH KARENA BELUM TERSEDIA GROUND-TRUTH NUMERICAL BENCHMARK.**  
> Status yang benar adalah: **Pipeline Reliability: 100% (24/24 Tests Passed)**, sedangkan **Akurasi Statistik: UNPROVEN / BELUM TERUJI SECARA FORMAL**.
