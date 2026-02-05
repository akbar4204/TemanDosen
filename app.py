import streamlit as st
from scholarly import scholarly
import google.generativeai as genai

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="TemanDosen Pro", page_icon="🎓", layout="wide")

# Header
st.markdown("## 🎓 TemanDosen: Asisten Karier Akademik")
st.markdown("---")

# --- FUNGSI PEMBERSIH ID ---
def bersihkan_id(input_text):
    # Membersihkan link panjang menjadi ID saja
    if "user=" in input_text:
        try:
            return input_text.split("user=")[1].split("&")[0]
        except:
            return input_text
    if "&" in input_text:
        return input_text.split("&")[0]
    return input_text

# --- KOLOM INPUT LENGKAP ---
col_kiri, col_kanan = st.columns(2)

with col_kiri:
    st.subheader("1. Identitas Digital")
    raw_id = st.text_input("Paste Link / ID Google Scholar", placeholder="Contoh: 3lUcciYAAAAJ")
    scholar_id = bersihkan_id(raw_id)
    
    if raw_id and raw_id != scholar_id:
        st.success(f"✅ ID Terdeteksi: {scholar_id}")
    
    rumpun = st.text_input("Rumpun Ilmu / Prodi", placeholder="Contoh: Pariwisata Halal")

with col_kanan:
    st.subheader("2. Status Kepegawaian")
    # INI YANG ANDA MINTA (JABATAN & PENDIDIKAN)
    jabatan = st.selectbox("Jabatan Fungsional Saat Ini", 
                           ["Tenaga Pengajar", "Asisten Ahli", "Lektor", "Lektor Kepala", "Guru Besar"])
    
    pendidikan = st.selectbox("Pendidikan Terakhir", 
                              ["S2 (Magister)", "S3 (Doktor)"])

st.markdown("---")
tombol = st.button("🚀 Analisa Karier & Roadmap", type="primary", use_container_width=True)

# --- LOGIKA UTAMA ---
if tombol:
    if not scholar_id:
        st.warning("⚠️ Mohon isi ID Google Scholar dulu.")
        st.stop()
        
    # Container Output
    container = st.container(border=True)
    status = container.status("🔍 Sedang memproses data...", expanded=True)
    
    try:
        # 1. AMBIL DATA SCHOLAR
        status.write("📂 Mengakses database Google Scholar...")
        
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author) # Tarik data lengkap
        
        # Ekstrak Data
        nama = author.get('name')
        afiliasi = author.get('affiliation')
        h_index = author.get('hindex')
        total_sitasi = author.get('citedby')
        
        # Ambil 5 judul publikasi terbaru
        publikasi_list = [pub['bib']['title'] for pub in author.get('publications')[:5]]
        
        status.write(f"✅ Data Ditemukan: {nama} | H-Index: {h_index}")
        
        # 2. ANALISIS AI
        status.write("🤖 Mengirim data ke AI Consultant...")
        
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("API Key belum disetting!")
            st.stop()
            
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # KITA GUNAKAN MODEL TERBARU (Pastikan requirements.txt sudah diupdate)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Bertindaklah sebagai Asesor PAK (Penilaian Angka Kredit) Indonesia.
        
        DATA DOSEN:
        - Nama: {nama}
        - Jabatan Saat Ini: {jabatan}
        - Pendidikan Terakhir: {pendidikan}
        - Rumpun Ilmu: {rumpun}
        - H-Index Scholar: {h_index}
        - Total Sitasi: {total_sitasi}
        - 5 Publikasi Terakhir: {publikasi_list}
        
        TUGAS ANDA:
        1. **Analisis Posisi**: Apakah dengan H-Index {h_index} dan jabatan {jabatan}, dosen ini sudah layak naik ke jenjang berikutnya? Apa kekurangannya?
        2. **Rekomendasi Riset**: Berikan 3 ide judul penelitian tentang '{rumpun}' yang berpeluang besar disitasi tinggi tahun 2025.
        3. **Roadmap Karier**: Buatlah checklist target konkret untuk 1 tahun ke depan agar bisa naik jabatan / lulus serdos.
        
        Gunakan gaya bahasa profesional, memotivasi, dan format poin-poin yang rapi.
        """
        
        response = model.generate_content(prompt)
        
        status.update(label="Selesai!", state="complete", expanded=False)
        
        # TAMPILKAN HASIL
        st.success(f"Analisis untuk **{nama}** ({jabatan})")
        st.markdown(response.text)

    except Exception as e:
        status.update(label="Terjadi Kesalahan", state="error")
        st.error(f"Error Detail: {e}")
        st.info("Tips: Jika error '404 model not found', pastikan Anda sudah melakukan 'Reboot App' setelah update requirements.txt.")
