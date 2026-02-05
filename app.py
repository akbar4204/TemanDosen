import streamlit as st
from scholarly import scholarly
import google.generativeai as genai

# --- SETUP HALAMAN ---
st.set_page_config(page_title="TemanDosen Simple", page_icon="🎓")

st.title("🎓 TemanDosen: Analisis Karier")
st.write("Versi: Lite & Stabil (Tanpa Proxy)")

# --- FUNGSI PEMBERSIH ID (BARU!) ---
def bersihkan_id(input_text):
    # Jika user memasukkan URL lengkap, ambil ID-nya saja
    if "user=" in input_text:
        try:
            # Ambil teks setelah 'user=' dan sebelum tanda '&'
            return input_text.split("user=")[1].split("&")[0]
        except:
            return input_text
    # Jika user memasukkan ID + buntut (misal: ID&hl=en)
    if "&" in input_text:
        return input_text.split("&")[0]
    # Jika bersih
    return input_text

# --- INPUT DATA ---
col1, col2 = st.columns(2)
with col1:
    raw_id = st.text_input("Paste Link/ID Google Scholar", placeholder="Contoh: 3lUcciYAAAAJ")
    # Langsung bersihkan ID saat user mengetik
    scholar_id = bersihkan_id(raw_id)
    if raw_id != scholar_id:
        st.caption(f"✅ ID Terdeteksi: {scholar_id}")

with col2:
    rumpun = st.text_input("Rumpun Ilmu", placeholder="Contoh: Manajemen")

tombol = st.button("🚀 Analisa Sekarang")

# --- LOGIKA UTAMA ---
if tombol:
    if not scholar_id:
        st.error("Mohon isi ID Google Scholar.")
        st.stop()
        
    status = st.status("Sedang bekerja...", expanded=True)
    
    try:
        # 1. TARIK DATA SCHOLAR (Tanpa Proxy)
        status.write("🔍 Mencari data dosen...")
        
        # Cari author langsung by ID
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author) # Tarik detail lengkap
        
        nama = author.get('name')
        afiliasi = author.get('affiliation')
        h_index = author.get('hindex')
        
        status.write(f"✅ Ketemu: {nama} | H-Index: {h_index}")
        
        # 2. PROSES AI (Pakai Model Paling Aman: Gemini Pro)
        status.write("🤖 Mengirim data ke AI...")
        
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("API Key belum disetting!")
            st.stop()
            
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-pro') # KITA PAKAI PRO AGAR STABIL
        
        # Ambil 5 judul publikasi teratas
        pubs = [pub['bib']['title'] for pub in author.get('publications')[:5]]
        
        prompt = f"""
        Analisis profil dosen ini untuk kenaikan jabatan.
        Nama: {nama}
        Afiliasi: {afiliasi}
        Rumpun Ilmu: {rumpun}
        H-Index: {h_index}
        Total Sitasi: {author.get('citedby')}
        5 Publikasi Teratas: {pubs}
        
        Berikan:
        1. Analisis Singkat Kekuatan Profil.
        2. Rekomendasi Topik Riset Viral tahun depan sesuai rumpun ilmu.
        3. Strategi untuk menaikkan H-Index dalam 6 bulan.
        """
        
        response = model.generate_content(prompt)
        
        status.update(label="Selesai!", state="complete", expanded=False)
        
        # TAMPILKAN HASIL
        st.divider()
        st.subheader(f"Hasil Analisis: {nama}")
        st.markdown(response.text)

    except Exception as e:
        status.update(label="Gagal", state="error")
        st.error(f"Terjadi kesalahan: {e}")
        st.warning("Jika error berlanjut, kemungkinan Google Scholar membatasi akses (Rate Limit). Tunggu 1-2 jam dan coba lagi.")
