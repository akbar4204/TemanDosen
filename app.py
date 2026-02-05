import streamlit as st
import google.generativeai as genai
from scholarly import scholarly

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="TemanDosen Pro", page_icon="🎓", layout="wide")

# --- JUDUL & DEBUGGER VERSI (PENTING) ---
st.markdown("## 🎓 TemanDosen: Asisten Karier Akademik")
# Baris ini akan memberitahu kita versi berapa yang dipakai server
st.caption(f"System Info: Library AI Version **{genai.__version__}** (Target: >= 0.8.3)") 
st.markdown("---")

# --- FUNGSI PEMBERSIH ID ---
def bersihkan_id(input_text):
    if "user=" in input_text:
        try:
            return input_text.split("user=")[1].split("&")[0]
        except:
            return input_text
    if "&" in input_text:
        return input_text.split("&")[0]
    return input_text

# --- KOLOM INPUT ---
col_kiri, col_kanan = st.columns(2)

with col_kiri:
    st.subheader("1. Identitas Digital")
    raw_id = st.text_input("Paste Link / ID Google Scholar", placeholder="Contoh: 3lUcciYAAAAJ")
    scholar_id = bersihkan_id(raw_id)
    
    if raw_id and raw_id != scholar_id:
        st.info(f"✅ ID Bersih: {scholar_id}")
    
    rumpun = st.text_input("Rumpun Ilmu / Prodi", placeholder="Contoh: Pariwisata Halal")

with col_kanan:
    st.subheader("2. Status Kepegawaian")
    jabatan = st.selectbox("Jabatan Fungsional", 
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
        
    container = st.container(border=True)
    status = container.status("🔍 Sedang memproses...", expanded=True)
    
    try:
        # 1. SETUP API KEY
        if "GEMINI_API_KEY" not in st.secrets:
            st.error("API Key belum disetting!")
            st.stop()
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

        # 2. AMBIL DATA SCHOLAR
        status.write("📂 Mengakses Google Scholar...")
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author)
        
        nama = author.get('name')
        h_index = author.get('hindex')
        total_sitasi = author.get('citedby')
        pubs_raw = author.get('publications', [])
        publikasi_list = [pub['bib']['title'] for pub in pubs_raw[:5]] if pubs_raw else ["Belum ada publikasi"]
        
        status.write(f"✅ Data Ditemukan: {nama} | H-Index: {h_index}")
        
        # 3. ANALISIS AI
        status.write("🤖 Mengirim ke Gemini 1.5 Flash...")
        
        # Model Configuration
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Bertindaklah sebagai Asesor PAK (Penilaian Angka Kredit) Indonesia.
        
        DATA DOSEN:
        - Nama: {nama}
        - Jabatan: {jabatan}
        - Pendidikan: {pendidikan}
        - Rumpun Ilmu: {rumpun}
        - H-Index: {h_index}
        - Total Sitasi: {total_sitasi}
        - 5 Publikasi Terakhir: {publikasi_list}
        
        BERIKAN:
        1. Analisis Gap untuk kenaikan jabatan.
        2. 3 Ide Riset '{rumpun}' yang Viral/High Impact 2025.
        3. Roadmap karier 1 tahun ke depan.
        """
        
        response = model.generate_content(prompt)
        
        status.update(label="Selesai!", state="complete", expanded=False)
        st.success(f"Analisis Selesai untuk **{nama}**")
        st.markdown(response.text)

    except Exception as e:
        status.update(label="Error", state="error")
        st.error(f"Terjadi kesalahan: {e}")
        
        # PESAN DIAGNOSA KHUSUS
        if "404" in str(e):
             st.warning(f"""
             **DIAGNOSA:** Versi Library Anda saat ini: `{genai.__version__}`.
             Untuk menggunakan Gemini Flash, versi MINIMAL harus `0.7.0` atau `0.8.3`.
             
             **SOLUSI:**
             1. Pastikan `requirements.txt` sudah diupdate.
             2. Lakukan 'Reboot App' untuk memaksa update.
             """)
