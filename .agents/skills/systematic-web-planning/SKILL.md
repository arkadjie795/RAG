---
name: systematic-web-planning
description: >-
  Framework perencanaan sistematis (planning, specification, dan task breakdown) sebelum mengeksekusi fitur web,
  dashboard, atau modul backend Python. Gunakan skill ini sebelum menulis atau memodifikasi kode untuk menyusun roadmap,
  breakdown task berurutan, skema data flow, mitigasi resiko, validasi fraksi/aturan bisnis, dan rencana verifikasi sebelum dianggap selesai.
---

# Systematic Web Planning & Execution Framework

Skill ini memandu AI agent dalam merancang dan merencanakan pengembangan fitur secara terstruktur, sistematis, dan terukur sebelum menyentuh atau mengubah kode sumber. Menghindari pengembangan impulsif tanpa rencana ("ngawur"), mencegah regresi bug, dan memastikan kepatuhan terhadap aturan bisnis/domain.

---

## 1. Siklus Hidup Perencanaan Fitur (Feature Lifecycle)

Sebelum menulis baris kode pertama pada aplikasi web atau modul komputasi, agent **wajib** melalui 4 tahapan berurutan:

```
[Tahap 1: Analisis Kebutuhan & Aturan Domain]
                   │
                   ▼
[Tahap 2: Spesifikasi Teknis & Alur Data (Data Flow)]
                   │
                   ▼
[Tahap 3: Breakdown Tugas Bertahap (Atomic Checklist)]
                   │
                   ▼
[Tahap 4: Strategi Verifikasi & Standar Selesai (DoD)]
```

---

## 2. Rincian Setiap Tahapan Perencanaan

### Tahap 1: Analisis Kebutuhan & Aturan Domain
Identifikasi secara eksplisit:
1. **Objektif Utama**: Masalah spesifik apa yang diselesaikan fitur ini untuk pengguna?
2. **Aturan Bisnis & Domain**:
   - Contoh pasar saham BEI: Fraksi harga (tick size), batas ARA/ARB, format kode ticker (`.JK`), jam perdagangan, volume lot (1 lot = 100 lembar).
   - Aturan database / data safety: **DILARANG KERAS** melakukan `DROP`, `TRUNCATE`, atau menghapus data persisten tanpa izin eksplisit.
3. **Batasan Teknis**: Apakah fitur ini membutuhkan penarikan data baru dari API eksternal? Apakah ada limitasi kuota/rate-limit?

### Tahap 2: Spesifikasi Teknis & Alur Data (Data Flow)
Petakan rute perpindahan data:
1. **Input Data**: Dari mana data berasal? (yfinance, file CSV di `data/`, input formulir pengguna).
2. **Modul Pengolahan (Pure Engine)**: Fungsi atau modul mana yang bertanggung jawab melakukan komputasi?
   - Logika kalkulasi harus berada di modul mandiri (misal: `technical_engine.py` atau `fundamental_analyzer.py`), BUKAN di dalam blok event UI Streamlit.
3. **State & Caching**:
   - Apakah hasil kalkulasi perlu disimpan di `st.session_state`?
   - Apakah pemanggilan fungsi perlu diberi dekorator `@st.cache_data` dengan TTL tertentu?
4. **Output UI**: Bagaimana data disajikan? (Tabel metrik, chart interaktif Plotly, card alert status, file download).

### Tahap 3: Breakdown Tugas Bertahap (Atomic Checklist)
Bagi pekerjaan menjadi unit-unit kecil yang independen dan dapat diverifikasi:
- [ ] **Langkah 1**: Buat/modifikasi fungsi logika di engine (misal: kalkulasi indikator baru atau filter screener).
- [ ] **Langkah 2**: Buat skrip uji mandiri (CLI test / unit test) untuk memastikan formula matematika benar dan tidak error.
- [ ] **Langkah 3**: Integrasikan fungsi engine ke antarmuka web UI (`app.py`), buat widget input (`st.form`), dan hubungkan ke state.
- [ ] **Langkah 4**: Tambahkan komponen visualisasi (Plotly chart, badge status, warning boundary jika data kosong).
- [ ] **Langkah 5**: Uji coba interaktivitas dan verifikasi performa (memastikan tidak terjadi lag berulang).

### Tahap 4: Strategi Verifikasi & Definition of Done (DoD)
Fitur **HANYA** boleh dinyatakan selesai jika memenuhi seluruh kriteria berikut:
1. **Verifikasi Sintaks & Eksekusi**:
   - Jalankan `python -m py_compile <file.py>` untuk memastikan tidak ada kesalahan sintaks.
   - Jalankan skrip engine via terminal untuk memastikan kalkulasi mengembalikan data yang valid tanpa exception.
2. **Uji UI & Rendering**:
   - Pastikan widget tidak memicu error crash di browser saat input kosong atau tidak valid (graceful fallback).
3. **Aturan Selesai Fitur (Workflow Otomatis)**:
   - Lakukan `git add .`, `git commit -m "pesan commit jelas"`, dan `git push`.
   - Update file `README.md` pada bagian Changelog dengan tanggal hari ini dan daftar fitur/perbaikan yang selesai.
