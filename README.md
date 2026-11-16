# 🕌 Mutabaah Yaumiyah Telegram Bot (IMA Korea)

Bot Telegram untuk pencatatan dan pelacakan amalan harian (*Mutabaah Amalan Yaumiyah*) anggota **IMA Korea (Indonesian Muslim Association in Korea)**.

Bot ini menyederhanakan proses mutabaah: anggota tidak perlu lagi membuka atau mengedit spreadsheet secara manual di HP mereka. Cukup isi secara interaktif melalui tombol Telegram, dan seluruh data otomatis tersinkronisasi ke Google Sheet terpusat secara realtime.

---

## 📌 Fitur Utama

- **Pendaftaran Anggota Mandiri**: Anggota baru otomatis diminta mendaftarkan nama lengkap saat pertama kali menekan `/start`.
- **Fleksibilitas Pengisian Amalan (Per Amalan atau Berurutan)**:
  - **Opsi Isi Satu Amalan**: User dapat memilih untuk mengisi atau memperbarui hanya satu amalan saja tanpa harus menjawab semua pertanyaan.
  - **Opsi Isi Semua Berurutan**: Panduan langkah demi langkah cepat dan terstruktur untuk semua amalan yang dipilih.
  - Ringkasan konfirmasi sebelum data disimpan ke Google Sheets.
- **Kustomisasi Amalan yang Dimutabaah (`/amalan`)**:
  - Anggota bebas memilih amalan apa saja yang ingin dimutabaah melalui checklist interaktif (misal: menonaktifkan Qiyamulail atau amalan lain jika tidak diwajibkan).
  - Amalan yang tidak dipilih tidak akan ditanyakan dan tidak mengurangi persentase capaian target.
- **Kustomisasi Target Angka Harian & Bulanan (`/target`)**:
  - Setiap pengguna dapat menyesuaikan target angka mereka sendiri; target default sistem berfungsi sebagai nilai awal.
- **Dukungan 13 Amalan Yaumiyah Lengkap**:
  1. 📖 Tilawah Al-Qur'an (default: 20 halaman/hari)
  2. 🕌 Sholat Wajib (default: 5 waktu/hari)
  3. 🌙 Sholat Sunnah Rawatib (default: 12 rakaat/hari)
  4. 📿 Al-Ma’tsurat (default: 2 kali/hari)
  5. 🌸 Shalawat (default: 100 kali/hari)
  6. 🤲 Istighfar (default: 100 kali/hari)
  7. 📜 Tadabbur Al-Qur'an (default: 1 ayat/hari)
  8. 🍽️ Shaum Sunnah (default: min. 4 hari/bulan)
  9. 🌃 Qiyamulail (default: 12 hari/bulan)
  10. ☀️ Sholat Dhuha (default: 12 hari/bulan)
  11. 🏃 Olahraga (default: 30 menit/pekan)
  12. 🤝 Silaturahim (default: min. 4 hari/bulan)
  13. 🤲 Doa untuk Kebaikan Ummat Islam (default: 1 kali/hari)
- **Opsi Cepat "Berhalangan" (Haid)**:
  - Tersedia tombol cepat `🌸 Berhalangan` pada pengisian **Tilawah Al-Qur'an** dan **Sholat Wajib**.
  - Mengakomodasi akhwat yang sedang haid/berhalangan syar'i.
  - **Pengecualian Performa Otomatis**: Hari-hari yang ditandai *Berhalangan* otomatis dikecualikan dari pembagi/target performa pribadi (`/progress`) maupun rata-rata agregat admin (`/stats`), sehingga tidak menurunkan persentase capaian target secara tidak adil.
- **Pembaruan Data Cerdas (Upsert & Preservasi Data)**:
  - 1 baris per pengguna per hari (menggunakan timezone Korea `Asia/Seoul`).
  - Pembaruan sebagian (*partial update*) menjaga data amalan lain yang sudah diisi sebelumnya pada hari tersebut.
- **Pantau Progres Bulanan Personal (`/progress`)**:
  - Menghitung persentase ketercapaian secara adil hanya berdasarkan amalan yang diaktifkan oleh pengguna.
