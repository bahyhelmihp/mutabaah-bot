import os
import subprocess
import zipfile
import base64

ROOT_DIR = "/home/bahy/aibrain/mutabaah-bot"
ASSETS_DIR = os.path.join(ROOT_DIR, "presentation_assets")
SCREENSHOTS_DIR = os.path.join(ASSETS_DIR, "screenshots")
SLIDES_IMG_DIR = os.path.join(ASSETS_DIR, "slide_images")
os.makedirs(SLIDES_IMG_DIR, exist_ok=True)

def img_b64(filename):
    path = os.path.join(SCREENSHOTS_DIR, filename)
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{data}"
    return ""

img_start = img_b64("01_registration_and_start.png")
img_fill = img_b64("02_fill_flow_tilawah.png")
img_confirm = img_b64("03_summary_confirmation.png")
img_settings = img_b64("04_settings_amalan.png")
img_picker = img_b64("05_date_picker_missing.png")
img_progress = img_b64("06_progress_personal.png")
img_admin = img_b64("07_admin_dashboard.png")

CSS_STYLES = """
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
  
  @page {
    size: 1920px 1080px;
    margin: 0;
  }
  
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  
  body {
    background: #061412;
    color: #F8FAFC;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  
  .slide {
    width: 1920px;
    height: 1080px;
    max-height: 1080px;
    page-break-after: always;
    position: relative;
    overflow: hidden;
    background: radial-gradient(circle at top right, #0F3E33 0%, #061814 60%, #030D0A 100%);
    padding: 35px 70px 65px 70px; max-height: 1080px; overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  
  .slide::before {
    content: '';
    position: absolute;
    top: -150px;
    right: -150px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }
  
  .slide::after {
    content: '';
    position: absolute;
    bottom: -150px;
    left: -150px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(212, 175, 55, 0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }
  
  .slide-header {
    position: relative;
    z-index: 2;
  }
  
  .badge-category {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34D399;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
  }
  
  .slide-title {
    font-size: 40px;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.15;
    letter-spacing: -0.5px;
  }
  
  .slide-subtitle {
    font-size: 19px;
    color: #94A3B8;
    margin-top: 6px;
    font-weight: 400;
  }
  
  .slide-footer {
    position: absolute;
    bottom: 18px;
    left: 70px;
    right: 70px;
    z-index: 10;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    padding-top: 14px;
    font-size: 14.5px;
    color: #94A3B8;
  }
  
  .footer-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
    color: #94A3B8;
  }
  
  .footer-dot {
    width: 6px;
    height: 6px;
    background: #10B981;
    border-radius: 50%;
  }
  
  .slide-cover {
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 80px 140px;
    background: radial-gradient(circle at center, #0F493B 0%, #061B16 50%, #020A08 100%);
  }
  
  .cover-logo {
    width: 95px;
    height: 95px;
    background: linear-gradient(135deg, #059669, #10B981);
    border-radius: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 50px;
    box-shadow: 0 15px 35px rgba(16, 185, 129, 0.35);
    margin-bottom: 26px;
  }
  
  .cover-title {
    font-size: 62px;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.15;
    margin-bottom: 18px;
    letter-spacing: -1px;
  }
  
  .cover-title span {
    background: linear-gradient(135deg, #34D399, #FBBF24);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .cover-desc {
    font-size: 23px;
    color: #CBD5E1;
    max-width: 950px;
    line-height: 1.5;
    margin-bottom: 40px;
    font-weight: 400;
  }
  
  .cover-meta {
    display: flex;
    gap: 28px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(10px);
    padding: 14px 34px;
    border-radius: 100px;
    font-size: 16.5px;
    color: #94A3B8;
  }
  
  .cover-meta strong {
    color: #F8FAFC;
  }
  
  .slide-content {
    position: relative;
    z-index: 2;
    flex: 1;
    display: flex;
    align-items: center;
    margin: 18px 0;
  }
  
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
    width: 100%;
  }
  
  .grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 24px;
    width: 100%;
  }
  
  .card {
    background: rgba(18, 38, 32, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 26px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
  }
  
  .card-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34D399;
    font-size: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
  }
  
  .card-title {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 10px;
  }
  
  .card-desc {
    font-size: 15.5px;
    color: #94A3B8;
    line-height: 1.55;
  }
  
  .compare-box {
    padding: 30px;
    border-radius: 18px;
    border: 1px solid;
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .compare-box.old {
    background: rgba(30, 20, 20, 0.6);
    border-color: rgba(239, 68, 68, 0.3);
  }
  
  .compare-box.new {
    background: rgba(15, 45, 35, 0.7);
    border-color: rgba(16, 185, 129, 0.4);
    box-shadow: 0 15px 35px rgba(16, 185, 129, 0.15);
  }
  
  .compare-badge {
    font-size: 13.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: inline-block;
    padding: 6px 14px;
    border-radius: 8px;
    width: fit-content;
  }
  
  .old .compare-badge {
    background: rgba(239, 68, 68, 0.2);
    color: #F87171;
  }
  
  .new .compare-badge {
    background: rgba(16, 185, 129, 0.2);
    color: #34D399;
  }
  
  .list-item {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    font-size: 16px;
    line-height: 1.45;
    color: #CBD5E1;
  }
  
  .list-icon {
    font-size: 18px;
    margin-top: 1px;
  }
  
  .split-layout {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 45px;
    align-items: center;
    width: 100%;
  }
  
  .split-layout.double-shot {
    grid-template-columns: 1fr 1fr;
    gap: 36px;
  }
  
  .steps-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .step-row {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 15px;
    padding: 12px 18px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
  }
  
  .step-num {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, #059669, #10B981);
    color: white;
    font-weight: 800;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 6px 14px rgba(16, 185, 129, 0.3);
  }
  
  .step-info h4 {
    font-size: 18px;
    color: #FFFFFF;
    margin-bottom: 4px;
    font-weight: 700;
  }
  
  .step-info p {
    font-size: 14.5px;
    color: #94A3B8;
    line-height: 1.45;
  }
  
  .step-info code {
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    padding: 2px 7px;
    border-radius: 5px;
    font-size: 13.5px;
  }
  
  .screenshot-wrapper {
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .screenshot-frame {
    background: #0E1621;
    border: 3px solid #1E2C3A;
    border-radius: 22px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
    overflow: hidden;
    max-height: 480px;
    display: flex;
    justify-content: center;
  }
  
  .screenshot-frame img {
    height: 470px;
    width: auto;
    object-fit: contain;
    display: block;
  }
  
  .stat-hero-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 22px;
    margin-bottom: 18px;
    width: 100%;
  }
  
  .stat-hero-card {
    background: rgba(18, 38, 32, 0.7);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 18px;
    padding: 22px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    position: relative;
    overflow: hidden;
  }
  
  .stat-hero-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, #10B981, #F59E0B);
  }
  
  .stat-hero-val {
    font-size: 50px;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.1;
    margin: 6px 0;
  }
  
  .stat-hero-val span {
    font-size: 24px;
    font-weight: 500;
    color: #34D399;
  }
  
  .stat-hero-label {
    font-size: 14.5px;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .stat-pill-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    width: 100%;
  }
  
  .stat-pill {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 18px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .stat-pill-name {
    font-size: 15px;
    color: #E2E8F0;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .stat-pill-num {
    font-size: 18px;
    font-weight: 700;
    color: #FBBF24;
  }
"""

