"""
Sahabat Data BPS Kabupaten Demak (RAG3321) - Web GUI
Aplikasi Chatbot Cerdas Berbasis RAG & Hybrid Search (PostgreSQL + pgvector).
"""
import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from chatbot.bot import BPSChatbot
from modules.retrieval.entity_dictionary import DEMAK_KECAMATAN

# Page Configuration
st.set_page_config(
    page_title="Sahabat Data BPS Demak (3321)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (BPS Brand Colors: Deep Navy #002B49 & Vibrant Orange #F26522)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #002B49 0%, #004B87 100%);
        padding: 18px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
    }
    .main-header p {
        margin: 4px 0 0 0;
        font-size: 0.9rem;
        color: #E0E7FF;
    }
    .badge-bps {
        background-color: #F26522;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .citation-card {
        background-color: #F8FAFC;
        border-left: 4px solid #004B87;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 0.88rem;
    }
    .stChatMessage {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Menyiapkan mesin Sahabat Data BPS...")
def load_chatbot():
    """Initializes and caches the BPSChatbot instance."""
    bot = BPSChatbot()
    return bot


try:
    bot = load_chatbot()
except Exception as e:
    st.error(f"Gagal menginisialisasi Chatbot: {e}")
    st.stop()

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit_session"

# Sidebar Configuration
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/28/Lambang_Badan_Pusat_Statistik_%28BPS%29_Indonesia.svg", width=64)
    st.title("Pengaturan RAG")
    st.markdown("Konfigurasi pencarian data statistik terpadu.")

    st.subheader("Filter Konteks (Opsional)")
    kecamatan_options = ["Semua / Otomatis"] + sorted([k.title() for k in DEMAK_KECAMATAN])
    selected_kec = st.selectbox("Wilayah / Kecamatan:", kecamatan_options, index=0)
    filter_daerah = None if selected_kec == "Semua / Otomatis" else selected_kec

    year_options = ["Semua / Otomatis", "2025", "2024", "2023", "2022", "2021", "2020"]
    selected_year = st.selectbox("Tahun Rujukan:", year_options, index=0)
    filter_tahun = None if selected_year == "Semua / Otomatis" else selected_year

    top_k = st.slider("Jumlah Chunks (Top-K):", min_value=2, max_value=8, value=4, step=1)

    st.markdown("---")
    st.subheader("Status Arsitektur")
    st.success("Database: PostgreSQL 16 + pgvector\n\nHost: 10.133.21.24:5433\n\nDB: bps_rag3321")

    if st.button("🗑️ Bersihkan Riwayat Chat", use_container_width=True):
        bot.clear_memory(st.session_state.session_id)
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.caption("BPS Kabupaten Demak © 2026 | Sahabat Data 3321")

# Main Header
st.markdown("""
<div class="main-header">
    <div>
        <h1>Sahabat Data BPS Kabupaten Demak</h1>
        <p>Asisten AI Resmi Berbasis Publikasi Statistik Terpadu (Kode Wilayah 3321)</p>
    </div>
    <div>
        <span class="badge-bps">RAG3321 v2.0 Enterprise</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Starter Suggestions when conversation is empty
if len(st.session_state.messages) == 0:
    st.info("👋 **Selamat datang di Sahabat Data BPS Kabupaten Demak!** Silakan ajukan pertanyaan seputar data statistik atau pilih contoh di bawah ini:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👥 Berapa jumlah penduduk Kabupaten Demak 2024?", use_container_width=True):
            st.session_state.user_prompt_input = "Berapa jumlah penduduk Kabupaten Demak tahun 2024?"
        if st.button("🌾 Berapa produksi padi sawah di Dempet?", use_container_width=True):
            st.session_state.user_prompt_input = "Berapa produksi padi sawah di Kecamatan Dempet?"
    with col2:
        if st.button("📈 Bagaimana capaian IPM Demak tahun 2024?", use_container_width=True):
            st.session_state.user_prompt_input = "Bagaimana capaian Indeks Pembangunan Manusia (IPM) Demak tahun 2024?"
        if st.button("👔 Siapa Kepala BPS Kabupaten Demak saat ini?", use_container_width=True):
            st.session_state.user_prompt_input = "Siapa nama Kepala BPS Kabupaten Demak saat ini?"

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander(f"📚 {len(msg['citations'])} Sumber & Referensi Resmi BPS"):
                for idx, cit in enumerate(msg["citations"], 1):
                    doc_title = cit.get("dokumen_sumber") or cit.get("dokumen") or "Publikasi BPS"
                    hal = cit.get("halaman", "-")
                    thn = cit.get("tahun", "-")
                    tbl = cit.get("judul_tabel", "-")
                    st.markdown(
                        f"**{idx}. {doc_title} ({thn})**  \n"
                        f"- *Halaman:* {hal}  \n"
                        f"- *Tabel/Bagian:* {tbl}"
                    )

# Input Box
prompt = st.chat_input("Ketik pertanyaan Anda tentang data BPS Demak di sini...")

# Check if a suggestion button was clicked
if "user_prompt_input" in st.session_state and st.session_state.user_prompt_input:
    prompt = st.session_state.user_prompt_input
    del st.session_state.user_prompt_input

if prompt:
    # Append User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Mencari data resmi di database BPS Demak..."):
            try:
                response = bot.ask(
                    question=prompt,
                    session_id=st.session_state.session_id,
                    daerah=filter_daerah,
                    tahun=filter_tahun,
                    top_k=top_k
                )
                answer = response.get("answer", "Maaf, tidak dapat menghasilkan jawaban.")
                citations = response.get("citations", [])
            except Exception as ex:
                answer = f"Terjadi kesalahan saat memproses data: {ex}"
                citations = []

            st.markdown(answer)

            if citations:
                with st.expander(f"📚 {len(citations)} Sumber & Referensi Resmi BPS"):
                    for idx, cit in enumerate(citations, 1):
                        doc_title = cit.get("dokumen_sumber") or cit.get("dokumen") or "Publikasi BPS"
                        hal = cit.get("halaman", "-")
                        thn = cit.get("tahun", "-")
                        tbl = cit.get("judul_tabel", "-")
                        st.markdown(
                            f"**{idx}. {doc_title} ({thn})**  \n"
                            f"- *Halaman:* {hal}  \n"
                            f"- *Tabel/Bagian:* {tbl}"
                        )

            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "citations": citations
            })
