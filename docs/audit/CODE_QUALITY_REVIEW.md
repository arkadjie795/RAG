# Phase 12 — Code Quality, Architecture & Maintainability Review

## 1. Executive Summary

Dokumen ini memuat ulasan mendalam mengenai kualitas kode sumber (*code quality*), kepatuhan terhadap prinsip rekayasa perangkat lunak (SOLID, Clean Architecture, DRY), utang teknis (*technical debt*), kode mati (*dead code*), serta peringatan pustaka pihak ketiga.

---

## 2. Kepatuhan terhadap Prinsip Rekayasa Perangkat Lunak

### A. Single Responsibility Principle (SRP)
- **Modul Ekstraksi (`modules/extraction/`)**:
  - `extractor.py`: Khusus membaca PDF dan memotong area tabel.
  - `cleaner.py`: Khusus membersihkan whitespace, simbol BPS, dan format numerik.
  - `synthesizer.py`: Khusus mengonversi baris tabel menjadi kalimat deskriptif.
  - **Penilaian**: **Sangat Baik**. Pembagian tanggung jawab jelas dan terisolasi.
- **Modul Chatbot (`chatbot/bot.py`)**:
  - Tanggung jawab agak bercampur antara manajemen history percakapan, pembuatan prompt sistem, pemilihan model LLM fallback, dan parsing respons sitasi.
  - **Penilaian**: **Cukup**. Disarankan untuk memisahkan logika routing prompt ke modul tersendiri.

### B. Dependency Inversion Principle (DIP)
- Komponen backend FastAPI (`api/routers/`) menggunakan dependency injection FastAPI (`Depends`), mempermudah mocking koneksi database pada pengujian.
- Komponen storage (`BPSVectorStore`) berinteraksi langsung dengan driver `psycopg2` via SQL mentah. Meskipun cepat dan efisien, pembungkus antarmuka repository abstrak (*Repository Pattern*) akan membuat kode lebih mudah diganti jenis penyimpanannya jika di masa depan diperlukan.

---

## 3. Identifikasi Kode Mati & Artefak Usang (Dead Code & Legacy Files)

Berdasarkan penelusuran struktur file, ditemukan beberapa file yang sudah tidak terpakai atau bersifat redundan:

| Path File / Folder | Kategori | Alasan Identifikasi | Rekomendasi |
| :--- | :--- | :--- | :--- |
| `app.py` | Legacy UI | File antarmuka Streamlit lama. Sistem utama telah dimigrasikan ke Vue 3 + FastAPI. | Simpan di folder `legacy/` atau dokumentasikan sebagai portal GUI alternatif. |
| `database/chroma_store/` | Dead Storage (3 GB) | Direktori penyimpanan ChromaDB lokal versi lama sebelum migrasi total ke PostgreSQL HNSW. | Dapat diarsipkan atau dihapus dari lingkungan produksi untuk menghemat 3 GB ruang disk. |
| `test_*.py` di root directory (`test_bot.py`, `test_embedder.py`, dll.) | Ad-hoc Scripts | Script pengujian manual sementara sebelum suite resmi dibuat di folder `tests/`. | Pindahkan ke `scripts/experimental/` agar root repositori tetap bersih. |
| `verify_setup.py`, `demo_rag.py` | Ad-hoc Helper | Script demo awal pembuatan proyek. | Dokumentasikan fungsinya di panduan pengembang. |

---

## 4. Analisis Peringatan Pustaka (Deprecation Warnings)

Pada saat eksekusi test suite dan startup FastAPI, tercatat beberapa peringatan:

1. **Pydantic V2 Deprecation Warning**:
   ```text
   PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead.
   ```
   - **Lokasi**: Pada beberapa pemanggilan skema respons API (`api/schemas/`).
   - **Dampak**: Tidak merusak eksekusi saat ini, namun berisiko menimbulkan galat jika Pydantic diupgrade ke versi 3.x.
2. **PyTorch Tensor Warning**:
   ```text
   FutureWarning: `encoder_hidden_states` is deprecated and will be removed in future versions.
   ```
   - **Lokasi**: Di dalam internal library `sentence-transformers` saat memuat model MiniLM.
   - **Dampak**: Peringatan dari pustaka internal, aman untuk diabaikan.

---

## 5. Ringkasan Skor Kualitas Kode

| Aspek Kode | Skor (1–10) | Catatan |
| :--- | :---: | :--- |
| **Keterbacaan & Gaya Penulisan (PEP 8)** | 8.5 | Penamaan fungsi, kelas, dan variabel sangat deskriptif dan konsisten. |
| **Separation of Concerns** | 8.0 | Pembagian modul extraction, storage, crawler, dan API terstruktur rapi. |
| **Modularitas & Ekstensibilitas** | 7.5 | Mudah ditambahkan fitur baru, namun butuh abstraksi antarmuka storage. |
| **Kebersihan Repositori (Hygiene)** | 6.5 | Masih terdapat file script ad-hoc di direktori root dan folder Chroma lama. |
| **Dokumentasi Kode (Docstrings & Typing)** | 8.0 | Mayoritas fungsi inti dilengkapi Type Hinting dan docstring penjelasan. |

**Skor Kualitas Kode Keseluruhan: 7.7 / 10**
