# 📋 LAPORAN HASIL AUDIT TEKNIS & PANDUAN PENGEMBANGAN SISTEM RAG3321
**Proyek:** Sahabat Data BPS Kabupaten Demak (RAG3321)  
**Tujuan Dokumen:** Bahan Edukasi, Refleksi Teknis Rekayasa Perangkat Lunak, dan Panduan Diskusi Pengembangan Lanjutan untuk Rekan-Rekan Tim / Mahasiswa Magang BPS.  
**Tanggal:** 9 November 2026  
**Status Audit & Perbaikan:** Selesai & Terverifikasi (18/18 Unit & Benchmark Tests Passed)

---

## 🌟 1. Apresiasi Awal untuk Tim Pengembang / Mahasiswa Magang

Pertama-tama, **apresiasi setinggi-tingginya** kepada rekan-rekan mahasiswa magang yang telah berhasil merancang dan menginisiasi prototipe awal sistem **RAG3321**! 

Membangun pipeline dari ekstraksi PDF publikasi BPS (`pdfplumber`), pembentukan konteks tabular, integrasi Sentence-Transformers, hingga pembuatan bot percakapan adalah pencapaian yang sangat solid untuk proyek magang. Pondasi logika yang dibangun sudah mencerminkan pemahaman yang baik tentang arsitektur *Retrieval-Augmented Generation* (RAG).

Laporan audit ini **bukan bertujuan mencari kesalahan**, melainkan sebagai wadah pembelajaran (*learning opportunity*) mengenai perbedaan antara **Prototipe Akademik/Eksperimen** dengan **Sistem Produksi Enterprise Tingkat Instansi Pemerintah (BPS)** yang mengutamakan integritas data, akurasi mutlak, dan keandalan sistem.

---

## 🔍 2. Temuan Audit Krusial & Pelajaran Berharga (*Lessons Learned*)

Berikut adalah 5 temuan teknis utama yang telah diaudit dan diperbaiki ke tingkat standar industri statistik:

### 💡 Pelajaran 1: Integritas Data Statistik (Simbol Strip `-` Bukan Nol!)
* **Kondisi Sebelumnya:** Pada `table_cleaner.py`, setiap kali tabel menemukan sel berisi strip `-`, kode otomatis mengonversinya menjadi angka `0`.
* **Mengapa Ini Fatal di BPS?**  
  Dalam standar metadata statistik resmi BPS:
  * Angka `0` berarti **ada kegiatan/objek dan nilainya nol mutlak**.
  * Simbol `-` berarti **data tidak ada / nihil / tidak dapat dihitung**.
  * Simbol `...` berarti data belum tersedia / belum selesai dihimpun.
  * Simbol `r` berarti data revisi sementara.  
  Jika `-` dipaksa menjadi `0`, maka perhitungan rata-rata (*mean*), total agregat, atau analisis data oleh AI akan menghasilkan kesimpulan yang salah (misalnya menyimpulkan suatu kecamatan gagal panen padahal datanya hanya nihil/tidak tercatat).
* **Solusi Perbaikan:**  
  Dibuat struktur kelas semantik `StatisticalCell`. Nilai `-` sekarang dilestarikan dengan status `ValueStatus.NIL` dan `raw_value='-'`, sehingga AI dapat menjelaskan secara jujur: *"Data untuk kecamatan tersebut berstatus nihil / tidak ada data dalam tabel resmi BPS"*.

---

### 💡 Pelajaran 2: Bahaya "Degradasi Senyap" (*Silent Failure*) dari Pseudo-Random Hash
* **Kondisi Sebelumnya:** Pada `embedder.py`, terdapat blok penanganan error (`try-except`) di mana jika model `sentence_transformers` gagal dimuat karena kehabisan memori atau dependensi kurang, sistem secara otomatis membuat vektor tiruan menggunakan `hashlib.md5(text).hexdigest()`.
* **Mengapa Ini Berbahaya?**  
  Secara tampilan kode tidak ada pesan error (*silent failure*), tetapi secara fungsional:
  * Vektor MD5 acak memiliki korelasi semantik **0%**.
  * Akibatnya, pencarian data menjadi acak (*garbage in, garbage out*).
  * Chatbot tetap menjawab dengan percaya diri, tetapi mengutip data dari tabel acak yang salah, memicu halusinasi fatal.
* **Solusi Perbaikan:**  
  Penghapusan total fallback random hash. Di sistem produksi, jika model AI gagal dimuat, sistem harus memberikan error eksplisit (*fail-fast*) atau memanfaatkan *persistent embedding cache* di database PostgreSQL.

---

