---
name: python-web-builder
description: >-
  Panduan arsitektur dan pengembangan aplikasi web interaktif menggunakan Python (Streamlit, Plotly, FastAPI, Flask).
  Gunakan skill ini untuk merancang, membangun, mengoptimalkan, dan memelihara dashboard interaktif, visualisasi data,
  layout UI modern, manajemen session state, data caching, responsive components, dan arsitektur web Python yang tangguh tanpa lag atau bug rendering.
---

# Python Web Builder Skill

Skill ini memandu AI agent dalam merancang dan membangun aplikasi web interaktif, dashboard data, dan visualisasi finansial berbasis Python dengan performa tinggi, UI/UX modern, dan arsitektur bersih.

---

## 1. Arsitektur Aplikasi Web Python (Streamlit + Plotly)

Aplikasi web berbasis data Python (seperti Streamlit) memiliki siklus eksekusi unik: **setiap interaksi pengguna me-rerun seluruh skrip dari atas ke bawah**. Oleh karena itu, arsitektur harus memisahkan lapisan logika dengan jelas:

```
├── app.py                     # Lapisan UI / Controller (Streamlit widgets & visual rendering)
├── technical_engine.py        # Lapisan Bisnis / Komputasi Murni (tanpa dependensi UI)
├── fetch_idx_fundamentals.py  # Lapisan Data Ingestion / Scraper / API client
└── data/                      # Lapisan Penyimpanan Data Lokal (CSV, SQLite, JSON)
```

### Prinsip Utama:
1. **Separation of Concerns**: Jangan campur kalkulasi matematika/finansial kompleks langsung di dalam blok rendering UI. Taruh di engine modul independen yang bisa dites via CLI.
2. **Deterministic Inputs/Outputs**: Fungsi di engine harus murni (*pure functions*) yang menerima `pandas.DataFrame` atau parameter lalu mengembalikan hasil siap render.

---

## 2. Best Practices Manajemen State & Rerun di Streamlit

### Hindari Unnecessary Reruns dengan `st.form`
Gunakan `st.form` untuk kelompok input konfigurasi agar aplikasi tidak me-rerun setiap kali pengguna mengetik satu karakter atau mengubah satu slider:

```python
with st.sidebar.form(key="screener_filter_form"):
    min_volume = st.number_input("Min Volume", value=1_000_000, step=500_000)
    max_pe = st.slider("Max P/E", 0, 50, 15)
    submitted = st.form_submit_button("🔍 Terapkan Filter")
    if submitted:
        # Jalankan filter hanya setelah tombol ditekan
        apply_filters(min_volume, max_pe)
```

### Session State Hygiene
- Inisialisasi default state di awal aplikasi:
  ```python
  if "selected_ticker" not in st.session_state:
      st.session_state["selected_ticker"] = "BBRI"
  ```
- Hindari overwrite `st.session_state` di tengah siklus render widget yang sudah mengikat key yang sama.

---

## 3. Strategi Caching Data & Performa (`@st.cache_data`)

Panggilan API eksternal (Yahoo Finance, REST API, scraping) dan pemrosesan dataset besar **wajib dicache**:

```python
import streamlit as st
import pandas as pd
import yfinance as yf

# Cache data harga saham selama 15 menit (900 detik)
@st.cache_data(ttl=900, show_spinner=False)
def get_cached_stock_data(ticker: str, period: str = "6mo") -> pd.DataFrame:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        if df.empty:
            return pd.DataFrame()
        return df
    except Exception as e:
        return pd.DataFrame()

# Cache data fundamental statis selama 6 jam (21600 detik)
@st.cache_data(ttl=21600)
def load_fundamental_dataset(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)
```

- **Mutasi Data**: Jangan memodifikasi DataFrame hasil cache langsung secara *in-place*. Selalu gunakan `.copy()` sebelum transformasi lokal.
- Sediakan tombol manual refresh: `st.cache_data.clear()` jika pengguna ingin memaksa penarikan data baru.

---

## 4. Visualisasi Finansial Interaktif dengan Plotly

Saat merancang grafik saham multi-indikator:
1. **Subplots Terkoordinasi**:
   - Subplot 1: Candlestick + MA/EMA + Bollinger Bands.
   - Subplot 2: Volume bar dengan pewarnaan dinamis (Hijau = Bullish day, Merah = Bearish day).
   - Subplot 3: RSI (14) dengan garis referensi 70 & 30.
   - Subplot 4: MACD Line, Signal Line, & Histogram.
2. **Shared X-Axis**: Selalu set `shared_xaxes=True` agar saat zoom/pan di satu subplot, subplot lain ikut bergeser secara sinkron.
3. **Rangebreaks untuk Hari Libur BEI**:
   - Hilangkan jeda akhir pekan (Sabtu & Minggu) agar grafik tidak bolong:
     ```python
     fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
     ```
4. **Theme & Responsiveness**:
   - Gunakan layout `plotly_dark` untuk tampilan profesional kontras tinggi.
   - Set `autosize=True` dan `margin=dict(l=40, r=40, t=40, b=40)` agar pas di berbagai resolusi layar.

---

## 5. Error Boundaries & UX Polishing

1. **Feedback Visual yang Jelas**:
   - Gunakan `st.spinner("Mengambil data live dari bursa...")` saat operasi asynchronous berjalan.
   - Berikan `st.toast("Data berhasil diperbarui!", icon="✅")` untuk aksi sukses cepat.
2. **Graceful Degradation**:
   - Jika ticker tidak ditemukan atau Yahoo Finance limit, tampilkan pesan ramah via `st.warning()` atau `st.error()` beserta saran tindakan perbaikan, bukan traceback error merah mentah Python.
3. **Responsive Multi-Column Layout**:
   - Manfaatkan `st.columns([1, 2, 1])` untuk menyusun metrik ringkasan (KPI cards) di bagian atas dashboard.
   - Gunakan `st.metric(label="Harga Terakhir", value=f"Rp {price:,}", delta=f"{change:+0.2f}%")`.
