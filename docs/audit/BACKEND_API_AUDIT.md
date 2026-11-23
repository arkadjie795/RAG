# 🔌 PHASE 6: BACKEND API AUDIT
## Project: BPS Demak RAG Knowledge Base & AI Chatbot ("Sahabat Data BPS" / RAG3321)
**Auditor:** Multi-Disciplinary Forensic Engineering Team  
**Audit Date:** 2026-11-13  
**Classification:** REST Endpoints, Schema Validation, Security, and Concurrency Review  

---

### 1. Daftar Lengkap Endpoint REST API

Aplikasi FastAPI terpusat di [chatbot/api.py](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/chatbot/api.py) dan memuat sub-router dari direktori [api/routers/](file:///c:/Users/arkadjie/Documents/Documents/MAGANG%20BOSSS/IT/RAG/api/routers/).

| Endpoint | HTTP Method | Router / Lokasi | Fungsi & Tanggung Jawab | Skema Input (Request) | Skema Output (Response) | Autentikasi | Status |
|:---|:---:|:---|:---|:---|:---|:---:|:---:|
| `/api/chat` | `POST` | `chatbot/api.py:114` | Endpoint utama inferensi AI Chatbot publik & RAG | `ChatRequest`: `{ message, session_id, daerah, tahun, kategori, top_k }` | `{ answer, citations, chunks, type, session_id }` | Publik (None) | **AKTIF (PROD)** |
| `/api/session/{id}` | `DELETE` | `chatbot/api.py:119` | Mereset riwayat percakapan sesi tertentu | Path param: `session_id` (str) | `{ status: "success", message: "..." }` | Publik (None) | **AKTIF (PROD)** |
| `/api/health` | `GET` | `chatbot/api.py:125` | Healthcheck dasar untuk load balancer / Docker | None | `{ status: "healthy", service: "..." }` | Publik (None) | **AKTIF (PROD)** |
| `/api/auth/me` | `GET` | `api/routers/auth.py:54` | Memeriksa profil user yang sedang login | Header: `Authorization: Bearer <token>` | `{ authenticated: bool, user: {...} \| null }` | Optional Bearer | **AKTIF (PROD)** |
| `/api/auth/mock-login` | `POST` | `api/routers/auth.py:69` | Login bypass lokal untuk dev/offline | `MockLoginRequest`: `{ username, name, nip, role }` | `{ status, access_token, user }` | Publik (None) | **AKTIF (PROD)** |
| `/api/auth/sipetra/redirect` | `GET` | `api/routers/auth.py:90` | Menghasilkan URL otorisasi SSO SIPETRA | Query: `client_redirect` (optional) | 302 Redirect atau `{ auth_url: "..." }` | Publik (None) | **AKTIF (PROD)** |
| `/api/auth/sipetra/callback` | `GET` | `api/routers/auth.py:120` | Callback pertukaran kode OAuth2 SIPETRA | Query: `code`, `state`, `error` | 302 Redirect ke `/admin` dengan token query | Publik (None) | **AKTIF (PROD)** |
| `/auth/callback` | `GET` | `chatbot/api.py:97` | Alias top-level untuk callback SIPETRA | Query: `code`, `state`, `error` | Meneruskan ke `sipetra_callback()` | Publik (None) | **AKTIF (PROD)** |
| `/api/ingestion/status` | `GET` | `api/routers/ingestion.py:149` | Membaca status real-time scraper job | None | `{ status, progress_pct, current_phase, processed_items, total_items, logs: [...] }` | Publik (None) | **AKTIF (PROD)** |
| `/api/ingestion/run` | `POST` | `api/routers/ingestion.py:155` | Memicu eksekusi crawler di background thread | `ScraperRunRequest`: `{ mode, max_pages, pdf_path }` | `{ status: "RUNNING", job_id, mode, message }` | Admin Token (Diinginkan) | **AKTIF (PROD)** |
| `/api/data/publications` | `GET` | `api/routers/data_viewer.py:15` | Daftar master publikasi BPS terindeks | Query: `tahun`, `kategori`, `limit`, `offset` | `{ success: true, total: int, items: [...] }` | Publik (None) | **AKTIF (PROD)** |
| `/api/data/tables` | `GET` | `api/routers/data_viewer.py:78` | Daftar tabel statistik terstruktur | Query: `search`, `kecamatan`, `tahun`, `kategori`, `limit`, `page` | `{ success: true, total: int, items: [...] }` | Publik (None) | **AKTIF (PROD)** |
| `/api/data/tables/{table_id}` | `GET` | `api/routers/data_viewer.py:145` | Detail satu tabel statistik lengkap | Path param: `table_id` (str) | `{ success: true, data: { kolom, records, ... } }` | Publik (None) | **AKTIF (PROD)** |
| `/api/data/tables/{table_id}/json` | `GET` | `api/routers/data_viewer.py:180` | File JSON mentah per-tabel dari disk | Path param: `table_id` (str) | Raw JSON dictionary | Publik (None) | **AKTIF (PROD)** |
| `/api/data/categories` | `GET` | `api/routers/data_viewer.py:195` | Daftar kategori unik publikasi BPS | None | `{ success: true, categories: [...] }` | Publik (None) | **AKTIF (PROD)** |
| `/api/data/districts` | `GET` | `api/routers/data_viewer.py:205` | Daftar 14 kecamatan resmi Kabupaten Demak | None | `{ success: true, districts: [...] }` | Publik (None) | **AKTIF (PROD)** |
| `/api/system/health` | `GET` | `api/routers/system_telemetry.py:26`| Pemeriksaan kesehatan DB & model AI | None | `{ status, database_connected, pgvector, llm_provider }` | Publik (None) | **AKTIF (PROD)** |
| `/api/system/vector-stats` | `GET` | `api/routers/system_telemetry.py:64`| Statistik chunk, cache, & tabel | None | `{ success: true, total_chunks, cached_embeddings, total_tables, ... }` | Publik (None) | **AKTIF (PROD)** |
| `/api/system/test-search` | `POST` | `api/routers/system_telemetry.py:111`| Form uji live retrieval hybrid pgvector | `SearchTestRequest`: `{ query, daerah, tahun, top_k }` | `{ success: true, total_results, results: [...] }` | Publik (None) | **AKTIF (PROD)** |
| `/api/system/logs` | `GET` | `api/routers/system_telemetry.py:136`| Membaca baris log backend Loguru | Query: `limit: int` (default 50) | `{ success: true, total_lines, logs: [...] }` | Publik (None) | **AKTIF (PROD)** |

---

### 2. Audit Kualitas Implementasi Endpoint

#### A. Request Validation & Pydantic Schemas
* Seluruh endpoint `POST` menggunakan model validasi Pydantic (`ChatRequest`, `MockLoginRequest`, `ScraperRunRequest`, `SearchTestRequest`).
* Input disanitasi: string whitespace di-strip, string `undefined` atau `null` dari query frontend dibersihkan secara eksplisit pada layer router (`buildCleanQuery` di frontend dan sanitasi di `data_viewer.py`).

#### B. CORS Configuration
* Dikonfigurasi pada `chatbot/api.py:81` menggunakan `CORSMiddleware`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
* *Evaluasi:* Sangat baik untuk fase pengembangan dan intranet deployment. Namun untuk peladen publik BPS ber-domain publik, disarankan mengganti `allow_origins=["*"]` dengan domain spesifik (misal: `https://demakkab.bps.go.id`).

#### C. Background Processing & Thread Safety
* Endpoint `/api/ingestion/run` mengeksekusi pipeline di background thread menggunakan `threading.Thread(target=_run_crawler_task, daemon=True)`.
* State tracking dikelola oleh singleton `job_manager = IngestionJobState()`.
* Penggunaan `threading.RLock()` mencegah deadlock saat update status dan penulisan log dilakukan secara bersamaan dari thread yang sama.

#### D. Kelemahan & Celah Akses Endpoint (Security Vulnerability Finding)
* **Kelemahan Otorisasi Endpoint Ingestion:**
  Endpoint `POST /api/ingestion/run` saat ini **belum diproteksi secara ketat dengan middleware otorisasi bearer token** di sisi backend FastAPI (validasi token baru diterapkan di sisi client router Vue).
  * *Risiko:* Pengguna luar yang mengetahui endpoint ini dapat memicu proses crawling di latar belakang secara sembarangan tanpa login terlebih dahulu.
  * *Rekomendasi:* Tambahkan dependency injection `Depends(verify_token)` pada endpoint `POST /api/ingestion/run`.