SLIDES_DATA = [
    # Slide 1
    f"""
<div class="slide slide-cover">
  <div class="cover-logo">🕌</div>
  <h1 class="cover-title">Mutabaah Yaumiyah <span>Telegram Bot</span></h1>
  <p class="cover-desc">
    Digitalisasi Pencatatan & Evaluasi Ibadah Harian Muslim Indonesia di Korea Selatan Terintegrasi Google Sheets secara Real-Time.
  </p>
  <div class="cover-meta">
    <div>Inisiatif: <strong>IMA Korea (Indonesian Muslim Association in Korea)</strong></div>
    <div>•</div>
    <div>Periode Evaluasi: <strong>Oktober 2026</strong></div>
    <div>•</div>
    <div>Platform: <strong>Telegram Bot & Google Cloud</strong></div>
  </div>
</div>
""",

    # Slide 2
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">Latar Belakang & Masalah</div>
    <h2 class="slide-title">Mengapa Mutabaah Bot Dibuat?</h2>
    <p class="slide-subtitle">Tantangan pencatatan mutabaah manual dan transformasi digital untuk jamaah IMA Korea.</p>
  </div>
  
  <div class="slide-content">
    <div class="grid-2">
      <div class="compare-box old">
        <div class="compare-badge">Kondisi Sebelumnya (Manual Spreadsheet di HP)</div>
        <div class="list-item">
          <div class="list-icon">❌</div>
          <div><b>Tampilan Rumit di HP:</b> Spreadsheet memiliki belasan kolom horizontal yang sulit digeser dan lambat dibuka pada smartphone.</div>
        </div>
        <div class="list-item">
          <div class="list-icon">❌</div>
          <div><b>Risiko Kerusakan Data:</b> Anggota rawan salah mengisi baris orang lain, atau tidak sengaja menghapus formula dan data rekap bersama.</div>
        </div>
        <div class="list-item">
          <div class="list-icon">❌</div>
          <div><b>Sering Terlupa:</b> Tidak ada sistem pengingat personal. Banyak jamaah baru mengisi di akhir bulan atau bahkan berhenti mengisi.</div>
        </div>
        <div class="list-item">
          <div class="list-icon">❌</div>
          <div><b>Rekap Pengurus Melelahkan:</b> Pengurus harus menghitung persentase dan keaktifan puluhan anggota secara manual setiap bulan.</div>
        </div>
      </div>
      
      <div class="compare-box new">
        <div class="compare-badge">Solusi Baru (Bot Telegram Interaktif)</div>
        <div class="list-item">
          <div class="list-icon">✅</div>
          <div><b>Pengisian Cepat 30 Detik:</b> Cukup klik tombol interaktif di Telegram tanpa perlu membuka aplikasi spreadsheet atau zoom in/out.</div>
        </div>
        <div class="list-item">
          <div class="list-icon">✅</div>
          <div><b>Keamanan & Privasi Terjamin:</b> Tiap user hanya mengakses akunnya sendiri. Data tersimpan aman via Google Sheets API (Upsert).</div>
        </div>
        <div class="list-item">
          <div class="list-icon">✅</div>
          <div><b>Pengingat Harian Otomatis:</b> Bot otomatis mengirimkan reminder pukul 21:00 KST (Asia/Seoul) bagi yang belum mengisi hari ini.</div>
        </div>
        <div class="list-item">
          <div class="list-icon">✅</div>
          <div><b>Dashboard & Analytics Realtime:</b> Evaluasi capaian personal (`/progress`) dan panel admin (`/stats`) otomatis terhitung akurat.</div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 2 / 10</div>
  </div>
</div>
""",

    # Slide 3
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">Arsitektur & Fitur</div>
    <h2 class="slide-title">Fitur-Fitur Utama Mutabaah Bot</h2>
    <p class="slide-subtitle">Solusi komprehensif yang dirancang fleksibel sesuai kebutuhan ibadah masing-masing anggota.</p>
  </div>
  
  <div class="slide-content">
    <div class="grid-3">
      <div class="card">
        <div class="card-icon">⚡</div>
        <div class="card-title">2 Moda Pengisian Fleksibel</div>
        <div class="card-desc">Bisa <b>Isi Semua Berurutan</b> (panduan langkah demi langkah) atau <b>Isi Satu Amalan Cepat</b> untuk memperbarui amalan tertentu saja.</div>
      </div>
      <div class="card">
        <div class="card-icon">🎯</div>
        <div class="card-title">Kustomisasi Amalan & Target</div>
        <div class="card-desc">Anggota bebas memilih amalan yang dimutabaah via checklist (`/amalan`) dan menyesuaikan target angka harian/bulanan (`/target`).</div>
      </div>
      <div class="card">
        <div class="card-icon">🕌</div>
        <div class="card-title">11 Amalan Yaumiyah Lengkap</div>
        <div class="card-desc">Tilawah, Sholat Wajib, Rawatib, Al-Ma’tsurat, Shalawat, Istighfar, Tadabbur, Shaum Sunnah, Qiyamulail, Dhuha, dan Olahraga.</div>
      </div>
      <div class="card">
        <div class="card-icon">🔄</div>
        <div class="card-title">Smart Upsert & Seoul Time</div>
        <div class="card-desc">Pembaruan data tanpa menimpa amalan lain yang sudah diisi di hari yang sama. Selaras zona waktu Korea (<code>Asia/Seoul</code>).</div>
      </div>
      <div class="card">
        <div class="card-icon">🔔</div>
        <div class="card-title">Pengingat Harian (21:00 KST)</div>
        <div class="card-desc">Notifikasi sopan di malam hari khusus bagi anggota terdaftar yang belum menyelesaikan mutabaah harian mereka.</div>
      </div>
      <div class="card">
        <div class="card-icon">📊</div>
        <div class="card-title">Progress & Panel Admin</div>
        <div class="card-desc">Rekap personal real-time (`/progress`) serta panel pengurus (`/admin`, `/stats`) dengan auto-sync ke sheet rangkuman eksekutif.</div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 3 / 10</div>
  </div>
</div>
""",

    # Slide 4
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">Value Proposition</div>
    <h2 class="slide-title">Manfaat Nyata bagi Jamaah & Pengurus</h2>
    <p class="slide-subtitle">Memberikan dampak langsung terhadap konsistensi ibadah dan kemudahan operasional dakwah.</p>
  </div>
  
  <div class="slide-content">
    <div class="grid-2">
      <div class="card" style="border-left: 4px solid #10B981;">
        <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
          <div class="card-icon" style="margin:0;">👤</div>
          <div>
            <h3 style="font-size:24px; color:#FFFFFF;">Bagi Anggota / Jamaah</h3>
            <p style="color:#34D399; font-size:14px; font-weight:600;">Kemudahan & Istiqomah Personal</p>
          </div>
        </div>
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div class="list-item">
            <div class="list-icon">✨</div>
            <div><b>Praktis & Super Cepat:</b> Pengisian hanya memakan waktu 30-60 detik tepat sebelum tidur tanpa aplikasi tambahan.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">✨</div>
            <div><b>Menjaga Konsistensi (Self-Accountability):</b> Daily reminder dan evaluasi bulanan memacu semangat untuk terus istiqomah.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">✨</div>
            <div><b>Fleksibel & Adil:</b> Amalan yang tidak diaktifkan tidak mengurangi persentase capaian target bulanan.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">✨</div>
            <div><b>Privasi Terjaga:</b> Anggota mengisi tanpa rasa sungkan atau canggung dibanding spreadsheet terbuka bersama.</div>
          </div>
        </div>
      </div>
      
      <div class="card" style="border-left: 4px solid #F59E0B;">
        <div style="display:flex; align-items:center; gap:16px; margin-bottom:16px;">
          <div class="card-icon" style="margin:0; background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.3); color:#FBBF24;">🏛️</div>
          <div>
            <h3 style="font-size:24px; color:#FFFFFF;">Bagi Pengurus IMA Korea</h3>
            <p style="color:#FBBF24; font-size:14px; font-weight:600;">Efisiensi & Akurasi Data Dakwah</p>
          </div>
        </div>
        <div style="display:flex; flex-direction:column; gap:14px;">
          <div class="list-item">
            <div class="list-icon">⭐</div>
            <div><b>Otomatisasi Penuh (Zero Manual Work):</b> Data dari puluhan anggota langsung tersinkron ke Google Sheets tanpa rekap tangan.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">⭐</div>
            <div><b>Integritas Data Terjamin:</b> Menghilangkan risiko formula rusak, baris terhapus, atau data saling menimpa.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">⭐</div>
            <div><b>Monitoring Keaktifan Real-Time:</b> Pengurus dapat melihat tingkat partisipasi (76.7%) dan agregat ibadah kapan saja via `/stats`.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">⭐</div>
            <div><b>Skalabilitas Luas:</b> Mampu menampung ratusan anggota IMA di seluruh penjuru Korea Selatan dengan infrastruktur cloud Google.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 4 / 10</div>
  </div>
</div>
""",

    # Slide 5
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">User Guide (Panduan Pengguna) • 1/4</div>
    <h2 class="slide-title">Memulai Bot & Menu Utama</h2>
    <p class="slide-subtitle">Langkah pendaftaran mandiri yang cepat dan navigasi menu interaktif.</p>
  </div>
  
  <div class="slide-content">
    <div class="split-layout">
      <div class="steps-container">
        <div class="step-row">
          <div class="step-num">1</div>
          <div class="step-info">
            <h4>Buka Bot & Mulai</h4>
            <p>Cari bot di Telegram dan klik tombol <b>Start</b> atau kirim perintah <code>/start</code>.</p>
          </div>
        </div>
        <div class="step-row">
          <div class="step-num">2</div>
          <div class="step-info">
            <h4>Pendaftaran Nama Lengkap</h4>
            <p>Untuk anggota baru, bot akan menanyakan nama lengkap satu kali saja. Ketik nama Anda (contoh: <i>Bahy Helmi</i>).</p>
          </div>
        </div>
        <div class="step-row">
          <div class="step-num">3</div>
          <div class="step-info">
            <h4>Menu Utama Interaktif</h4>
            <p>Setelah terdaftar, bot menampilkan 4 tombol menu utama:</p>
            <p style="margin-top:6px; color:#E2E8F0;">
              • <b>📝 Isi Mutabaah Hari Ini</b>: Mulai pengisian harian<br>
              • <b>📊 Lihat Progress Saya</b>: Cek rekap pencapaian bulan ini<br>
              • <b>✏️ Edit / Isi Hari Lain</b>: Koreksi atau isi hari terlewat<br>
              • <b>⚙️ Pengaturan Amalan & Target</b>: Kustomisasi amalan
            </p>
          </div>
        </div>
      </div>
      
      <div class="screenshot-wrapper">
        <div class="screenshot-frame">
          <img src="{img_start}" alt="Start & Registration">
        </div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 5 / 10</div>
  </div>
</div>
""",

    # Slide 6
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">User Guide (Panduan Pengguna) • 2/4</div>
    <h2 class="slide-title">Alur Pengisian Amalan & Konfirmasi</h2>
    <p class="slide-subtitle">Panduan langkah pengisian dengan opsi tombol cepat dan ringkasan sebelum disimpan.</p>
  </div>
  
  <div class="slide-content">
    <div class="split-layout double-shot">
      <div class="card" style="padding: 20px; align-items:center;">
        <h4 style="font-size:19px; color:#34D399; margin-bottom:10px; align-self:flex-start;">Tahap 1: Pertanyaan Interaktif</h4>
        <p style="font-size:14px; color:#94A3B8; margin-bottom:14px; align-self:flex-start;">
          Tersedia tombol angka cepat (misal: <b>20 hal Target</b>, 10 hal, 5 hal, 0 hal) atau klik <b>✏️ Input Angka Sendiri</b>.
        </p>
        <div class="screenshot-frame" style="max-height: 400px;">
          <img src="{img_fill}" alt="Fill Flow Tilawah" style="height: 390px;">
        </div>
      </div>
      
      <div class="card" style="padding: 20px; align-items:center;">
        <h4 style="font-size:19px; color:#34D399; margin-bottom:10px; align-self:flex-start;">Tahap 2: Ringkasan & Konfirmasi</h4>
        <p style="font-size:14px; color:#94A3B8; margin-bottom:14px; align-self:flex-start;">
          Setelah semua amalan dijawab, bot menampilkan rekapitulasi. Klik <b>💾 Simpan</b> untuk otomatis sync ke Google Sheets.
        </p>
        <div class="screenshot-frame" style="max-height: 400px;">
          <img src="{img_confirm}" alt="Summary Confirmation" style="height: 390px;">
        </div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 6 / 10</div>
  </div>
</div>
""",

    # Slide 7
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">User Guide (Panduan Pengguna) • 3/4</div>
    <h2 class="slide-title">Kustomisasi Amalan & Pengisian Susulan</h2>
    <p class="slide-subtitle">Menyesuaikan amalan aktif pribadi serta mengisi mutabaah tanggal-tanggal yang terlewat.</p>
  </div>
  
  <div class="slide-content">
    <div class="split-layout double-shot">
      <div class="card" style="padding: 20px; align-items:center;">
        <h4 style="font-size:19px; color:#34D399; margin-bottom:10px; align-self:flex-start;">Kustomisasi Amalan (`/amalan`)</h4>
        <p style="font-size:14px; color:#94A3B8; margin-bottom:14px; align-self:flex-start;">
          Klik nama amalan untuk mengaktifkan (✅) atau menonaktifkan (❌). Amalan nonaktif tidak ditanyakan dan tidak mengurangi skor.
        </p>
        <div class="screenshot-frame" style="max-height: 400px;">
          <img src="{img_settings}" alt="Settings Amalan" style="height: 390px;">
        </div>
      </div>
      
      <div class="card" style="padding: 20px; align-items:center;">
        <h4 style="font-size:19px; color:#34D399; margin-bottom:10px; align-self:flex-start;">Pilih Tanggal & Susulan (`/edit`)</h4>
        <p style="font-size:14px; color:#94A3B8; margin-bottom:14px; align-self:flex-start;">
          Kalender pintar mendeteksi hari yang sudah diisi (<span style="color:#34D399;">✅ hijau</span>) dan hari yang terlewat (<span style="color:#F87171;">🔴 merah</span>) untuk diisi kapan saja.
        </p>
        <div class="screenshot-frame" style="max-height: 400px;">
          <img src="{img_picker}" alt="Date Picker Missing" style="height: 390px;">
        </div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 7 / 10</div>
  </div>
</div>
""",

    # Slide 8
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">User Guide (Panduan Pengguna) • 4/4</div>
    <h2 class="slide-title">Pantau Progress & Panel Admin</h2>
    <p class="slide-subtitle">Evaluasi pencapaian bulanan personal dan fasilitas khusus monitoring pengurus.</p>
  </div>
  
  <div class="slide-content">
    <div class="split-layout double-shot">
      <div class="card" style="padding: 20px; align-items:center;">
        <h4 style="font-size:19px; color:#34D399; margin-bottom:10px; align-self:flex-start;">Progress Bulanan Anggota (`/progress`)</h4>
        <p style="font-size:14px; color:#94A3B8; margin-bottom:14px; align-self:flex-start;">
          Menampilkan bar visual, persentase tiap amalan, dan daftar tanggal yang belum terisi lengkap dengan tombol susulan langsung.
        </p>
        <div class="screenshot-frame" style="max-height: 400px;">
          <img src="{img_progress}" alt="Progress Personal" style="height: 390px;">
        </div>
      </div>
      
      <div class="card" style="padding: 20px; align-items:center;">
        <h4 style="font-size:19px; color:#F59E0B; margin-bottom:10px; align-self:flex-start;">Panel Khusus Pengurus (`/admin` & `/stats`)</h4>
        <p style="font-size:14px; color:#94A3B8; margin-bottom:14px; align-self:flex-start;">
          Khusus ID terdaftar. Menampilkan ringkasan seluruh jamaah, leaderboard bulanan, dan tombol sinkronisasi otomatis ke Google Sheets.
        </p>
        <div class="screenshot-frame" style="max-height: 400px;">
          <img src="{img_admin}" alt="Admin Dashboard" style="height: 390px;">
        </div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 8 / 10</div>
  </div>
</div>
""",

    # Slide 9
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category" style="background:rgba(245,158,11,0.15); border-color:rgba(245,158,11,0.3); color:#FBBF24;">Status Terkini & Pencapaian</div>
    <h2 class="slide-title">Laporan Data Aktif (Oktober 2026)</h2>
    <p class="slide-subtitle">Data riil langsung dari database Google Sheets terpusat IMA Korea (per 26 Oktober 2026).</p>
  </div>
  
  <div class="slide-content" style="flex-direction:column; justify-content:center;">
    <div class="stat-hero-grid">
      <div class="stat-hero-card">
        <div class="stat-hero-label">Total Anggota Terdaftar</div>
        <div class="stat-hero-val">30 <span>orang</span></div>
        <p style="font-size:13px; color:#94A3B8;">Muslim Indonesia di Korea</p>
      </div>
      <div class="stat-hero-card">
        <div class="stat-hero-label">Anggota Aktif Mengisi</div>
        <div class="stat-hero-val" style="color:#34D399;">23 <span>orang</span></div>
        <p style="font-size:13px; color:#34D399;">Tingkat Partisipasi 76.7%</p>
      </div>
      <div class="stat-hero-card">
        <div class="stat-hero-label">Total Entri Mutabaah</div>
        <div class="stat-hero-val" style="color:#FBBF24;">90 <span>entri</span></div>
        <p style="font-size:13px; color:#94A3B8;">Tersimpan realtime di Sheet</p>
      </div>
      <div class="stat-hero-card">
        <div class="stat-hero-label">Rata-rata Capaian Target</div>
        <div class="stat-hero-val" style="color:#60A5FA;">40.8<span>%</span></div>
        <p style="font-size:13px; color:#94A3B8;">Akumulasi seluruh amalan</p>
      </div>
    </div>
    
    <div class="stat-pill-grid">
      <div class="stat-pill">
        <div class="stat-pill-name">📖 Tilawah Al-Qur'an</div>
        <div class="stat-pill-num">734 hal</div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-name">🌸 Shalawat Nabi</div>
        <div class="stat-pill-num">4,214x</div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-name">🤲 Istighfar</div>
        <div class="stat-pill-num">5,431x</div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-name">🕌 Sholat Wajib</div>
        <div class="stat-pill-num">246 waktu</div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-name">🌙 Sholat Rawatib</div>
        <div class="stat-pill-num">216 rakaat</div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-name">📿 Dzikir Al-Ma'tsurat</div>
        <div class="stat-pill-num">67 kali</div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-name">📜 Tadabbur Qur'an</div>
        <div class="stat-pill-num">49 ayat</div>
      </div>
      <div class="stat-pill">
        <div class="stat-pill-name">🏃 Aktivitas Olahraga</div>
        <div class="stat-pill-num">775 menit</div>
      </div>
    </div>
    <div style="margin-top:12px; font-size:14.5px; color:#94A3B8; text-align:center;">
      ✨ Plus Capaian Amalan Sunnah: <b>12 Hari Shaum Sunnah</b> • <b>27 Malam Qiyamulail</b> • <b>26 Hari Sholat Dhuha</b>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea</div>
    <div>Slide 9 / 10</div>
  </div>
</div>
""",

    # Slide 10
    f"""
<div class="slide">
  <div class="slide-header">
    <div class="badge-category">Kesimpulan & Masa Depan</div>
    <h2 class="slide-title">Dampak Nyata & Rencana Pengembangan</h2>
    <p class="slide-subtitle">Membangun ekosistem ibadah yang konsisten dan saling mendukung di perantauan.</p>
  </div>
  
  <div class="slide-content">
    <div class="grid-2">
      <div class="card">
        <div class="card-icon">🚀</div>
        <div class="card-title">Dampak Positif Saat Ini</div>
        <div style="display:flex; flex-direction:column; gap:14px; margin-top:8px;">
          <div class="list-item">
            <div class="list-icon">✅</div>
            <div><b>Partisipasi Melonjak:</b> 76.7% anggota aktif mengisi mutabaah secara konsisten setiap pekan.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">✅</div>
            <div><b>Nol Hambatan Akses:</b> Mengeliminasi sepenuhnya kerumitan mengedit file spreadsheet di HP.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">✅</div>
            <div><b>Transparansi Pengurus:</b> Rekapitulasi dapat dicek langsung dalam hitungan detik via command <code>/stats</code>.</div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-icon">💡</div>
        <div class="card-title">Rencana Pengembangan (Roadmap)</div>
        <div style="display:flex; flex-direction:column; gap:14px; margin-top:8px;">
          <div class="list-item">
            <div class="list-icon">📌</div>
            <div><b>Weekly Motivation & Recognition:</b> Notifikasi apresiasi berkala bagi jamaah yang paling istiqomah.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">📌</div>
            <div><b>Grafik Tren Pribadi:</b> Visualisasi grafik tren peningkatan ibadah anggota dari bulan ke bulan.</div>
          </div>
          <div class="list-item">
            <div class="list-icon">📌</div>
            <div><b>Jadwal Sholat Korea & Pengingat Imsak:</b> Integrasi pengingat waktu sholat lokal wilayah Korea Selatan.</div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <div class="slide-footer">
    <div class="footer-brand"><span class="footer-dot"></span> Mutabaah Bot IMA Korea • Bersama Meraih Ridho Allah di Negeri Ginseng</div>
    <div>Slide 10 / 10</div>
  </div>
</div>
"""
]

