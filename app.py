import streamlit as st
from scholarly import scholarly
import google.generativeai as genai

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="TemanDosen Pro", page_icon="🎓", layout="wide")

st.markdown("## 🎓 TemanDosen: Asisten Karier Akademik")
st.caption("System Check: ✅ Scholar ID Support | ✅ Auto-Model Switching")
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

# --- FUNGSI PENCARI MODEL OTOMATIS (SOLUSI ERROR 404) ---
def get_working_model():
    # Daftar prioritas model yang ingin dicoba
    priority_models = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-pro'
    ]
    
    # Cek model apa yang tersedia di akun ini
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except:
        pass # Lanjut saja kalau gagal list

    # Cari kecocokan
    for target in priority_models:
        # Cek format 'models/nama' atau 'nama' saja
        if any(target in m for m in available_models):
            return target
            
    # Jika tidak ada yang cocok, kembalikan default aman
    return 'gemini-pro'

# --- KOLOM INPUT LENGKAP ---
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
        try:
            author = scholarly.search_author_id(scholar_id)
            author = scholarly.fill(author)
        except Exception as e:
            st.error(f"Gagal mengambil data Scholar. Pastikan ID benar. Error: {e}")
            st.stop()
        
        nama = author.get('name')
        afiliasi = author.get('affiliation')
        h_index = author.get('hindex')
        total_sitasi = author.get('citedby')
        # Ambil publikasi (handle jika kosong)
        pubs_raw = author.get('publications', [])
        publikasi_list = [pub['bib']['title'] for pub in pubs_raw[:5]] if pubs_raw else ["Belum ada publikasi terdeteksi"]
        
        status.write(f"✅ Data Ditemukan: {nama} | H-Index: {h_index}")
        
        # 3. ANALISIS AI (DENGAN AUTO-SWITCH)
        status.write("🤖 Mencari model AI terbaik...")
        
        # Cari model yang valid
        model_name = get_working_model()
        status.write(f"⚙️ Menggunakan Model: {model_name}")
        
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        Bertindaklah sebagai Asesor PAK (Penilaian Angka Kredit) Indonesia & Konsultan Karier.
        
        DATA DOSEN:
        - Nama: {nama}
        - Jabatan: {jabatan}
        - Pendidikan: {pendidikan}
        - Rumpun Ilmu: {rumpun}
        - H-Index: {h_index}
        - Total Sitasi: {total_sitasi}
        - 5 Publikasi Terakhir: {publikasi_list}
        
        TUGAS:
        1. **Analisis Gap**: Apa kekurangan utama profil ini untuk naik ke jenjang selanjutnya (atau untuk Guru Besar jika sudah LK)?
        2. **Ide Riset Viral 2025**: Berikan 3 judul paper spesifik untuk bidang '{rumpun}' yang berpotensi Q1/High Impact.
        3. **Strategi Percepatan**: Roadmap konkret 12 bulan ke depan.
        
        Gunakan bahasa Indonesia profesional, format Markdown rapi.
        """
        
        response = model.generate_content(prompt)
        
        status.update(label="Selesai!", state="complete", expanded=False)
        
        # TAMPILKAN HASIL
        st.success(f"Analisis Selesai untuk **{nama}**")
        st.markdown(response.text)

    except Exception as e:
        status.update(label="Error", state="error")
        st.error(f"Terjadi kesalahan sistem: {e}")
        st.markdown("---")
        st.warning("""
        **Solusi:**
        1. Coba refresh halaman.
        2. Jika masih error, kemungkinan API Key bermasalah atau kuota habis.
        3. Coba lakukan 'Reboot App' di menu kanan atas.
        """)
