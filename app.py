import streamlit as st
import google.generativeai as genai
from scholarly import scholarly

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="TemanDosen Pro", page_icon="🎓", layout="wide")

st.markdown("## 🎓 TemanDosen: Asisten Karier Akademik")
st.markdown("---")

# --- 1. SETUP API KEY & DETEKSI MODEL (RADAR) ---
# Kita cek dulu model apa yang DIIZINKAN untuk API Key ini
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # Minta daftar model yang tersedia
        model_list = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Bersihkan nama (misal: models/gemini-pro -> gemini-pro)
                clean_name = m.name.replace("models/", "")
                model_list.append(clean_name)
        
        # Urutkan agar Flash/Pro ada di atas
        model_list.sort(reverse=True) 
        
    except Exception as e:
        st.error(f"❌ API Key Bermasalah: {e}")
        model_list = []
else:
    st.error("⚠️ API Key belum disetting di Secrets!")
    model_list = []

# --- 2. KOLOM INPUT ---
col_kiri, col_kanan = st.columns(2)

with col_kiri:
    st.subheader("1. Identitas & Model")
    
    # --- PILIHAN MODEL (ANTI ERROR 404) ---
    if model_list:
        pilihan_model = st.selectbox(
            "✅ Model Tersedia (Pilih Satu):", 
            model_list,
            index=0
        )
        st.caption(f"ℹ️ Menggunakan model: `{pilihan_model}`")
    else:
        st.warning("⚠️ Tidak ada model yang ditemukan. Cek API Key Anda.")
        pilihan_model = None

    raw_id = st.text_input("Paste Link / ID Google Scholar", placeholder="Contoh: 3lUcciYAAAAJ")
    
    # Pembersih ID
    scholar_id = raw_id
    if "user=" in raw_id:
        try: scholar_id = raw_id.split("user=")[1].split("&")[0]
        except: pass
        
    rumpun = st.text_input("Rumpun Ilmu / Prodi", placeholder="Contoh: Pariwisata Halal")

with col_kanan:
    st.subheader("2. Status Kepegawaian")
    jabatan = st.selectbox("Jabatan Fungsional", ["Tenaga Pengajar", "Asisten Ahli", "Lektor", "Lektor Kepala", "Guru Besar"])
    pendidikan = st.selectbox("Pendidikan Terakhir", ["S2 (Magister)", "S3 (Doktor)"])

st.markdown("---")
tombol = st.button("🚀 Analisa Karier & Roadmap", type="primary", use_container_width=True)

# --- 3. LOGIKA UTAMA ---
if tombol:
    if not scholar_id or not pilihan_model:
        st.warning("⚠️ Pastikan ID Scholar diisi dan Model tersedia.")
        st.stop()
        
    status = st.status("🔍 Memproses...", expanded=True)
    
    try:
        # A. AMBIL DATA SCHOLAR
        status.write("📂 Mengambil data Scholar...")
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author)
        
        nama = author.get('name')
        h_index = author.get('hindex')
        pubs = [p['bib']['title'] for p in author.get('publications', [])[:5]]
        
        status.write(f"✅ Data: {nama} | H-Index: {h_index}")
        
        # B. ANALISIS AI (SESUAI PILIHAN)
        status.write(f"🤖 Mengirim ke AI ({pilihan_model})...")
        
        model = genai.GenerativeModel(pilihan_model) # Gunakan model yang dipilih user
        
        prompt = f"""
        Role: Asesor PAK Dosen Indonesia.
        Data: {nama}, {jabatan}, {pendidikan}, {rumpun}, H-Index {h_index}.
        Publikasi Terakhir: {pubs}
        
        Buat:
        1. Analisis Gap Karier.
        2. 3 Ide Riset Viral 2025.
        3. Roadmap 1 Tahun.
        """
        
        response = model.generate_content(prompt)
        
        status.update(label="Selesai!", state="complete", expanded=False)
        st.subheader(f"Hasil Analisis: {nama}")
        st.markdown(response.text)

    except Exception as e:
        status.update(label="Gagal", state="error")
        st.error(f"Terjadi kesalahan: {e}")
        st.info("💡 Tips: Coba ganti pilihan model di dropdown (misal ke gemini-1.5-flash-001 atau gemini-pro).")
