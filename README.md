# 🕌 Mutabaah Yaumiyah Telegram Bot (IMA Korea)

Bot Telegram untuk pencatatan dan pelacakan amalan harian (*Mutabaah Amalan Yaumiyah*) anggota **IMA Korea (Indonesian Muslim Association in Korea)**.

Bot ini menyederhanakan proses mutabaah: anggota tidak perlu lagi membuka atau mengedit spreadsheet secara manual di HP mereka. Cukup isi secara interaktif melalui tombol Telegram, dan seluruh data otomatis tersinkronisasi ke Google Sheet terpusat secara realtime.

---

## 📌 Fitur Utama

- **Pendaftaran Anggota Mandiri**: Anggota baru otomatis diminta mendaftarkan nama lengkap saat pertama kali menekan `/start`.
- **Alur Pengisian Cepat (Kurang dari 1 Menit)**:
  - Dipandu langkah demi langkah dengan *inline keyboard*.
  - Tombol angka cepat & fleksibel (tetap mendukung input teks manual jika diinginkan).
  - Navigasi **⬅️ Kembali** di setiap langkah dan **❌ Batal** kapan saja.
  - Ringkasan konfirmasi sebelum data disimpan ke Google Sheets.
- **Pembaruan Data Cerdas (Upsert)**:
  - 1 baris per pengguna per hari (menggunakan timezone Korea `Asia/Seoul`).
  - Jika anggota mengisi ulang atau mengedit hari ini (`/edit`), bot memperbarui baris hari ini dan mencatat waktu pembaruan (*Last Updated*) tanpa membuat baris duplikat.
- **Pantau Progres Bulanan (`/progress`)**:
  - Rekap jumlah hari terisi pada bulan berjalan.
  - Perbandingan capaian tilawah, sholat wajib, rawatib, al-ma'tsurat terhadap target harian.
  - Rekap amalan yaumiyah (Qiyamulail, Dhuha, Olahraga).
  - Kalkulasi persentase ketercapaian target mutabaah.
- **Pengingat Harian Otomatis (*Daily Reminder*)**:
  - Dikirim setiap pukul 21:00 KST (`Asia/Seoul`).
  - **Hanya dikirim kepada anggota terdaftar yang belum mengisi mutabaah hari ini**.
  - Dilengkapi tombol langsung `[📝 Isi Sekarang]`.
- **Panel Admin Khusus (`/admin`, `/stats`, `/export`)**:
  - Hanya dapat diakses oleh user ID yang didaftarkan di `ADMIN_TELEGRAM_IDS`.
  - Rekap agregat bulanan: total anggota, jumlah submit hari ini, persentase keaktifan hari ini, rata-rata ketercapaian amalan.
  - Tautan langsung ke Google Sheets tanpa mengekspos privasi data ke anggota umum.

---

## 🏗️ Arsitektur Proyek

```text
mutabaah-bot/
├── app/
│   ├── __init__.py
│   ├── bot.py               # Inisialisasi bot, scheduler pengingat, polling/webhook runner
│   ├── config.py            # Konfigurasi & validasi environment variables
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py         # Registrasi anggota, sapaan /start, /help, /cancel
│   │   ├── mutabaah.py      # ConversationHandler mutabaah (/isi, /edit, konfirmasi simpan)
│   │   ├── progress.py      # Laporan capaian mutabaah pribadi (/progress)
│   │   └── admin.py         # Panel admin (/admin, /stats, /export)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sheets.py        # Klien Google Sheets (gspread), auto-create sheet, upsert row
│   │   ├── members.py       # Manajemen data anggota & verifikasi status aktif
│   │   └── statistics.py    # Logika kalkulasi progres personal & statistik agregat admin
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── common.py        # Builder inline keyboard & navigasi tombol Telegram
│   └── utils/
│       ├── __init__.py
│       └── datetime.py      # Konversi timezone Asia/Seoul & format penanggalan Indonesia
├── tests/
│   ├── test_bot.py          # Unit tests keyboard, kalkulasi statistik, & timezone
│   └── test_sheets.py       # Unit tests upsert & update logic Google Sheets
├── .env.example             # Template variabel lingkungan
├── .gitignore
├── requirements.txt         # Dependensi Python
└── README.md
```

---

## 📊 Struktur Data Google Sheets

Bot menggunakan satu Google Spreadsheet terpusat dengan 2 *worksheet*. Jika lembar kerja belum ada, bot akan otomatis membuatnya beserta baris judul kolom:

