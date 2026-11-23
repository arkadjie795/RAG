# 🎓 MATERI TEKNIS LAPORAN MAGANG: SISTEM BASIS PENGETAHUAN & AI CHATBOT BPS KABUPATEN DEMAK (RAG3321)

Dokumen ini disusun sebagai materi rujukan teknis resmi (*technical reference material*) untuk penyusunan **Laporan Akhir Praktik Kerja Lapangan / Magang Mandiri di Badan Pusat Statistik (BPS) Kabupaten Demak**. Seluruh konten didasarkan secara ketat pada pekerjaan nyata yang telah diimplementasikan, memisahkan fakta pekerjaan riil dari rencana pengembangan lanjutan.

---

## 1. Identitas Proyek & Judul Laporan Magang yang Direkomendasikan

- **Judul Laporan Magang Disarankan:**  
  *"Rancang Bangun Sistem Konsultasi Data Statistik Cerdas Berbasis Retrieval-Augmented Generation (RAG) dan Hybrid Vector Database pada Badan Pusat Statistik Kabupaten Demak"*
- **Nama Sistem Operasional:** Sahabat Data BPS Kabupaten Demak (`RAG3321`)
- **Unit Kerja:** Tim Fungsi Integrasi Pengolahan dan Diseminasi Statistik (IPDS) / Seksi TI BPS Kabupaten Demak
- **Wilayah Kerja:** Kabupaten Demak, Provinsi Jawa Tengah (Kode Wilayah: 3321)

---

## 2. Latar Belakang Permasalahan

1. **Kompleksitas Format Publikasi Statistik:**  
   BPS Kabupaten Demak secara rutin menerbitkan publikasi resmi (seperti *Kabupaten Demak Dalam Angka* dan 14 publikasi *Kecamatan Dalam Angka*) dalam bentuk dokumen PDF ratusan halaman. Publikasi ini didominasi oleh tabel statistik hierarkis (*multi-index header*) yang sulit dibaca dan ditelusuri secara instan oleh masyarakat, akademisi, maupun perencana kebijakan.
2. **Kelemahan Pencarian Berbasis Kata Kunci Standar (Ctrl+F):**  
   Pencarian teks sederhana pada dokumen PDF tidak mampu memahami konteks kolom, baris, satuan data, dan wilayah kecamatan secara simultan.
3. **Resiko Halusinasi AI Konvensional:**  
   Penggunaan model bahasa besar (Large Language Models / LLM) secara mandiri (*standalone*) tanpa grounding data seringkali menghasilkan halusinasi (*confabulation*) berupa angka statistik palsu yang sangat berbahaya bagi integritas institusi BPS.
4. **Keunikan Notasi Statistik BPS:**  
   BPS memiliki standar notasi khusus seperti tanda strip (`-`) yang berarti kegiatan bernilai nihil (*NIL*), titik tiga (`...`) yang berarti data belum tersedia, dan tanda bintang (`*`) yang berarti angka sementara. Sistem AI standar sering salah mengartikan simbol tersebut sebagai angka nol atau karakter rusak.

---

## 3. Tujuan Pengembangan Sistem

1. Membangun basis data pengetahuan statistik digital terstruktur dari publikasi resmi PDF BPS Kabupaten Demak ke dalam PostgreSQL.
2. Mencegah halusinasi AI dengan menerapkan pendekatan *Retrieval-Augmented Generation* (RAG) ketat berbasis sitasi resmi (*mandatory citation*).
3. Mengembangkan formulasi semantik *Row-to-Speech* untuk merepresentasikan baris angka tabel statistik menjadi kalimat bahasa alami yang mudah dipahami model vektor.
4. Mengimplementasikan pencarian hibrida berkecepatan tinggi (*PostgreSQL HNSW Cosine Similarity + Indonesian Full-Text Search*) yang digabungkan menggunakan *Reciprocal Rank Fusion (RRF)*.
5. Menyediakan portal terpadu (*Dual-Portal SPA*) untuk publik (antarmuka konsultasi data ramah pemustaka) dan internal BPS (*Command Center* data, scraping, dan observabilitas vektor).

---

## 4. Tinjauan Pustaka & Teknologi yang Digunakan

| Komponen Arsitektur | Teknologi Terpilih | Justifikasi Ilmiah & Teknis |
| :--- | :--- | :--- |
| **Penyimpanan Vektor** | PostgreSQL 15 + `pgvector` v0.8.1 | Mendukung indeks HNSW berkecepatan $\mathcal{O}(\log N)$, eliminasi kebutuhan database vektor terpisah, dan terintegrasi langsung dengan SQL relasional institusi. |
| **Model Embedding** | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Model dense 384 dimensi yang sangat efisien dijalankan pada CPU lokal tanpa memerlukan kartu grafis (GPU) mahal, dengan akurasi semantik tinggi untuk Bahasa Indonesia. |
| **Mesin FTS** | PostgreSQL `tsvector` & GIN Index | Melengkapi pencarian semantik dengan pencarian leksikal eksak menggunakan kamus Bahasa Indonesia untuk menangkap akronim teknis (seperti IPM, PDRB, TPAK). |
| **Algoritma Fusion** | Reciprocal Rank Fusion (RRF, $k=60$) | Menggabungkan peringkat dari dense search dan sparse search secara matematis tanpa memerlukan normalisasi skor yang rentan bias. |
| **Backend API** | FastAPI (Python 3.10+) | Framework asinkron berkecepatan tinggi dengan validasi Pydantic otomatis dan kemampuan menyajikan API sekaligus berkas statis (*single-port serving*). |
| **Frontend UI** | Vue 3 + Tailwind CSS + Pinia | Antarmuka SPA reaktif modern, ringan, dan ramah pengguna telepon pintar (*mobile-friendly*). |
| **LLM Reasoning** | Google Gemini API (via REST v1beta) | Model penalaran canggih dengan context window besar, pemahaman konteks tabel rapi, dan latensi inferensi efisien. |

