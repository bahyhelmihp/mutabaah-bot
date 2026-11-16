import subprocess
import os

TEMPLATES = {
    "01_registration_and_start": """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0E1621; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
  .chat-container { width: 440px; background: #0E1621; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #1E2C3A; }
  .chat-header { background: #17212B; padding: 12px 16px; display: flex; align-items: center; border-bottom: 1px solid #1E2C3A; }
  .avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #059669, #10B981); display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin-right: 12px; }
  .header-info h3 { font-size: 15px; color: #FFFFFF; font-weight: 600; }
  .header-info p { font-size: 12px; color: #708499; }
  .chat-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #0E1621; }
  
  .msg { max-width: 88%; padding: 10px 14px; border-radius: 14px; font-size: 14px; line-height: 1.45; position: relative; }
  .msg-incoming { background: #182533; color: #F5F5F5; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid #233446; }
  .msg-outgoing { background: #2B5278; color: #FFFFFF; align-self: flex-end; border-bottom-right-radius: 4px; }
  .msg-time { font-size: 10px; color: #708499; float: right; margin-left: 8px; margin-top: 4px; }
  .msg-outgoing .msg-time { color: #8CAFC8; }
  
  .inline-keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
  .kb-btn { background: #243547; color: #64B5F6; border: 1px solid #2F445A; padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 500; text-align: center; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; }
  .highlight { color: #4ADE80; font-weight: 600; }
</style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">🕌</div>
    <div class="header-info">
      <h3>Mutabaah Bot IMA Korea</h3>
      <p>bot • resmi IMA Korea</p>
    </div>
  </div>
  <div class="chat-body">
    <div class="msg msg-outgoing">
      /start
      <span class="msg-time">20:58 ✓✓</span>
    </div>
    <div class="msg msg-incoming">
      Assalamu’alaikum! Sebelum memulai, mari berkenalan terlebih dahulu.<br><br>
      <b>Siapa nama Anda?</b>
      <span class="msg-time">20:58</span>
    </div>
    <div class="msg msg-outgoing">
      Bahy Helmi
      <span class="msg-time">20:59 ✓✓</span>
    </div>
    <div class="msg msg-incoming">
      Alhamdulillah, salam kenal <span class="highlight">Bahy Helmi</span>! Pendaftaran berhasil. 🎉<br><br>
      Secara default, seluruh amalan yaumiyah aktif dengan target standar.<br><br>
      <b>Silakan isi amalan hari ini.</b> Data otomatis tersinkronisasi ke Google Sheet.
      <span class="msg-time">20:59</span>
      
      <div class="inline-keyboard">
        <div class="kb-btn">📝 Isi Mutabaah Hari Ini</div>
        <div class="kb-btn">📊 Lihat Progress Saya</div>
        <div class="kb-btn">✏️ Edit / Isi Hari Lain</div>
        <div class="kb-btn">⚙️ Pengaturan Amalan & Target</div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
""",

    "02_fill_flow_tilawah": """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0E1621; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
  .chat-container { width: 440px; background: #0E1621; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #1E2C3A; }
  .chat-header { background: #17212B; padding: 12px 16px; display: flex; align-items: center; border-bottom: 1px solid #1E2C3A; }
  .avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #059669, #10B981); display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin-right: 12px; }
  .header-info h3 { font-size: 15px; color: #FFFFFF; font-weight: 600; }
  .header-info p { font-size: 12px; color: #708499; }
  .chat-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #0E1621; }
  
  .msg { max-width: 90%; padding: 10px 14px; border-radius: 14px; font-size: 14px; line-height: 1.45; position: relative; }
  .msg-incoming { background: #182533; color: #F5F5F5; align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid #233446; }
  .msg-outgoing { background: #2B5278; color: #FFFFFF; align-self: flex-end; border-bottom-right-radius: 4px; }
  .msg-time { font-size: 10px; color: #708499; float: right; margin-left: 8px; margin-top: 4px; }
  
  .inline-keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
  .kb-row { display: flex; gap: 6px; }
  .kb-btn { flex: 1; background: #243547; color: #64B5F6; border: 1px solid #2F445A; padding: 9px 8px; border-radius: 8px; font-size: 12.5px; font-weight: 500; text-align: center; }
  .kb-btn.primary { background: #1B4332; color: #52B788; border-color: #2D6A4F; font-weight: 600; }
  .badge { background: #1E3A5F; color: #90CAF9; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; display: inline-block; margin-bottom: 6px; }
</style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">🕌</div>
    <div class="header-info">
      <h3>Mutabaah Bot IMA Korea</h3>
      <p>bot • pengisian amalan interaktif</p>
    </div>
  </div>
  <div class="chat-body">
    <div class="msg msg-outgoing">
      📝 Isi Mutabaah Hari Ini
      <span class="msg-time">21:05 ✓✓</span>
    </div>
    <div class="msg msg-incoming">
      <span class="badge">Langkah 1 dari 11</span><br>
      📖 <b>Tilawah Al-Qur'an</b><br>
      <i>Berapa halaman Al-Qur'an yang Anda baca hari ini?</i><br>
      <small style="color: #94A3B8;">Target harian Anda: 20 halaman</small>
      <span class="msg-time">21:05</span>
      
      <div class="inline-keyboard">
        <div class="kb-row">
          <div class="kb-btn primary">✨ 20 hal (Target)</div>
          <div class="kb-btn">10 hal</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn">5 hal</div>
          <div class="kb-btn">0 hal (Belum)</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn">✏️ Input Angka Sendiri</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn" style="color: #EF4444; border-color: #7F1D1D;">❌ Batalkan</div>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
""",

    "03_summary_confirmation": """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0E1621; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
  .chat-container { width: 440px; background: #0E1621; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #1E2C3A; }
  .chat-header { background: #17212B; padding: 12px 16px; display: flex; align-items: center; border-bottom: 1px solid #1E2C3A; }
  .avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #059669, #10B981); display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin-right: 12px; }
  .header-info h3 { font-size: 15px; color: #FFFFFF; font-weight: 600; }
  .header-info p { font-size: 12px; color: #708499; }
  .chat-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #0E1621; }
  
  .msg { width: 100%; padding: 12px 14px; border-radius: 14px; font-size: 13.5px; line-height: 1.45; position: relative; }
  .msg-incoming { background: #182533; color: #F5F5F5; align-self: flex-start; border: 1px solid #233446; }
  .msg-time { font-size: 10px; color: #708499; float: right; margin-left: 8px; margin-top: 4px; }
  
  .rekap-box { background: #101B26; padding: 10px 12px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #10B981; font-size: 12.5px; }
  .rekap-item { display: flex; justify-content: space-between; padding: 3px 0; }
  .rekap-item span.val { color: #34D399; font-weight: 600; }
  
  .inline-keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
  .kb-btn { background: #243547; color: #64B5F6; border: 1px solid #2F445A; padding: 10px 8px; border-radius: 8px; font-size: 13px; font-weight: 600; text-align: center; }
  .kb-btn.success { background: #065F46; color: #A7F3D0; border-color: #047857; }
</style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">🕌</div>
    <div class="header-info">
      <h3>Mutabaah Bot IMA Korea</h3>
      <p>bot • konfirmasi & simpan</p>
    </div>
  </div>
  <div class="chat-body">
    <div class="msg msg-incoming">
      📋 <b>Ringkasan Mutabaah Hari Ini</b><br>
      <small style="color:#94A3B8;">Tanggal: 26 Oktober 2026 (Asia/Seoul)</small>
      
      <div class="rekap-box">
        <div class="rekap-item"><span>📖 Tilawah:</span> <span class="val">20 halaman (100%)</span></div>
        <div class="rekap-item"><span>🕌 Sholat Wajib:</span> <span class="val">5 waktu (100%)</span></div>
        <div class="rekap-item"><span>🌙 Rawatib:</span> <span class="val">12 rakaat (100%)</span></div>
        <div class="rekap-item"><span>📿 Al-Ma'tsurat:</span> <span class="val">2 kali (100%)</span></div>
        <div class="rekap-item"><span>🌸 Shalawat:</span> <span class="val">100 kali (100%)</span></div>
        <div class="rekap-item"><span>🤲 Istighfar:</span> <span class="val">100 kali (100%)</span></div>
        <div class="rekap-item"><span>📜 Tadabbur:</span> <span class="val">1 ayat (100%)</span></div>
        <div class="rekap-item"><span>🍽️ Shaum Sunnah:</span> <span class="val">✅ Ya</span></div>
        <div class="rekap-item"><span>🌃 Qiyamulail:</span> <span class="val">✅ Ya</span></div>
        <div class="rekap-item"><span>☀️ Dhuha:</span> <span class="val">✅ Ya</span></div>
        <div class="rekap-item"><span>🏃 Olahraga:</span> <span class="val">✅ Ya</span></div>
      </div>
      
      <i>Apakah data di atas sudah sesuai?</i>
      <span class="msg-time">21:12</span>
      
      <div class="inline-keyboard">
        <div class="kb-btn success">💾 Simpan ke Google Sheets</div>
        <div class="kb-btn">✏️ Koreksi Amalan Tertentu</div>
        <div class="kb-btn" style="color: #EF4444; border-color: #7F1D1D;">❌ Batalkan</div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
""",

    "04_settings_amalan": """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0E1621; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
  .chat-container { width: 440px; background: #0E1621; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #1E2C3A; }
  .chat-header { background: #17212B; padding: 12px 16px; display: flex; align-items: center; border-bottom: 1px solid #1E2C3A; }
  .avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #059669, #10B981); display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin-right: 12px; }
  .header-info h3 { font-size: 15px; color: #FFFFFF; font-weight: 600; }
  .header-info p { font-size: 12px; color: #708499; }
  .chat-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #0E1621; }
  
  .msg { width: 100%; padding: 12px 14px; border-radius: 14px; font-size: 13.5px; line-height: 1.45; position: relative; }
  .msg-incoming { background: #182533; color: #F5F5F5; align-self: flex-start; border: 1px solid #233446; }
  .msg-time { font-size: 10px; color: #708499; float: right; margin-left: 8px; margin-top: 4px; }
  
  .inline-keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
  .kb-row { display: flex; gap: 6px; }
  .kb-btn { flex: 1; background: #243547; color: #FFFFFF; border: 1px solid #2F445A; padding: 8px 6px; border-radius: 8px; font-size: 12px; font-weight: 500; text-align: left; }
  .kb-btn.active { border-left: 3px solid #10B981; }
  .kb-btn.inactive { opacity: 0.6; border-left: 3px solid #EF4444; }
  .kb-btn.done { background: #1E3A5F; color: #90CAF9; text-align: center; font-weight: 600; padding: 10px; }
</style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">🕌</div>
    <div class="header-info">
      <h3>Mutabaah Bot IMA Korea</h3>
      <p>bot • kustomisasi amalan</p>
    </div>
  </div>
  <div class="chat-body">
    <div class="msg msg-incoming">
      ⚙️ <b>Kustomisasi Amalan yang Dimutabaah</b><br>
      <small style="color: #94A3B8;">Klik untuk toggle (aktif / nonaktif). Amalan nonaktif tidak ditanyakan dan tidak mengurangi skor Anda.</small>
      <span class="msg-time">21:20</span>
      
      <div class="inline-keyboard">
        <div class="kb-row">
          <div class="kb-btn active">✅ 📖 Tilawah</div>
          <div class="kb-btn active">✅ 🕌 Sholat Wajib</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn active">✅ 🌙 Rawatib</div>
          <div class="kb-btn active">✅ 📿 Al-Ma’tsurat</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn active">✅ 🌸 Shalawat</div>
          <div class="kb-btn active">✅ 🤲 Istighfar</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn active">✅ 📜 Tadabbur</div>
          <div class="kb-btn active">✅ 🍽️ Shaum</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn inactive">❌ 🌃 Qiyamulail</div>
          <div class="kb-btn active">✅ ☀️ Dhuha</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn active">✅ 🏃 Olahraga</div>
          <div class="kb-btn active">⚡ Atur Target Angka</div>
        </div>
        <div class="inline-keyboard">
          <div class="kb-btn done">💾 Selesai Simpan Pengaturan</div>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
""",

    "05_date_picker_missing": """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0E1621; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
  .chat-container { width: 440px; background: #0E1621; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #1E2C3A; }
  .chat-header { background: #17212B; padding: 12px 16px; display: flex; align-items: center; border-bottom: 1px solid #1E2C3A; }
  .avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #059669, #10B981); display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin-right: 12px; }
  .header-info h3 { font-size: 15px; color: #FFFFFF; font-weight: 600; }
  .header-info p { font-size: 12px; color: #708499; }
  .chat-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #0E1621; }
  
  .msg { width: 100%; padding: 12px 14px; border-radius: 14px; font-size: 13.5px; line-height: 1.45; position: relative; }
  .msg-incoming { background: #182533; color: #F5F5F5; align-self: flex-start; border: 1px solid #233446; }
  .msg-time { font-size: 10px; color: #708499; float: right; margin-left: 8px; margin-top: 4px; }
  
  .inline-keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
  .kb-row { display: flex; gap: 6px; }
  .kb-btn { flex: 1; background: #243547; color: #FFFFFF; border: 1px solid #2F445A; padding: 8px 6px; border-radius: 8px; font-size: 12px; font-weight: 500; text-align: center; }
  .kb-btn.done { background: #064E3B; border-color: #059669; color: #A7F3D0; }
  .kb-btn.miss { background: #451A1A; border-color: #991B1B; color: #FCA5A5; }
</style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">🕌</div>
    <div class="header-info">
      <h3>Mutabaah Bot IMA Korea</h3>
      <p>bot • pemilihan tanggal & susulan</p>
    </div>
  </div>
  <div class="chat-body">
    <div class="msg msg-incoming">
      🗓️ <b>Pilih Tanggal Mutabaah</b><br>
      Keterangan:<br>
      • <span style="color:#34D399;">✅</span> = Sudah diisi (klik untuk edit)<br>
      • <span style="color:#F87171;">🔴</span> = Belum diisi (klik untuk susulan)
      <span class="msg-time">21:25</span>
      
      <div class="inline-keyboard">
        <div class="kb-row">
          <div class="kb-btn done">✅ Hari Ini (26 Okt)</div>
          <div class="kb-btn done">✅ Kemarin (25 Okt)</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn miss">🔴 Sab, 24 Okt</div>
          <div class="kb-btn done">✅ Jum, 23 Okt</div>
        </div>
        <div class="kb-row">
          <div class="kb-btn miss">🔴 Kam, 22 Okt</div>
          <div class="kb-btn done">✅ Rab, 21 Okt</div>
        </div>
        <div class="inline-keyboard">
          <div class="kb-btn" style="background: #17212B; border-color: #374151;">📅 Ketik Tanggal Lain (YYYY-MM-DD)</div>
          <div class="kb-btn" style="color: #9CA3AF;">🏠 Kembali ke Menu Utama</div>
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
""",

    "06_progress_personal": """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0E1621; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
  .chat-container { width: 440px; background: #0E1621; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #1E2C3A; }
  .chat-header { background: #17212B; padding: 12px 16px; display: flex; align-items: center; border-bottom: 1px solid #1E2C3A; }
  .avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #059669, #10B981); display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin-right: 12px; }
  .header-info h3 { font-size: 15px; color: #FFFFFF; font-weight: 600; }
  .header-info p { font-size: 12px; color: #708499; }
  .chat-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #0E1621; }
  
  .msg { width: 100%; padding: 12px 14px; border-radius: 14px; font-size: 13.5px; line-height: 1.45; position: relative; }
  .msg-incoming { background: #182533; color: #F5F5F5; align-self: flex-start; border: 1px solid #233446; }
  .msg-time { font-size: 10px; color: #708499; float: right; margin-left: 8px; margin-top: 4px; }
  
  .score-card { background: linear-gradient(135deg, #065F46, #047857); padding: 12px; border-radius: 10px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; color: white; }
  .score-val { font-size: 22px; font-weight: 700; color: #A7F3D0; }
  
  .prog-item { margin: 6px 0; font-size: 12.5px; }
  .prog-bar-bg { background: #233446; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 3px; }
  .prog-bar-fill { background: #10B981; height: 100%; border-radius: 3px; }
  
  .inline-keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
  .kb-btn { background: #243547; color: #64B5F6; border: 1px solid #2F445A; padding: 10px 8px; border-radius: 8px; font-size: 13px; font-weight: 500; text-align: center; }
  .kb-btn.warn { background: #451A1A; border-color: #991B1B; color: #FCA5A5; font-weight: 600; }
</style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">🕌</div>
    <div class="header-info">
      <h3>Mutabaah Bot IMA Korea</h3>
      <p>bot • rekap evaluasi bulanan</p>
    </div>
  </div>
  <div class="chat-body">
    <div class="msg msg-incoming">
      📊 <b>Progress Mutabaah Bulan Ini</b><br>
      <small style="color: #94A3B8;">Periode: 1 - 26 Oktober 2026 (Waktu Korea)</small>
      
      <div class="score-card">
        <div>
          <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9;">Capaian Kumulatif</div>
          <div style="font-size: 13px; font-weight: 500;">Aktif 20 dari 26 hari</div>
        </div>
        <div class="score-val">76.9%</div>
      </div>
      
      <div class="prog-item">
        <div style="display:flex; justify-content:space-between;"><span>📖 Tilawah (400 hal / bln)</span><span style="color:#34D399; font-weight:600;">85%</span></div>
        <div class="prog-bar-bg"><div class="prog-bar-fill" style="width: 85%;"></div></div>
      </div>
      <div class="prog-item">
        <div style="display:flex; justify-content:space-between;"><span>🕌 Sholat Wajib (5 waktu)</span><span style="color:#34D399; font-weight:600;">96%</span></div>
        <div class="prog-bar-bg"><div class="prog-bar-fill" style="width: 96%;"></div></div>
      </div>
      <div class="prog-item">
        <div style="display:flex; justify-content:space-between;"><span>🌙 Rawatib (12 rakaat)</span><span style="color:#FBBF24; font-weight:600;">72%</span></div>
        <div class="prog-bar-bg"><div class="prog-bar-fill" style="width: 72%; background: #FBBF24;"></div></div>
      </div>
      <div class="prog-item">
        <div style="display:flex; justify-content:space-between;"><span>📿 Al-Ma'tsurat (2x/hari)</span><span style="color:#34D399; font-weight:600;">80%</span></div>
        <div class="prog-bar-bg"><div class="prog-bar-fill" style="width: 80%;"></div></div>
      </div>
      <div class="prog-item">
        <div style="display:flex; justify-content:space-between;"><span>🏃 Olahraga (Min. 5 mnt)</span><span style="color:#34D399; font-weight:600;">88%</span></div>
        <div class="prog-bar-bg"><div class="prog-bar-fill" style="width: 88%;"></div></div>
      </div>
      
      <div style="margin-top: 8px; font-size: 12px; color: #FCA5A5;">
        ⚠️ <i>Hari belum terisi: 6 hari (tgl 2, 8, 14, 18, 22, 24)</i>
      </div>
      <span class="msg-time">21:30</span>
      
      <div class="inline-keyboard">
        <div class="kb-btn warn">🗓️ Isi Hari yang Kosong / Terlewat</div>
        <div class="kb-btn">📝 Isi Mutabaah Hari Ini</div>
        <div class="kb-btn" style="color: #9CA3AF;">🏠 Menu Utama</div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
""",

    "07_admin_dashboard": """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background: #0E1621; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
  .chat-container { width: 440px; background: #0E1621; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.5); border: 1px solid #1E2C3A; }
  .chat-header { background: #17212B; padding: 12px 16px; display: flex; align-items: center; border-bottom: 1px solid #1E2C3A; }
  .avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #D97706, #F59E0B); display: flex; align-items: center; justify-content: center; font-size: 22px; color: white; margin-right: 12px; }
  .header-info h3 { font-size: 15px; color: #FFFFFF; font-weight: 600; }
  .header-info p { font-size: 12px; color: #F59E0B; font-weight: 500; }
  .chat-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #0E1621; }
  
  .msg { width: 100%; padding: 12px 14px; border-radius: 14px; font-size: 13.5px; line-height: 1.45; position: relative; }
  .msg-incoming { background: #182533; color: #F5F5F5; align-self: flex-start; border: 1px solid #233446; }
  .msg-time { font-size: 10px; color: #708499; float: right; margin-left: 8px; margin-top: 4px; }
  
  .grid-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 8px 0; }
  .card-stat { background: #101B26; padding: 10px; border-radius: 8px; border-left: 3px solid #3B82F6; }
  .stat-label { font-size: 11px; color: #94A3B8; }
  .stat-num { font-size: 18px; font-weight: 700; color: #FFFFFF; }
  
  .rekap-item { display: flex; justify-content: space-between; padding: 2px 0; font-size: 12.5px; }
  
  .inline-keyboard { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
  .kb-btn { background: #243547; color: #64B5F6; border: 1px solid #2F445A; padding: 9px 8px; border-radius: 8px; font-size: 12.5px; font-weight: 500; text-align: center; }
  .kb-btn.action { background: #1E3A5F; color: #90CAF9; font-weight: 600; }
</style>
</head>
<body>
<div class="chat-container">
  <div class="chat-header">
    <div class="avatar">⚡</div>
    <div class="header-info">
      <h3>Admin Panel • Mutabaah IMA</h3>
      <p>Akses Khusus Pengurus</p>
    </div>
  </div>
  <div class="chat-body">
    <div class="msg msg-incoming">
      📊 <b>Statistik Mutabaah IMA Korea</b><br>
      <small style="color: #94A3B8;">Bulan Ini: 1 - 26 Oktober 2026</small>
      
      <div class="grid-stats">
        <div class="card-stat">
          <div class="stat-label">Anggota Terdaftar</div>
          <div class="stat-num">30 <span style="font-size:12px; font-weight:normal; color:#94A3B8;">org</span></div>
        </div>
        <div class="card-stat" style="border-color:#10B981;">
          <div class="stat-label">Anggota Aktif</div>
          <div class="stat-num" style="color:#34D399;">23 <span style="font-size:12px; font-weight:normal; color:#94A3B8;">(76.7%)</span></div>
        </div>
        <div class="card-stat" style="border-color:#F59E0B;">
          <div class="stat-label">Total Entri Data</div>
          <div class="stat-num">90 <span style="font-size:12px; font-weight:normal; color:#94A3B8;">entri</span></div>
        </div>
        <div class="card-stat" style="border-color:#8B5CF6;">
          <div class="stat-label">Rata-rata Capaian</div>
          <div class="stat-num">40.8%</div>
        </div>
      </div>
      
      <div style="background:#101B26; padding:8px 10px; border-radius:8px; font-size:12px; margin: 4px 0;">
        <div class="rekap-item"><span>📖 Tilawah:</span> <b>734 hal</b> (avg 8.2)</div>
        <div class="rekap-item"><span>🌸 Shalawat:</span> <b>4,214x</b> (avg 46.8)</div>
        <div class="rekap-item"><span>🤲 Istighfar:</span> <b>5,431x</b> (avg 60.3)</div>
        <div class="rekap-item"><span>🕌 Sholat Wajib:</span> <b>246 waktu</b></div>
        <div class="rekap-item"><span>🌙 Rawatib:</span> <b>216 rakaat</b></div>
      </div>
      <span class="msg-time">21:35</span>
      
      <div class="inline-keyboard">
        <div class="kb-btn action">🔄 Tulis & Sinkronkan ke Google Sheet Summary</div>
        <div class="kb-btn">📅 Ganti Periode (Mingguan / Bulanan / Custom)</div>
        <div class="kb-btn" style="color: #9CA3AF;">🔗 Tautan Langsung Spreadsheet</div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""
}

out_dir = "/home/bahy/aibrain/mutabaah-bot/presentation_assets/screenshots"
os.makedirs(out_dir, exist_ok=True)

for name, html_content in TEMPLATES.items():
    html_path = f"/tmp/{name}.html"
    png_path = os.path.join(out_dir, f"{name}.png")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    cmd = [
        "google-chrome",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=480,820",
        f"--screenshot={png_path}",
        html_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Generated screenshot: {png_path}")

print("All screenshots generated successfully.")