### 💡 Pelajaran 3: Kelemahan ChromaDB/SQLite di Windows vs PostgreSQL Enterprise
* **Kondisi Sebelumnya:** Sistem menyimpan vektor dalam ChromaDB lokal berbasis file SQLite.
* **Tantangan di Lingkungan Windows:**  
  * SQLite sering mengalami masalah *file locking* saat diakses secara multi-threading oleh API web atau batch processing di Windows.
  * Pencarian kemiripan vektor di SQLite dilakukan dengan metode *linear scan* $O(N)$ yang lambat ketika tabel data mencapai ribuan.
* **Solusi Perbaikan:**  
  Sistem telah dimigrasikan ke **PostgreSQL Server 10.133.21.24:5433** dengan database `bps_rag3321` dan ekstensi `pgvector (0.8.1)`.
  * Menggunakan indeks **HNSW (*Hierarchical Navigable Small World*)** yang mampu melakukan pencarian kemiripan kosinus dalam hitungan milidetik (*sub-millisecond*).
  * Data terpusat, aman, dapat diakses multi-user tanpa risiko konflik file lock.

---

### 💡 Pelajaran 4: Pemformatan Standar Angka Desimal Indonesia
* **Kondisi Sebelumnya:** Format angka Indonesia menggunakan titik `.` sebagai pemisah ribuan dan koma `,` sebagai desimal (contoh: `1.234.567,89`). Parser sebelumnya terkadang memotong desimal atau salah mendeteksi ribuan sebagai koma.
* **Solusi Perbaikan:**  
  Dibuat regex pembersih cerdas yang mampu mendeteksi format angka Indonesia secara akurat, sekaligus mempertahankan anotasi penting BPS seperti catatan revisi (`123,4r`) dan tanda bintang footnote (`*`).

---

### 💡 Pelajaran 5: Mengapa Vektor Saja Tidak Cukup? (*Hybrid Search RRF*)
* **Kondisi Sebelumnya:** Sistem hanya mengandalkan pencarian kemiripan kosinus vektor (*Dense Vector Search*).
* **Masalah:**  
  Model embedding bahasa (*Sentence Transformers*) sangat pintar memahami sinonim kata, namun sering **kurang presisi** ketika berhadapan dengan kata kunci khusus seperti:
  * Nama kecamatan spesifik: *"Bonang"*, *"Wedung"*, *"Guntur"*.
  * Singkatan statistik resmi: *"IPM"*, *"PDRB"*, *"IHK"*, *"NTP"*.
  * Angka tahun: *"2024"*, *"2023"*.
* **Solusi Perbaikan:**  
  Diimplementasikan **Hybrid Search** menggunakan algoritma **RRF (*Reciprocal Rank Fusion*)**:
  $$\text{RRF Score} = \frac{1}{60 + \text{Rank}_{\text{Vector}}} + \frac{1}{60 + \text{Rank}_{\text{FullTextSearch}}}$$
  Metode ini menggabungkan ketepatan kata kunci eksak dari PostgreSQL Full-Text Search Bahasa Indonesia (`tsvector`) dengan pemahaman makna dari pgvector HNSW.

---

## 🚀 3. Bahan & Topik Diskusi Pengembangan ke Depan

Untuk sesi diskusi lanjutan bersama anak magang, berikut topik-topik inovasi yang sangat menarik dan bernilai tinggi untuk dikembangkan:

### 1. Mesin Hitung Deterministik (*Deterministic Math / Statistical Engine*)
* **Latar Belakang:** Pengguna sering bertanya hal komparatif, misalnya:
  * *"Berapa selisih jumlah penduduk antara Kecamatan Mranggen dan Karangtengah tahun 2024?"*
  * *"Berapa persen pertumbuhan produksi padi di Demak dari tahun 2023 ke 2024?"*
* **Isu:** Large Language Model (LLM) sering mengalami halusinasi saat menghitung angka floating-point matematika secara langsung.
* **Bahan Diskusi:** Bagaimana mendesain modul kalkulator Python `Decimal` atau *Tool Calling / Function Calling* sehingga LLM mengekstrak angka resmi dari database, lalu fungsi Python yang melakukan kalkulasi pasti tanpa risiko salah hitung.

### 2. Pipeline OCR untuk Publikasi Jadul (Buku Statistik Era Pra-2018)
* **Latar Belakang:** Publikasi BPS era lama sebagian berwujud PDF hasil pindaian (*scanned image*), bukan teks digital langsung.
* **Bahan Diskusi:** Mengintegrasikan pustaka OCR seperti Tesseract atau PaddleOCR untuk mengenali struktur grid tabel pada PDF hasil scan.

### 3. Otomasi Crawler & Ingestion Terjadwal (*Scheduled Sync*)
* **Latar Belakang:** BPS secara berkala merilis Berita Resmi Statistik (BRS) dan publikasi baru di portal `demakkab.bps.go.id`.
* **Bahan Diskusi:** Membangun *scheduler* otomatis (cron job / Celery) yang memantau portal BPS setiap minggu, mengunduh rilis baru, lalu langsung memasukkannya ke database PostgreSQL tanpa perlu dijalankan manual.

