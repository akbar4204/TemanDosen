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
    # 1. Panggil Robot Pencari (Gunakan nama_dosen)
    author = get_scholar_data_safe(nama_dosen)

    # 2. Cek apakah Dosen Ditemukan
    if author is None:
        st.error("Maaf, data dosen tidak ditemukan atau koneksi Google Scholar sedang sibuk. Silakan coba lagi nanti.")
        st.stop() # Berhenti paksa

    # 3. Cek Kelengkapan Input (Gunakan nama_dosen juga!)
    if not nama_dosen or not rumpun_ilmu:
        st.toast("⚠️ Mohon lengkapi Nama Dosen dan Rumpun Ilmu!", icon="⚠️")
    else:
        # Jika semua aman, tampilkan hasil
        st.markdown(f'<p class="main-header">🎓 Analisis Karier & Roadmap</p>', unsafe_allow_html=True)
        st.markdown(f"Analisis untuk: **{rumpun_ilmu}** | Status: **{jabatan}**", unsafe_allow_html=True)

        status_box = st.status("🔄 Mengaudit data profil...", expanded=True)

        try:
            # --- MASUKKAN KODE AI DI SINI (GANTIKAN 'pass') ---
            
            # 1. Setup Kunci Rahasia
            my_api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=my_api_key)

            # 2. Siapkan Prompt
            prompt = f"Analisis dosen ini: {author} untuk rumpun ilmu {rumpun_ilmu}..."
            
            # 3. Panggil Gemini
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            # 4. Tampilkan Hasil
            status_box.update(label="Selesai!", state="complete")
            st.markdown(response.text)
            # --------------------------------------------------

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

            # Auto-Detect Model
            model_name = 'models/gemini-pro'
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        if 'flash' in m.name: model_name = m.name; break
            except: pass
            model = genai.GenerativeModel(model_name)

            # --- TARIK DATA SCHOLAR ---
            status_box.write("🔍 Mengambil data publikasi & sitasi...")
            author = scholarly.search_author_id(scholar_id)
            author = scholarly.fill(author)
            
            # --- AI THINKING (GABUNGAN PROMPT V3 & V4) ---
            status_box.write("🧠 Mengkalkulasi Gap & Menyusun Timeline...")
            
            paper_titles = [p['bib']['title'] for p in author['publications'][:10]]
            current_year = datetime.datetime.now().year
            
            # PROMPT RAKSASA (Menggabungkan Gap Analysis + Roadmap Detil)
            prompt = f"""
            Role: Asesor Penilaian Angka Kredit (PAK) Nasional & Konsultan Karier.
            Tugas: Lakukan Audit GAP ANALYSIS dan buat ROADMAP DETIL.
            
            DATA DOSEN:
            - Nama: {author['name']}
            - Jabatan: {jabatan}
            - Pendidikan: {pendidikan}
            - Rumpun Ilmu: {rumpun_ilmu}
            - H-Index: {author.get('hindex')}
            - Paper: {paper_titles}
            - Tahun: {current_year}
            
            INSTRUKSI LOGIKA:
            1. Jika CPNS, roadmap wajib mulai dari Latsar/AA. Jangan mimpi Guru Besar < 5 tahun.
            2. Cek Linearitas antara Rumpun Ilmu vs Judul Paper.
            3. Skor Barometer (0-100) berdasarkan Pendidikan, Jabatan, dan H-Index.

            OUTPUT WAJIB JSON (Struktur Gabungan):
            {{
                "gap_analysis": {{
                    "pendidikan_score": 50,
                    "penelitian_score": 30,
                    "pengajaran_score": 10,
                    "syarat_khusus_score": 0,
                    "gap_utama": "Sebutkan 1 kekurangan paling fatal",
                    "linearitas_status": "Aman/Warning/Bahaya",
                    "linearitas_pesan": "Komentar kesesuaian bidang"
                }},
                "roadmap_detil": [
                    {{"periode": "Semester 1 ({current_year})", "kegiatan": "...", "detail": "..."}},
                    {{"periode": "Semester 2 ({current_year})", "kegiatan": "...", "detail": "..."}},
                    {{"periode": "Tahun {current_year+1}", "kegiatan": "...", "detail": "..."}},
                    {{"periode": "Jangka Panjang ({current_year+3}+)", "kegiatan": "...", "detail": "..."}}
                ],
                "saran_narasi": "Paragraf nasihat strategis untuk dosen ini."
            }}
            """
            
            response = model.generate_content(prompt)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            status_box.update(label="Selesai!", state="complete", expanded=False)

            # --- 4. TAMPILAN TABS (INTI GABUNGAN) ---
            
            tab_gap, tab_roadmap, tab_profil = st.tabs(["📊 Gap Analysis (Audit)", "🗺️ Roadmap Timeline", "👤 Profil Data"])

            # === TAB 1: GAP ANALYSIS (Fitur MVP Baru) ===
            with tab_gap:
                st.subheader("🏁 Barometer Kesiapan Guru Besar")
                
                # Barometer
                scores = data['gap_analysis']
                c1, c2, c3, c4 = st.columns(4)
                
                def render_bar(col, label, score):
                    with col:
                        st.write(f"**{label}**")
                        st.progress(score / 100, text=f"{score}%")
                
                render_bar(c1, "🎓 Pendidikan", scores['pendidikan_score'])
                render_bar(c2, "🔬 Penelitian", scores['penelitian_score'])
                render_bar(c3, "🏫 Pengajaran", scores['pengajaran_score'])
                render_bar(c4, "🌟 Syarat Khusus", scores['syarat_khusus_score'])
                
                st.divider()
                
                # Linearitas & Gap Utama
                col_warn, col_msg = st.columns([1, 3])
                with col_warn:
                    status_lin = scores['linearitas_status']
                    color = "green" if "Aman" in status_lin else "orange" if "Warning" in status_lin else "red"
                    st.markdown(f"""
                    <div style="text-align:center; padding:20px; border:2px solid {color}; border-radius:10px;">
                        <h3 style="color:{color}; margin:0;">{status_lin}</h3>
                        <small>Status Linearitas</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_msg:
                    st.markdown(f"**🕵️ Analisis Linearitas:** {scores['linearitas_pesan']}")
                    st.error(f"**🔥 GAP PALING KRITIS:** {scores['gap_utama']}")
                    st.info(f"💡 **Saran Strategis:** {data['saran_narasi']}")

            # === TAB 2: TIMELINE ROADMAP (Fitur V3 Lama) ===
            with tab_roadmap:
                st.subheader("🗓️ Peta Jalan Karier (Step-by-Step)")
                st.write("Berikut adalah langkah taktis yang harus Anda eksekusi per semester:")
                
                for step in data['roadmap_detil']:
                    st.markdown(f"""
                    <div class="card-timeline">
                        <div class="card-date">{step['periode']}</div>
                        <div style="font-size: 1.1em; font-weight: bold; margin-top:5px; color:#2C3E50;">{step['kegiatan']}</div>
                        <div style="color: #666; margin-top:5px;">ℹ️ {step['detail']}</div>
                    </div>
                    """, unsafe_allow_html=True)

         # ... (kode sebelumnya bagian tab_gap dan tab_roadmap) ...

            # === TAB 3: PROFIL DATA (Pelengkap) ===
            # Pastikan indentasi 'with tab_profil:' sejajar dengan 'with tab_roadmap:' sebelumnya
            with tab_profil:
                col_header, col_stats = st.columns([1, 3])
                
                with col_header:
                    # Foto Profil
                    st.image(author.get('url_picture', 'https://via.placeholder.com/150'), use_container_width=True)
                
                with col_stats:
                    # Nama & Afiliasi
                    st.markdown(f"### {author['name']}")
                    st.write(f"🏢 **Afiliasi:** {author.get('affiliation', 'Tidak ada data afiliasi')}")
                    st.write(f"📧 **Email:** {author.get('email_domain', '-')}")
                    st.caption(f"🧠 **Minat Riset:** {', '.join(author.get('interests', []))}")
                    
                    st.divider()
                    
                    # Statistik Utama (Metrics)
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Sitasi", author.get('citedby', 0))
                    m2.metric("H-Index", author.get('hindex', 0))
                    m3.metric("i10-Index", author.get('i10index', 0))
                    m4.metric("Sitasi 5 Thn", author.get('citedby5y', 0))

                st.divider()
                
                # Grafik Tren Sitasi
                st.subheader("📈 Tren Sitasi Tahunan")
                if 'cites_per_year' in author:
                    st.bar_chart(author['cites_per_year'])
                else:
                    st.info("Data tren tahunan tidak tersedia di profil ini.")

        except Exception as e:
            status_box.update(label="Gagal Memproses", state="error")
            st.error(f"Error: {e}")

# Pastikan 'else' ini sejajar dengan 'if tombol_analisa:' yang ada jauh di atas
else:

    st.info("👈 Silakan isi data di Sidebar untuk memulai Audit Karier Anda.")