# Assemble complete HTML deck
all_slides_html = "\n".join(SLIDES_DATA)
HTML_DOCUMENT = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Mutabaah Yaumiyah Bot - IMA Korea</title>
<style>
{CSS_STYLES}
</style>
</head>
<body>
{all_slides_html}
<script>
  let currentSlide = 0;
  const slides = document.querySelectorAll('.slide');
  function showSlide(idx) {{
    if (idx < 0) idx = 0;
    if (idx >= slides.length) idx = slides.length - 1;
    currentSlide = idx;
    slides[currentSlide].scrollIntoView({{ behavior: 'smooth' }});
  }}
  window.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{
      e.preventDefault();
      showSlide(currentSlide + 1);
    }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
      e.preventDefault();
      showSlide(currentSlide - 1);
    }} else if (e.key.toLowerCase() === 'f') {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen();
      }} else {{
        document.exitFullscreen();
      }}
    }}
  }});
</script>
</body>
</html>
"""

html_file = os.path.join(ROOT_DIR, "Mutabaah_Bot_Presentation.html")
pdf_file = os.path.join(ROOT_DIR, "Mutabaah_Bot_Presentation.pdf")
pptx_file = os.path.join(ROOT_DIR, "Mutabaah_Bot_Presentation.pptx")

with open(html_file, "w", encoding="utf-8") as f:
    f.write(HTML_DOCUMENT)
print(f"Saved complete HTML deck to {html_file}")

# Generate PDF
print("Generating PDF presentation...")
cmd_pdf = [
    "google-chrome",
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    "--hide-scrollbars",
    f"--print-to-pdf={pdf_file}",
    html_file
]
subprocess.run(cmd_pdf, check=True)
print(f"Generated PDF: {pdf_file}")

# Render individual slides to PNG
slide_images = []
for i, s_html in enumerate(SLIDES_DATA, start=1):
    single_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{CSS_STYLES}
body {{ margin: 0; padding: 0; background: #061412; }}
.slide {{ page-break-after: unset; }}
</style>
</head>
<body>
{s_html}
</body>
</html>"""
    tmp_path = f"/tmp/single_slide_{i}.html"
    slide_png = os.path.join(SLIDES_IMG_DIR, f"slide_{i:02d}.png")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(single_html)
    
    cmd_shot = [
        "google-chrome",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1920,1167",
        f"--screenshot={slide_png}",
        tmp_path
    ]
    subprocess.run(cmd_shot, check=True)
    from PIL import Image
    im = Image.open(slide_png)
    if im.size != (1920, 1080):
        im = im.crop((0, 0, 1920, 1080))
        im.save(slide_png)
    slide_images.append(slide_png)
    print(f"Rendered slide {i}: {slide_png}")