### 4. Integrasi Multi-Kanal Layanan Publik (WhatsApp / Telegram Bot BPS Demak)
* **Latar Belakang:** Mayoritas masyarakat dan mitra BPS mengakses layanan Pelayanan Statistik Terpadu (PST) melalui WhatsApp.
* **Bahan Diskusi:** Menghubungkan endpoint REST API (`POST /api/chat`) pada `chatbot/api.py` ke WhatsApp Business API (Twilio / Fonnte / Wablas) agar masyarakat dapat bertanya data Demak langsung via pesan WA.

### 5. Continuous Benchmark & Quality Assurance (*Eval Harness*)
* **Latar Belakang:** Telah dibuat dataset uji emas (*Golden Dataset*) berisi 30 pertanyaan riil di `tests/benchmarks/golden_dataset.json`.
* **Bahan Diskusi:** Bagaimana menjalankan benchmark otomatis setiap kali ada perubahan prompt atau konfigurasi model untuk menjaga akurasi jawaban tetap di atas 95%.

---

## 🖥️ 4. Panduan Menjalankan Sistem & Melihat Tampilan Antarmuka (GUI)

Sistem RAG3321 menyediakan 3 pilihan antarmuka sesuai kebutuhan:

### Pilihan 1: Antarmuka Web Visual Interaktif (Streamlit GUI) — *Sangat Direkomendasikan!*
Telah dibuatkan aplikasi web modern berbasis **Streamlit** (`app.py`) dengan tema resmi BPS (Biru & Oranye), panel chat interaktif, filter kecamatan/tahun, status koneksi database, dan daftar sumber sitasi resmi.

**Langkah Menjalankan:**
1. Buka terminal (PowerShell atau Command Prompt) di folder proyek:
   ```bash
   cd D:\Coding\RAG3321
   ```
2. Jalankan perintah Streamlit:
   ```bash
   streamlit run app.py
   ```
   *(Atau menggunakan path Python Laragon:)*
   ```bash
   C:\laragon\bin\python\python-3.10\python.exe -m streamlit run app.py
   ```
3. Browser web akan otomatis terbuka pada alamat:
   ```text
   http://localhost:8501
   ```
4. Anda dapat langsung mengklik tombol pertanyaan cepat (contoh: *Jumlah Penduduk Demak*, *Produksi Padi*, *Capaian IPM*, *Nama Kepala BPS*) atau mengetik pertanyaan bebas di kotak chat.

---

### Pilihan 2: Antarmuka Terminal Interaktif (CLI)
Bagi tim teknis yang ingin mencoba langsung via terminal teks:
```bash
python -m chatbot.cli
```
Ketik pertanyaan di konsol terminal, dan chatbot akan membalas dengan menampilkan jawaban beserta dokumen referensinya. Ketik `exit` atau `quit` untuk keluar.

---

### Pilihan 3: Antarmuka Dokumentasi REST API (FastAPI Swagger UI)
Bagi tim yang ingin menghubungkan sistem ini ke aplikasi web lain, frontend React/Vue, atau bot WhatsApp:
```bash
python -m uvicorn chatbot.api:app --reload --port 8000
```
Buka browser dan akses Swagger UI di:
```text
http://127.0.0.1:8000/docs
```
Anda dapat menguji endpoint `POST /api/chat` secara langsung dengan form interaktif.

---

## 📊 5. Ringkasan Status Uji Verifikasi Sistem

| No | Modul Uji | Status | Keterangan |
|---|---|:---:|---|
| 1 | `test_table_cleaner.py` | **PASSED** | Pelestarian nilai `-` (NIL), desimal Indonesia, proteksi ffill baris total. |
| 2 | `test_json_builder.py` | **PASSED** | Struktur JSON tabular granular anti-token blowout. |
| 3 | `test_postgres_store.py` | **PASSED** | Penyimpanan & kueri kosinus pgvector HNSW pada server PostgreSQL. |
| 4 | `test_hybrid_search.py` | **PASSED** | Reciprocal Rank Fusion menggabungkan FTS Bahasa Indonesia + pgvector. |
| 5 | `test_chatbot_rag.py` | **PASSED** | Routing percakapan vs data, pembentukan prompt, dan ekstraksi sitasi. |
| 6 | `test_golden_benchmark.py` | **PASSED** | Evaluasi 30 kasus uji riil BPS Demak (akurasi retrieval & latensi warm < 2.0s). |
| **Total** | **Seluruh Test Suite (pytest)** | **18 / 18 PASSED (100%)** | Sistem stabil dan siap digunakan. |