- **Pengingat Harian Otomatis (*Daily Reminder*)**:
  - Dikirim setiap pukul 21:00 KST (`Asia/Seoul`) kepada anggota terdaftar yang belum mengisi mutabaah hari ini.
- **Edit Nama Terdaftar (`/editnama` / `/nama`)**:
  - Memungkinkan anggota mengoreksi nama lengkap kapan saja langsung dari Telegram atau menu pengaturan tanpa mengulang pendaftaran.
- **Panel Admin Khusus (`/admin`, `/stats`, `/export`)**:
  - Khusus pengurus terdaftar di `ADMIN_TELEGRAM_IDS`.


---

## 📊 Struktur Data Google Sheets

Bot menggunakan satu Google Spreadsheet terpusat dengan 3 *worksheet*:

### 1. Worksheet: `Members`
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `Telegram User ID` | Integer/Text | ID unik Telegram (primary identifier) |
| `Telegram Username` | Text | Username Telegram (misal: `@bahyhelmihp`) |
| `Full Name` | Text | Nama lengkap anggota |
| `Registration Date` | Date (YYYY-MM-DD) | Tanggal pendaftaran (Waktu Seoul) |
| `Active` | Boolean (TRUE/FALSE) | Status keaktifan anggota |

### 2. Worksheet: `Daily Mutabaah`
| Kolom | Tipe | Target Default | Contoh Nilai |
| :--- | :--- | :--- | :--- |
| `Date` | Date (YYYY-MM-DD) | - | `2026-10-14` |
| `Telegram User ID` | Integer/Text | - | `123456789` |
| `Telegram Username` | Text | - | `@bahyhelmihp` |
| `Full Name` | Text | - | `Bahy Helmi` |
| `Tilawah Pages` | Integer | 20 halaman | `20` |
| `Sholat Wajib` | Integer | 5 waktu | `5` |
| `Rawatib Rakaat` | Integer | 12 rakaat | `8` |
| `Almatsurat` | Integer | 2 kali | `2` |
| `Shalawat` | Integer | 100 kali | `100` |
| `Istighfar` | Integer | 100 kali | `100` |
| `Tadabbur Ayat` | Integer | 1 ayat | `2` |
| `Shaum Sunnah` | Boolean (TRUE/FALSE) | Min. 4x / bulan | `TRUE` |
| `Qiyamulail` | Boolean (TRUE/FALSE) | 3x / pekan | `TRUE` |
| `Dhuha` | Boolean (TRUE/FALSE) | 3x / pekan | `TRUE` |
| `Olahraga` | Integer | 30 menit / pekan | `30` |
| `Silaturahim` | Boolean (TRUE/FALSE) | Min. 4x / bulan | `TRUE` |
| `Doa Ummat Islam` | Integer | 1 kali / hari | `2` |
| `Submission Time` | Datetime | - | `2026-10-14 21:30:00` |
| `Last Updated` | Datetime | - | `2026-10-14 21:30:00` |

### 3. Worksheet: `User Settings`
Menyimpan pilihan amalan aktif dan target khusus per user:
| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `Telegram User ID` | Integer/Text | ID unik anggota |
| `Active Amalan` | Text | Daftar amalan aktif dipisahkan koma |
| `Target Tilawah` ... `Target Doa Ummat` | Integer | Nilai target kustom user |
| `Last Updated` | Datetime | Waktu pembaruan pengaturan |

---

## ⚙️ Persiapan & Setup

### 1. Buat Bot Telegram via BotFather
1. Buka Telegram dan cari [@BotFather](https://t.me/BotFather).
2. Kirim perintah `/newbot` dan ikuti petunjuk nama bot.
3. Simpan **HTTP API Token** yang diberikan.
4. (Opsional) Daftarkan menu perintah di BotFather melalui `/setcommands`:
   ```text
   start - Buka menu utama mutabaah
   isi - Isi mutabaah hari ini (per amalan atau berurutan)
   edit - Ubah isian mutabaah hari ini
   progress - Lihat rekap progress bulan ini
   amalan - Pilih amalan yang ingin dimutabaah
   target - Atur target harian & bulanan pribadi
   settings - Pengaturan amalan & target
   editnama - Ubah nama lengkap terdaftar
   help - Panduan amalan & penggunaan bot
   cancel - Batalkan proses yang sedang aktif
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