### 1. Worksheet: `Members`
Menyimpan daftar anggota yang terdaftar di bot:
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `Telegram User ID` | Integer/Text | ID unik Telegram (primary identifier) |
| `Telegram Username` | Text | Username Telegram (misal: `@bahyhelmihp`) |
| `Full Name` | Text | Nama lengkap anggota |
| `Registration Date` | Date (YYYY-MM-DD) | Tanggal pendaftaran (Waktu Seoul) |
| `Active` | Boolean (TRUE/FALSE) | Status keaktifan anggota |

### 2. Worksheet: `Daily Mutabaah`
Menyimpan 1 baris per pengguna per tanggal:
| Kolom | Tipe | Target Harian | Contoh Nilai |
| :--- | :--- | :--- | :--- |
| `Date` | Date (YYYY-MM-DD) | - | `2026-10-13` |
| `Telegram User ID` | Integer/Text | - | `123456789` |
| `Telegram Username` | Text | - | `@bahyhelmihp` |
| `Full Name` | Text | - | `Bahy Helmi` |
| `Tilawah Pages` | Integer (0-100) | 20 halaman | `20` |
| `Sholat Wajib` | Integer (0-5) | 5 waktu | `5` |
| `Rawatib Rakaat` | Integer (0-12) | 12 rakaat | `8` |
| `Almatsurat` | Integer (0-2) | 2 kali | `2` |
| `Qiyamulail` | Boolean (TRUE/FALSE) | 3x / pekan | `TRUE` |
| `Dhuha` | Boolean (TRUE/FALSE) | 3x / pekan | `TRUE` |
| `Olahraga` | Boolean (TRUE/FALSE) | Min. 5 menit | `TRUE` |
| `Submission Time` | Datetime | - | `2026-10-13 21:30:00` |
| `Last Updated` | Datetime | - | `2026-10-13 21:30:00` |

---

## ⚙️ Persiapan & Setup