# Create PPTX
print("Building PPTX package...")
cx = 12192000
cy = 6858000

with zipfile.ZipFile(pptx_file, 'w', zipfile.ZIP_DEFLATED) as z:
    ct = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '  <Default Extension="xml" ContentType="application/xml"/>',
        '  <Default Extension="png" ContentType="image/png"/>',
        '  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
    ]
    for idx in range(1, len(slide_images) + 1):
        ct.append(f'  <Override PartName="/ppt/slides/slide{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    ct.append('</Types>')
    z.writestr('[Content_Types].xml', "\n".join(ct))

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""
    z.writestr('_rels/.rels', rels)

    p_rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
    ]
    for idx in range(1, len(slide_images) + 1):
        p_rels.append(f'  <Relationship Id="rId{idx+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{idx}.xml"/>')
    p_rels.append('</Relationships>')
    z.writestr('ppt/_rels/presentation.xml.rels', "\n".join(p_rels))

    pres = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"',
        '                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"',
        '                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">',
        '  <p:sldMasterIdLst>',
        '    <p:sldMasterId id="2147483648" r:id="rId1"/>',
        '  </p:sldMasterIdLst>',
        '  <p:sldIdLst>'
    ]
    for idx in range(1, len(slide_images) + 1):
        pres.append(f'    <p:sldId id="{255 + idx}" r:id="rId{idx+1}"/>')
    pres.extend([
        '  </p:sldIdLst>',
        f'  <p:sldSz cx="{cx}" cy="{cy}" type="screen16x9"/>',
        '  <p:notesSz cx="6858000" cy="9144000"/>',
        '</p:presentation>'
    ])
    z.writestr('ppt/presentation.xml', "\n".join(pres))

    theme = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="0D3B2E"/></a:dk2>
      <a:lt2><a:srgbClr val="F8FAFC"/></a:lt2>
      <a:accent1><a:srgbClr val="10B981"/></a:accent1>
      <a:accent2><a:srgbClr val="F59E0B"/></a:accent2>
      <a:accent3><a:srgbClr val="3B82F6"/></a:accent3>
      <a:accent4><a:srgbClr val="8B5CF6"/></a:accent4>
      <a:accent5><a:srgbClr val="EC4899"/></a:accent5>
      <a:accent6><a:srgbClr val="14B8A6"/></a:accent6>
      <a:hlink><a:srgbClr val="10B981"/></a:hlink>
      <a:folHlink><a:srgbClr val="059669"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office">
      <a:majorFont><a:latin typeface="Segoe UI"/></a:majorFont>
      <a:minorFont><a:latin typeface="Segoe UI"/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidClr><a:schemeClr val="phClr"/></a:solidClr></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="9525"><a:solidClr><a:schemeClr val="phClr"/></a:solidClr></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectLst/></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidClr><a:schemeClr val="phClr"/></a:solidClr></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""
    z.writestr('ppt/theme/theme1.xml', theme)

    sm_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""
    z.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', sm_rels)

    sm = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
