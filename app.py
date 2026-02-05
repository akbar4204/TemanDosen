import streamlit as st
from scholarly import scholarly, ProxyGenerator
import google.generativeai as genai
import datetime
import time

# --- SETUP HALAMAN ---
st.set_page_config(page_title="TemanDosen - Analisis Karier", page_icon="🎓", layout="wide")

# CSS Agar Tampilan Rapi
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0;}
    .sub-header {font-size: 1.1rem; color: #64748B; margin-bottom: 2rem;}
    .card {background-color: #F8FAFC; padding: 1.5rem; border-radius: 10px; border: 1px solid #E2E8F0; margin-bottom: 1rem;}
    .success-box {background-color: #D1FAE5; color: #065F46; padding: 1rem; border-radius: 8px;}
    .stButton>button {width: 100%; background-color: #2563EB; color: white; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3429/3429149.png", width=80)
    st.title("TemanDosen")
    st.write("Partner Strategis Menuju Guru Besar")
    st.divider()
    
    st.header("🛠️ Data Input")
    
    # INPUT UTAMA: SCHOLAR ID
    scholar_id_input = st.text_input("Masukkan ID Google Scholar", placeholder="Contoh: 3lUcciYAAAAJ")
    st.caption("ℹ️ ID ada di URL profil Anda. Contoh: scholar.google.com/citations?user=**3lUcciYAAAAJ**")
    
    rumpun_ilmu = st.text_input("Rumpun Ilmu / Prodi", placeholder="Contoh: Pariwisata Halal")
    
    jabatan = st.selectbox("Jabatan Saat Ini", 
                           ["CPNS/Tenaga Pengajar", "Asisten Ahli", "Lektor", "Lektor Kepala", "Guru Besar"])
    
    pendidikan = st.selectbox("Pendidikan Terakhir", ["S2 (Magister)", "S3 (Doktor)"])
    
    tombol_analisa = st.button("🚀 Analisa Karier")
    
    st.divider()
    st.info("Versi: 5.1 (Scholar ID Only)")

# --- FUNGSI AI AUTO-DETECT (ANTI ERROR 404) ---
def get_gemini_response(prompt):
    try:
        # Coba model terbaru dulu
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt)
    except:
        try:
            # Jika gagal, coba model standar
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content(prompt)
        except Exception as e:
            return f"Error Koneksi AI: {e}"

# --- LOGIKA UTAMA ---
if tombol_analisa:
    if not scholar_id_input:
        st.warning("⚠️ Mohon masukkan ID Google Scholar dulu!")
        st.stop()
    
    if " " in scholar_id_input:
        st.error("❌ ID Google Scholar tidak boleh mengandung spasi! Pastikan Anda hanya memasukkan kode unik (contoh: 3lUcciYAAAAJ).")
        st.stop()

    col1, col2 = st.columns([1, 2])
    
    with col2:
        st.markdown(f'<p class="main-header">🎓 Analisis Karier & Roadmap</p>', unsafe_allow_html=True)
        st.markdown(f"Analisis untuk ID: **{scholar_id_input}** | Bidang: **{rumpun_ilmu}**", unsafe_allow_html=True)
        
        # Container Status
        status_box = st.status("🔍 Memulai proses audit...", expanded=True)
        
        try:
            # 1. SETUP PROXY (Agar tidak diblokir Google)
            pg = ProxyGenerator()
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            status_box.write("✅ Proxy aman.")

            # 2. TARIK DATA DARI ID
            status_box.write(f"📥 Mengambil data dari ID: {scholar_id_input}...")
            
            # --- INI KUNCI PERUBAHANNYA: SEARCH_AUTHOR_ID ---
            author = scholarly.search_author_id(scholar_id_input)
            author = scholarly.fill(author) # Ambil detail lengkap
            
            nama_dosen = author.get('name')
            st.success(f"✅ Data Ditemukan: {nama_dosen} ({author.get('affiliation')})")
            status_box.write("✅ Data profil & publikasi berhasil ditarik.")

            # 3. SIAPKAN DATA UNTUK AI
            status_box.write("🤖 Menghubungi AI untuk analisis...")
            
            # Setup API Key
            if "GEMINI_API_KEY" in st.secrets:
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            else:
                st.error("API Key belum disetting di Streamlit Secrets!")
                st.stop()

            # Prompt
            prompt = f"""
            Bertindaklah sebagai Asesor Penilaian Angka Kredit (PAK) Indonesia.
            
            DATA DOSEN:
            - Nama: {nama_dosen}
            - Jabatan Saat Ini: {jabatan}
            - Pendidikan: {pendidikan}
            - Rumpun Ilmu: {rumpun_ilmu}
            - H-Index Scopus/Scholar: {author.get('hindex')}
            - Total Sitasi: {author.get('citedby')}
            - Jumlah Publikasi Terdeteksi: {len(author.get('publications'))}
            
            3 JUDUL PUBLIKASI TERBARU:
            {[pub['bib']['title'] for pub in author.get('publications')[:3]]}

            TUGAS ANDA:
            1. BERIKAN STATUS SAAT INI: Apakah H-Index dan sitasi sudah cukup untuk naik jabatan ke tahap selanjutnya? (Jujur dan tegas).
            2. REKOMENDASI TOPIK RISET: Berikan 3 ide judul penelitian spesifik tentang '{rumpun_ilmu}' yang berpotensi tembus jurnal Q1 tahun depan.
            3. ROADMAP TAHUNAN: Buat rencana aksi (Action Plan) singkat untuk 12 bulan ke depan agar bisa naik jabatan.
            
            Gunakan bahasa Indonesia formal, format poin-poin agar mudah dibaca.
            """

            # 4. EKSEKUSI AI (Dengan Auto-Detect)
            response = get_gemini_response(prompt)
            
            status_box.update(label="Analisis Selesai!", state="complete", expanded=False)
            
            # TAMPILKAN HASIL
            st.markdown("---")
            if isinstance(response, str): # Jika error teks
                st.error(response)
            else:
                st.write(response.text)

        except Exception as e:
            status_box.update(label="Terjadi Kesalahan", state="error")
            st.error(f"Gagal memproses data: {e}")
            st.warning("Tips: Pastikan ID Scholar benar. Jika error proxy, coba Refresh halaman.")