### 1. Buat Bot Telegram via BotFather
1. Buka Telegram dan cari [@BotFather](https://t.me/BotFather).
2. Kirim perintah `/newbot` dan ikuti petunjuk nama bot (misal: `Mutabaah IMA Korea Bot`).
3. Simpan **HTTP API Token** yang diberikan (misal: `7123456789:ABCdef...`).
4. (Opsional) Daftarkan menu perintah di BotFather melalui `/setcommands`:
   ```text
   start - Buka menu utama mutabaah
   isi - Isi mutabaah hari ini
   edit - Ubah isian mutabaah hari ini
   progress - Lihat rekap progress bulan ini
   help - Panduan amalan & penggunaan bot
   cancel - Batalkan pengisian yang sedang aktif
   admin - Panel admin (khusus pengurus)
   stats - Statistik agregat (khusus pengurus)
   export - Tautan spreadsheet (khusus pengurus)
   ```

---

### 2. Setup Google Cloud & Google Sheets API
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buat Project baru (misal: `ima-korea-mutabaah`).
3. Buka menu **APIs & Services > Library**, cari dan **Enable** dua API berikut:
   - **Google Sheets API**
   - **Google Drive API**
4. Buka menu **APIs & Services > Credentials**:
   - Klik **Create Credentials** > pilih **Service Account**.
   - Beri nama Service Account (misal: `mutabaah-bot-sa`).
   - Selesaikan pembuatan tanpa perlu assign role khusus.
5. Klik Service Account yang baru dibuat > tab **Keys** > **Add Key** > **Create new key** > pilih format **JSON**.
6. Simpan file JSON yang terunduh (misal simpan sebagai `credentials.json` di folder proyek ini).
7. **PENTING**:
   - Buat spreadsheet baru di Google Sheets.
   - Salin email Service Account (contoh: `mutabaah-bot-sa@ima-korea-mutabaah.iam.gserviceaccount.com`).
   - Klik tombol **Share (Bagikan)** di pojok kanan atas spreadsheet Google Sheets Anda, lalu bagikan ke email Service Account tersebut dengan hak akses **Editor**.
   - Salin **Spreadsheet ID** dari URL browser:
     ```text
     https://docs.google.com/spreadsheets/d/<GOOGLE_SHEET_ID_ADA_DI_SINI>/edit
     ```

---

### 3. Konfigurasi Variabel Lingkungan (`.env`)
Salin file `.env.example` ke `.env`:
```bash
cp .env.example .env
```

Isi variabel di file `.env`:
```env
# Token Bot Telegram dari BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# ID Google Spreadsheet
GOOGLE_SHEET_ID=1a2B3c4D5e6F7g8H9i0J_spreadsheet_id_anda

# Kredensial Service Account:
# Mode Lokal: isi dengan path file JSON
GOOGLE_SERVICE_ACCOUNT_JSON=./credentials.json

# ID Telegram Admin (pisahkan dengan koma untuk beberapa admin)
ADMIN_TELEGRAM_IDS=123456789,987654321

# Timezone & Jadwal Pengingat (Asia/Seoul untuk Korea)
TIMEZONE=Asia/Seoul
REMINDER_HOUR=21
REMINDER_MINUTE=0
```

> **Catatan Kredensial di Cloud (Render / Railway / VPS):**
> Anda tidak perlu mengunggah file `credentials.json`. Cukup buka file JSON tersebut, salin seluruh isinya (mulai dari `{` sampai `}`), dan masukkan langsung sebagai nilai `GOOGLE_SERVICE_ACCOUNT_JSON` di Environment Variables dashboard hosting Anda.

---

### 4. Mengetahui ID Telegram Anda (Untuk Admin)
Untuk mengisi `ADMIN_TELEGRAM_IDS`:
1. Buka Telegram dan cari [@userinfobot](https://t.me/userinfobot) atau [@myidbot](https://t.me/myidbot).
2. Tekan `/start`. Bot akan menampilkan ID angka Anda (misal: `123456789`).
3. Masukkan ID tersebut ke dalam `ADMIN_TELEGRAM_IDS` di file `.env`.

---

## 🚀 Menjalankan Secara Lokal

### Menggunakan Virtual Environment (Python 3.10+)

```bash
# 1. Masuk ke direktori proyek
cd /Users/bahy/mutabaah-bot

# 2. Buat & aktifkan virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependensi
pip install -r requirements.txt

# 4. Jalankan unit test untuk memastikan semua fungsi normal
python -m unittest discover tests

# 5. Jalankan bot
python -m app.bot
```

Bot akan berjalan dalam mode **Long Polling** dan siap menerima pesan di Telegram.

---

## ☁️ Panduan Deploy ke Render.com

Deploy bot ke [Render](https://render.com) sangat mudah dan hemat biaya:

### Opsi A: Background Worker (Recommended untuk Polling)
1. Push kode bot ke GitHub / GitLab Anda (pastikan file `.env` dan `credentials.json` tidak ikut ter-push, sudah tercantum di `.gitignore`).
2. Login ke [Render Dashboard](https://dashboard.render.com).
3. Klik **New +** > pilih **Background Worker**.
4. Hubungkan repository GitHub Anda.
5. Konfigurasi service:
   - **Name**: `mutabaah-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m app.bot`
6. Buka bagian **Environment Variables** di Render, lalu tambahkan:
   - `TELEGRAM_BOT_TOKEN`
   - `GOOGLE_SHEET_ID`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` (Paste seluruh teks JSON mentah dari Service Account)
   - `ADMIN_TELEGRAM_IDS`
   - `TIMEZONE`: `Asia/Seoul`
   - `REMINDER_HOUR`: `21`
   - `REMINDER_MINUTE`: `0`
7. Klik **Create Background Worker**.

### Opsi B: Web Service dengan Webhook
Jika Anda ingin menggunakan Webhook gratis di Render:
1. Buat **Web Service** di Render.
2. Build Command: `pip install -r requirements.txt`
3. Start Command: `python -m app.bot`
4. Tambahkan variabel lingkungan tambahan:
   - `WEBHOOK_URL`: `https://nama-service-anda.onrender.com`
   - `PORT`: `8080`
Bot otomatis beralih ke mode Webhook saat `WEBHOOK_URL` terdeteksi!

---

## 🧪 Menjalankan Pengujian Otomatis (Unit Tests)

Proyek ini telah dilengkapi serangkaian pengujian unit untuk memastikan logika perhitungan target, timezone Korea, validasi tombol, dan logika Google Sheets upsert berjalan sempurna:

```bash
source venv/bin/activate
python -m unittest discover tests
```

Output:
```text
.......
----------------------------------------------------------------------
Ran 7 tests in 0.084s

OK
```

---

## 🤝 Kontribusi & Pengembangan Lanjutan

Rencana peningkatan pasca-MVP:
- Fitur whitelist / verifikasi persetujuan admin sebelum anggota baru aktif.
- Visualisasi grafik progress mingguan menggunakan grafik gambar interaktif.
- Pengaturan waktu pengingat personal sesuai preferensi masing-masing anggota.