</p:sldMaster>"""
    z.writestr('ppt/slideMasters/slideMaster1.xml', sm)

    sl_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""
    z.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', sl_rels)

    sl = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMap/></p:clrMapOvr>
</p:sldLayout>"""
    z.writestr('ppt/slideLayouts/slideLayout1.xml', sl)

    for idx, img_path in enumerate(slide_images, start=1):
        img_filename = f"image{idx}.png"
        with open(img_path, "rb") as imf:
            z.writestr(f"ppt/media/{img_filename}", imf.read())
        
        s_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{img_filename}"/>
</Relationships>"""
        z.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", s_rels)

        s_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
      <p:pic>
        <p:nvPicPr>
          <p:cNvPr id="{idx + 1}" name="Slide {idx}"/>
          <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
          <p:nvPr/>
        </p:nvPicPr>
        <p:blipFill>
          <a:blip r:embed="rId2"/>
          <a:stretch><a:fillRect/></a:stretch>
        </p:blipFill>
        <p:spPr>
          <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
      </p:pic>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMap/></p:clrMapOvr>
</p:sld>"""
        z.writestr(f"ppt/slides/slide{idx}.xml", s_xml)

print(f"PPTX ready: {pptx_file} ({os.path.getsize(pptx_file)} bytes)")
print("ALL DONE PERFECTLY!")