---

## 5. Metodologi Sistem & Tahapan Pemrosesan Data (ETL)

Sistem memproses data melalui 5 tahapan utama:

```
[1. Akuisisi Data] ──> [2. Ekstraksi & Cleaning] ──> [3. Row-to-Speech] ──> [4. Embedding Cache] ──> [5. Hybrid Storage]
```

1. **Akuisisi Data (Web API BPS Crawler):**  
   Modul crawler mengakses Web API resmi BPS (domain 3321) untuk mendeteksi katalog terbaru, mengunduh file PDF secara otomatis, dan mencatat hash SHA-256 pada SQLite registry guna mencegah redundansi.
2. **Ekstraksi Tabel & Normalisasi:**  
   Modul `pdfplumber` mengekstrak struktur tabel. Algoritma `detect_header_rows` memindai kedalaman hierarki header dan memipihkannya. Modul cleaner memetakan notasi statistik BPS (`-` dipertahankan sebagai status `ValueStatus.NIL`).
3. **Formulasi Semantik Row-to-Speech:**  
   Setiap baris angka statistik dikonversi menjadi kalimat deklaratif lengkap, contoh:  
   *"Berdasarkan Tabel: 'Jumlah Penduduk' (Kecamatan Demak Dalam Angka 2024, Tahun 2024): Pada Kecamatan 'Demak', nilai Jumlah Penduduk Laki-Laki adalah 54.120 Jiwa..."*
4. **Vektorisasi & Persistent Cache:**  
   Kalimat hasil sintesis di-hash menggunakan MD5. Sistem terlebih dahulu memeriksa tabel `embedding_cache` di PostgreSQL. Jika *cache-miss*, kalimat di-encode oleh SentenceTransformer MiniLM (384-d) dan hasilnya disimpan ke cache.
5. **Penyimpanan Hibrida:**  
   Vektor disimpan di tabel `vector_chunks` (diindeks HNSW), sedangkan struktur tabel mentah disimpan di tabel `statistical_tables` dalam format JSONB relasional.

---

## 6. Hasil Implementasi Nyata (Pekerjaan yang Telah Selesai)

Berikut adalah pencapaian konkret yang telah terpasang dan beroperasi di lingkungan BPS Demak:

1. **Basis Data Statistik Terstruktur:**  
   Berhasil mengekstrak dan menyimpan **8.905 tabel statistik** dan **218.517 vector chunks** dari **101 publikasi resmi BPS Demak** (termasuk Sensus Pertanian 2023 Tahap II dan seluruh Kecamatan Dalam Angka).
2. **Efisiensi Persistent Cache:**  
   Tersimpan **215.245 hash embedding** di PostgreSQL yang menghemat lebih dari 95% beban komputasi CPU saat pembaruan indeks berulang.
3. **Kecepatan Retrieval Tinggi:**  
   Pengujian kueri hibrida PostgreSQL HNSW + FTS + RRF membuktikan waktu pencarian konsisten berada di bawah **30 milidetik**.
4. **Penyajian Port Tunggal Mandiri (Single-Port Serving):**  
   FastAPI sukses melayani seluruh rute backend API sekaligus menyajikan antarmuka Vue 3 SPA dari port 8000 tanpa memerlukan server Node.js aktif di lingkungan produksi.
5. **Suite Pengujian Otomatis:**  
   Memiliki 24 kasus uji otomatis di direktori `tests/` yang mencakup unit testing, konektivitas database, integritas skema, dan benchmarking RAG.

---

## 7. Keterbatasan Sistem Saat Ini

Sebagai bentuk kejujuran akademis, berikut adalah batasan sistem yang perlu dicantumkan dalam laporan:
1. **Latensi Cloud API:** Respons percakapan membutuhkan waktu 3–10 detik karena ketergantungan pada koneksi internet ke API Google Gemini.
2. **Ketiadaan Streaming (SSE):** Teks jawaban muncul sekaligus setelah pemrosesan selesai, belum mendukung efek mengetik kata-per-kata secara real-time.
3. **Otorisasi Backend Masih Menggunakan Mock:** Integrasi login SIPETRA SSO masih menggunakan mekanisme *mock-login* karena kredensial OAuth2 resmi BPS belum dikonfigurasi pada server lokal.
4. **Dokumen Hasil Pindai (Scanned PDF):** Sistem baru optimal memproses PDF digital asli (teks vektor), belum dilengkapi modul OCR untuk dokumen cetak lama yang dipindai sebagai gambar.

---

## 8. Rekomendasi & Rencana Pengembangan Lanjutan

Rekomendasi tindakan yang dapat diusulkan untuk tim IT BPS Demak berikutnya:
1. **Implementasi Server-Sent Events (SSE):** Mengubah endpoint `/api/chat` menjadi streaming response untuk memangkas *perceived latency*.
2. **Pengamanan Otorisasi Token Backend:** Menambahkan middleware otentikasi Bearer Token pada rute ingestion untuk mencegah eksekusi scraper tanpa izin.
3. **Integrasi Neural Cross-Encoder Reranker:** Menerapkan model reranking sekunder (seperti `bge-reranker-base`) untuk kueri yang sangat ambigu.
4. **Penerapan Nginx Reverse Proxy & SSL:** Memasang Nginx dengan sertifikat HTTPS sebelum sistem dibuka untuk akses publik di luar jaringan kantor BPS.
