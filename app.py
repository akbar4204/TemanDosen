import streamlit as st
from scholarly import scholarly, ProxyGenerator # Pastikan ProxyGenerator di-import

# --- KONFIGURASI PROXY (AGAR TIDAK DIBLOKIR GOOGLE) ---
if 'proxy_setup' not in st.session_state:
    try:
        pg = ProxyGenerator()
        success = pg.FreeProxies() # Menggunakan Proxy Gratis
        if success:
            scholarly.use_proxy(pg)
            st.session_state['proxy_setup'] = True
            print("✅ Proxy berhasil dipasang!")
        else:
            print("⚠️ Gagal memasang proxy, mencoba koneksi langsung.")
    except Exception as e:
        print(f"⚠️ Error Proxy: {e}")
import google.generativeai as genai
import json
import datetime
import time
import random
from fake_useragent import UserAgent

# --- FUNGSI PENCARIAN BARU (LEBIH PINTAR) ---
def get_scholar_data_safe(input_text):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Bersihkan input
            input_text = input_text.strip()
            
            # DETEKSI: Apakah ini ID atau NAMA?
            # Jika tidak ada spasi dan panjangnya unik, anggap ID
            if " " not in input_text and len(input_text) < 20:
                print(f"🕵️ Mencoba mencari via ID: {input_text} (Percobaan {attempt+1})")
                author = scholarly.search_author_id(input_text)
            else:
                # Jika ada spasi, anggap NAMA
                print(f"🕵️ Mencoba mencari via Nama: {input_text} (Percobaan {attempt+1})")
                search_query = scholarly.search_author(input_text)
                author = next(search_query) # Ambil orang pertama yang muncul

            # Wajib: Ambil data lengkap (publikasi, dll)
            return scholarly.fill(author)

        except StopIteration:
            # Error ini muncul jika Nama tidak ada di database Google
            st.warning(f"❌ Nama '{input_text}' tidak ditemukan di Google Scholar.")
            return None
        except Exception as e:
            # Tampilkan error asli di layar agar kita tahu penyebabnya
            print(f"Error: {e}")
            if attempt == max_retries - 1:
                st.error(f"⚠️ Gagal mengambil data. Google mungkin memblokir koneksi. Detail Error: {e}")
                return None
            time.sleep(random.uniform(2, 5)) # Istirahat dulu sebelum coba lagi
            
    return None
# ==================================
# --- 1. KONFIGURASI TAMPILAN & CSS (GABUNGAN) ---
st.set_page_config(page_title="TemanDosen Ultimate", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .main-header {font-size: 2.2rem; color: #2C3E50; font-weight: 700; margin-bottom: 0px;}
    .sub-header {font-size: 1.1rem; color: #7f8c8d; margin-bottom: 20px;}
    
    /* Style untuk Gap Analysis (Barometer) */
    .metric-card {background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
    
    /* Style untuk Timeline (V3 Lama) */
    .card-timeline {
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 5px solid #2C3E50; 
        margin-bottom: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .card-date {font-weight: bold; color: #2980b9; font-size: 1.1rem;}
    
    /* Warning Box */
    .gap-alert {padding: 15px; border-radius: 8px; background-color: #fff3cd; border-left: 5px solid #ffc107; color: #856404;}
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.title("TemanDosen")
    st.markdown("---")
    st.write("### 🛠️ Data Dosen")
    
    nama_dosen = st.text_input("Masukkan Nama / ID Google Scholar")
    rumpun_ilmu = st.text_input("Rumpun Ilmu / Prodi", placeholder="Cth: Manajemen, Teknik Sipil")
    jabatan = st.selectbox("Jabatan Saat Ini:", ["CPNS/Tenaga Pengajar", "Asisten Ahli", "Lektor", "Lektor Kepala", "Guru Besar"])
    pendidikan = st.selectbox("Pendidikan Terakhir:", ["S2 (Magister)", "Sedang S3", "S3 (Doktor)"])
    
    tombol_analisa = st.button("🚀 Analisa Komprehensif", type="primary")
    st.markdown("---")
    st.caption("v5.0 - Ultimate Integrated")

# --- 3. LOGIKA UTAMA ---
if tombol_analisa:
    # --- MULAI DATA DUMMY (DATA PURA-PURA) ---
    # Kita set manual datanya agar tidak perlu konek ke Google (Anti Blokir)
    author = {
        "name": nama_dosen,
        "affiliation": "Universitas (Data Dummy)",
        "interests": ["Pariwisata Halal", "Ekonomi Islam", "Manajemen Pemasaran"],
        "citedby": 254,
        "hindex": 8,
        "publications": [
            {"bib": {"title": "Analisis Potensi Pariwisata Halal di Indonesia", "pub_year": "2021"}},
            {"bib": {"title": "Perilaku Konsumen Muslim dalam Memilih Hotel Syariah", "pub_year": "2022"}},
            {"bib": {"title": "Strategi Branding Produk Halal UMKM", "pub_year": "2023"}},
            {"bib": {"title": "Dampak Sertifikasi Halal Terhadap Penjualan", "pub_year": "2020"}},
            {"bib": {"title": "Tantangan Industri Halal Global", "pub_year": "2019"}}
        ]
    }
    # --- SELESAI DATA DUMMY ---

    # Cek apakah Data Kosong
    if author is None:
        st.error("Maaf, data dosen tidak ditemukan.")
        st.stop()

    # Cek Kelengkapan Input
    if not nama_dosen or not rumpun_ilmu:
        st.toast("⚠️ Mohon lengkapi Nama Dosen dan Rumpun Ilmu!", icon="⚠️")
    else:
        # Jika aman, tampilkan Judul
        st.markdown(f'<p class="main-header">🎓 Analisis Karier & Roadmap</p>', unsafe_allow_html=True)
        st.markdown(f"Analisis untuk: **{rumpun_ilmu}** | Status: **{jabatan}**", unsafe_allow_html=True)

        status_box = st.status("🤖 Mengaudit data profil...", expanded=True)

        try:
            # --- SETUP AI ---
            # 1. Ambil API Key
            my_api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=my_api_key)

            # 2. Siapkan Prompt (Perintah untuk AI)
            prompt = f"""
            Bertindaklah sebagai Konsultan Karier Akademik Senior.
            Saya seorang dosen dengan profil berikut:
            Nama: {author.get('name')}
            Afiliasi: {author.get('affiliation')}
            Minat Riset: {author.get('interests')}
            Total Sitasi: {author.get('citedby')}
            H-Index: {author.get('hindex')}
            Publikasi Terakhir: {author.get('publications')}

            Tugas Anda:
            1. Analisis apakah performa riset saya sudah baik untuk naik jabatan ke Guru Besar.
            2. Berikan 3 topik riset spesifik yang sedang tren di bidang '{rumpun_ilmu}' yang bisa menaikkan sitasi saya.
            3. Buat roadmap/timeline kasar untuk 2 tahun ke depan agar saya bisa mencapai Guru Besar.

            Gunakan bahasa Indonesia yang profesional, memotivasi, dan terstruktur.
            """

            # 3. Panggil Gemini (GANTI KE MODEL TERBARU: gemini-1.5-flash)
            status_box.write("Mnghubungi AI Cerdas...")
            model = genai.GenerativeModel('gemini-pro') 
            response = model.generate_content(prompt)

            # 4. Tampilkan Hasil
            status_box.update(label="Selesai!", state="complete")
            st.markdown("### 📋 Hasil Analisis AI")
            st.write(response.text)

        except Exception as e:
            status_box.update(label="Error", state="error")
            st.error(f"Terjadi kesalahan pada AI: {e}")











