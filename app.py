import streamlit as st
import google.generativeai as genai
from scholarly import scholarly

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="TemanDosen Pro",
    page_icon="🎓",
    layout="wide"
)

# --- 2. MANAJEMEN MEMORI (SESSION STATE) ---
# Ini fitur PENTING untuk menghemat kuota API Key Anda.
# Aplikasi akan "mengingat" hasil agar tidak perlu tanya Google berulang kali.
if 'analisis_tersimpan' not in st.session_state:
    st.session_state['analisis_tersimpan'] = None
if 'data_dosen_tersimpan' not in st.session_state:
    st.session_state['data_dosen_tersimpan'] = None

# Fungsi untuk menghapus ingatan jika user mengganti input
def reset_memory():
    st.session_state['analisis_tersimpan'] = None
    st.session_state['data_dosen_tersimpan'] = None

# --- 3. JUDUL & INFO ---
st.markdown("## 🎓 TemanDosen: Asisten Karier Akademik")
st.caption("✅ System Status: Secure API | ⚡ Model: Gemini 1.5 Flash (Optimized)")
st.divider()

# --- 4. KONEKSI KE BRANKAS (SECRETS) ---
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception as e:
        st.error(f"Kunci bermasalah: {e}")
        st.stop()
else:
    st.error("⚠️ API Key belum ditemukan!")
    st.info("👉 Masuk ke Settings -> Secrets -> Masukkan: GEMINI_API_KEY = 'kunci-baru-anda'")
    st.stop()

# --- 5. KOLOM INPUT USER ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📂 Data Digital")
    # on_change=reset_memory artinya: kalau teks diganti, hasil lama dibuang
    raw_id = st.text_input("Link / ID Google Scholar", 
                          placeholder="Contoh: 3lUcciYAAAAJ", 
                          on_change=reset_memory)
    
    # Pembersih ID Pintar
    scholar_id = raw_id
    if "user=" in raw_id:
        try: scholar_id = raw_id.split("user=")[1].split("&")[0]
        except: pass

    rumpun = st.text_input("Rumpun Ilmu / Prodi", 
                          placeholder="Contoh: Manajemen Pemasaran", 
                          on_change=reset_memory)

with col2:
    st.subheader("🎓 Status Akademik")
    jabatan = st.selectbox("Jabatan Saat Ini", 
                          ["Tenaga Pengajar", "Asisten Ahli", "Lektor", "Lektor Kepala", "Guru Besar"],
                          on_change=reset_memory)
    
    pendidikan = st.selectbox("Pendidikan Terakhir", 
                             ["S2 (Magister)", "S3 (Doktor)"],
                             on_change=reset_memory)

st.markdown("---")

# --- 6. TOMBOL EKSEKUSI ---
# Logika tombol pintar:
# Jika belum ada hasil -> Tampilkan tombol "Analisa"
# Jika sudah ada hasil -> Tampilkan tombol "Analisa Ulang"
if st.session_state['analisis_tersimpan'] is None:
    tombol_klik = st.button("🚀 Mulai Analisa (Hemat Kuota)", type="primary", use_container_width=True)
else:
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.success("✅ Hasil analisis ditampilkan dari memori (Gratis).")
    with col_b:
        tombol_reset = st.button("🔄 Analisa Ulang", use_container_width=True)
        if tombol_reset:
            reset_memory()
            st.rerun()
    tombol_klik = False

# --- 7. MESIN UTAMA (LOGIKA BACKEND) ---
if tombol_klik:
    if not scholar_id:
        st.toast("⚠️ Mohon isi ID Google Scholar dulu!", icon="🚫")
    else:
        # Container agar tampilan rapi
        container = st.container(border=True)
        status_box = container.status("🔍 Sedang bekerja...", expanded=True)
        
        try:
            # TAHAP A: AMBIL DATA SCHOLAR
            status_box.write("📂 Mengubungi server Google Scholar...")
            
            # Kita cari profilnya
            search_query = scholarly.search_author_id(scholar_id)
            author = scholarly.fill(search_query) # Tarik data lengkap
            
            # Ambil data penting saja
            nama_dosen = author.get('name')
            h_index = author.get('hindex')
            # Ambil 5 judul publikasi teratas, atau beri pesan jika kosong
            raw_pubs = author.get('publications', [])
            publikasi = [pub['bib']['title'] for pub in raw_pubs[:5]] if raw_pubs else ["Belum ada publikasi online"]
            
            # Simpan data dosen ke memori
            st.session_state['data_dosen_tersimpan'] = {
                'nama': nama_dosen,
                'h_index': h_index
            }
            
            status_box.write(f"✅ Profil Ditemukan: {nama_dosen} (H-Index: {h_index})")
            
            # TAHAP B: KIRIM KE AI (GEMINI FLASH)
            status_box.write("🤖 Mengirim data ke Gemini 1.5 Flash...")
            
            # Prompt Engineering (Instruksi ke AI)
            prompt_text = f"""
            Kamu adalah Konsultan Karier Dosen Senior di Indonesia.
            
            PROFIL KLIEN:
            - Nama: {nama_dosen}
            - Jabatan: {jabatan}
            - Pendidikan: {pendidikan}
            - Rumpun Ilmu: {rumpun}
            - H-Index Scholar: {h_index}
            - 5 Publikasi Terakhir: {publikasi}
            
            TUGAS:
            1. **Analisis Kenaikan Pangkat**: Berdasarkan data di atas, apa hambatan utama untuk naik ke jenjang berikutnya (atau ke Guru Besar)? Jelaskan to the point.
            2. **Ide Riset 2025**: Berikan 3 judul penelitian spesifik dalam bidang '{rumpun}' yang berpotensi tinggi masuk Q1 atau Viral tahun depan.
            3. **Roadmap 12 Bulan**: Buat checklist bulanan (Bulan 1-12) apa yang harus dilakukan dosen ini.
            
            Gunakan format Markdown yang rapi, bold untuk poin penting, dan bahasa yang profesional namun memotivasi.
            """
            
            # Panggil Model (Force Flash agar irit)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt_text)
            
            # Simpan hasil ke memori
            st.session_state['analisis_tersimpan'] = response.text
            
            status_box.update(label="Selesai!", state="complete", expanded=False)
            st.rerun() # Refresh halaman untuk menampilkan hasil

        except Exception as e:
            status_box.update(label="Terjadi Kesalahan", state="error")
            st.error(f"Error Detail: {e}")
            
            # Deteksi Error Spesifik untuk User
            msg = str(e).lower()
            if "429" in msg:
                st.warning("🛑 KUOTA HABIS: API Key Anda mencapai batas harian. Ganti Key atau coba besok.")
            elif "404" in msg:
                st.warning("🛑 DATA TIDAK DITEMUKAN: Pastikan ID Scholar benar.")

# --- 8. TAMPILKAN HASIL ---
if st.session_state['analisis_tersimpan']:
    dosen = st.session_state['data_dosen_tersimpan']
    st.header(f"📊 Hasil Analisis: {dosen['nama']}")
    st.success(f"H-Index Saat Ini: **{dosen['h_index']}**")
    
    # Tampilkan teks dari AI
    st.markdown(st.session_state['analisis_tersimpan'])
    
    # Pesan penutup
    st.info("💡 Tips: Simpan halaman ini atau copy hasilnya. Jika Anda refresh, data masih tersimpan selama tab tidak ditutup.")
