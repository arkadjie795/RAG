# 🔒 SECURITY RE-VERIFICATION: AUDIT ULANG KEAMANAN SIBER & KERENTANAN

Dokumen ini memverifikasi postur keamanan siber sistem RAG BPS Kabupaten Demak secara independen melalui inspeksi statis kode sumber dan analisis vektor serangan potensial tanpa melakukan pengujian penetrasi destruktif.

---

## 1. Matriks Re-Verifikasi Keamanan (Security Matrix)

| Aspek Keamanan | Temuan / Kondisi Aktual | Tingkat Resiko | Bukti Implementasi / Kode | Rekomendasi Remedi |
| :--- | :--- | :---: | :--- | :--- |
| **Secrets Hygiene** | Seluruh kredensial (API Key BPS, Password PostgreSQL, Gemini Key) tersimpan di `.env` lokal dan terdaftar di `.gitignore`. Tidak ada token yang bocor ke riwayat Git. | **LOW (AMAN)** | `.env`, `.gitignore` (L1-L15) | Pertahankan. Untuk staging server, gunakan secret vault (Docker Secrets / HashiCorp Vault). |
| **CORS Policy** | Middleware CORS pada FastAPI dikonfigurasi dengan wildcard (`allow_origins=["*"]`), mengizinkan browser dari sembarang domain memanggil API. | **MEDIUM** | `chatbot/api.py` (L81-L87) | Batasi ke whitelist terpercaya: `["http://localhost:5173", "http://10.133.21.24", "https://demakkab.bps.go.id"]`. |
| **SQL Injection** | Kueri pencarian vektor dan leksikal menggunakan *parameterized queries* bawaan driver `psycopg2`. FTS menggunakan `plainto_tsquery('indonesian', %s)`. | **LOW (AMAN)** | `modules/retrieval/hybrid_search.py` (L85-L93) | Tidak ada konkatenasi string SQL mentah dari input pengguna. Aman dari serangan injeksi SQL standar. |
| **Backend Auth on Ingestion** | Endpoint `POST /api/ingestion/run` dan `POST /api/ingestion/stop` tidak memiliki dependency `Depends(verify_token)`. Proteksi saat ini baru ada di level navigasi Vue Router. | **HIGH** | `api/routers/ingestion.py` (L166-L195) | Tambahkan dependency validasi header Bearer Token pada router FastAPI di backend. |
| **Public Chat Endpoint Access** | Endpoint `POST /api/chat` dapat diakses publik tanpa login. Ini sesuai kebutuhan chatbot publik, namun belum memiliki proteksi *rate-limiting*. | **MEDIUM** | `chatbot/api.py` (L113-L116) | Tambahkan middleware rate limiter (misal: `slowapi` atau batas 20 request per menit per IP) untuk mencegah abuse/DoS biaya API. |
| **Path Traversal pada Mode PDF** | Parameter `pdf_path` pada `ScraperRunRequest` menerima string path relatif/absolut. | **MEDIUM** | `api/routers/ingestion.py` (L140-L145) | Batasi pembacaan file hanya di dalam subdirektori aman `data_publikasi/` menggunakan `Path.resolve().is_relative_to()`. |
| **Prompt Injection Resistance** | Prompt sistem mendefinisikan batasan peran ketat sebagai Sahabat Data BPS Demak dan mewajibkan sitasi. Namun belum memiliki modul *adversarial input classifier*. | **LOW / MEDIUM** | `chatbot/prompt_templates.py` (L15-L65) | LLM patuh pada instruksi penolakan sopan, namun kueri injeksi kompleks berisiko mengaburkan konteks jika kueri sangat panjang. |

---

## 2. Analisis Rinci: Resiko Otorisasi Endpoint Admin

### A. Kondisi Aktual
Pada frontend Vue 3, navigasi rute `/admin/*` dijaga oleh Navigation Guard:
```javascript
// frontend/src/router.js (L109-L115)
const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
const token = getAuthToken()
if (requiresAuth && !token) {
    return next({ path: '/admin/login', query: { redirect: to.fullPath } })
}
```
Namun, jika seorang aktor jahat langsung menembakkan perintah HTTP cURL atau script Python ke endpoint backend:
```bash
curl -X POST http://10.133.21.24:8000/api/ingestion/run \
  -H "Content-Type: application/json" \
  -d '{"mode": "all", "max_pages": 50}'
```
Backend FastAPI akan langsung mengeksekusi job deep crawling tanpa meminta otentikasi apapun. Hal ini berpotensi menyebabkan *Denial of Service (DoS)* dan kehabisan memori server (*Resource Exhaustion*).

### B. Solusi Perbaikan Teknis (Non-Destructive Recommendation)
Tambahkan dependency `verify_token` pada `api/routers/ingestion.py`:
```python
from api.routers.auth import verify_token
from fastapi import Header, HTTPException

def require_admin(authorization: Optional[str] = Header(None)):
    user = verify_token(authorization)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Memerlukan hak akses Admin BPS")

@router.post("/run", dependencies=[Depends(require_admin)])
def run_ingestion(...):
    ...
```

---

## 3. Evaluasi Kebersihan Kredensial (Credential Hygiene)

Audit memeriksa seluruh commit git (`git log -p`) dan file source code:
- **Status:** **TERVERIFIKASI BERSIH**.
- Tidak ditemukan kata sandi database maupun kunci Google Gemini yang di-hardcode ke dalam file kode Python maupun template Vue.
- File `.env` yang berada di direktori lokal diabaikan secara tepat oleh aturan `.gitignore`.
- Seluruh variabel sensitif dibaca melalui modul terpusat `config/settings.py` dan `chatbot/config.py`.

---

## 4. Skor Postur Keamanan Sistem

| Parameter Audit Keamanan | Skor Mentah (0–100) | Keterangan |
| :--- | :---: | :--- |
| **Manajemen Secret & Kredensial** | 90 | Terkelola di `.env`, tidak ada kebocoran di git. |
| **Sanitasi Kueri & Anti-SQLi** | 92 | Parameterized SQL query konsisten. |
| **Proteksi Jaringan & CORS** | 60 | Wildcard `*` perlu dipersempit. |
| **Otorisasi Server-Side API** | 50 | Membutuhkan middleware token pada rute ingestion. |
| **Ketahanan Prompt Injection** | 80 | Sistem grounding ketat dan aturan abstensi aktif. |
| **RATA-RATA POSTUR KEAMANAN** | **74.4%** | **Cukup untuk Intranet, Butuh Pengerasan untuk Internet Publik** |
