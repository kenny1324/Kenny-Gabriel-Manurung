# ⚔️ Sword Defender — Game Pertahanan Pedang Interaktif (PCV)

Game pertahanan interaktif berbasis **Pengolahan Citra dan Video (PCV)** yang dimainkan secara langsung menggunakan gerakan tangan di depan webcam.

Pemain memegang kendali atas sebilah pedang pertahanan di layar. Dengan menggerakkan tangan secara bebas, pemain harus menangkis rentetan meteor dan bola api yang berjatuhan dari langit sebelum menyentuh dasar benteng pertahanan.

---

## 📸 Demo & Dokumentasi Visual

### 🎮 Screenshot Gameplay
<!-- SLOT GAMBAR SCREENSHOT: Ganti path atau tautan gambar di bawah ini dengan file screenshot running game Anda -->
![Screenshot Gameplay Sword Defender](docs/screenshot.png)
> *Slot Screenshot: Letakkan file tangkapan layar game pada folder `docs/screenshot.png` atau ganti URL di atas.*

---

### 🎥 Video Dokumentasi Gameplay
<!-- SLOT VIDEO DOKUMENTASI: Anda bisa menggunakan tag video lokal atau tautan YouTube di bawah -->
<div align="center">

[![Video Dokumentasi Sword Defender](https://img.shields.io/badge/▶_Tonton_Video_Dokumentasi-YouTube-red?style=for-the-badge&logo=youtube)](https://www.youtube.com)

*(Klik tombol di atas untuk menonton video dokumentasi permainan, atau sematkan file video langsung di folder `docs/gameplay.mp4`)*

</div>

---

## 🕹️ Bagaimana Game Ini Bekerja?

Game ini memadukan interaksi kamera dengan permainan arkade klasik melalui alur pemrosesan visual berikut:

```
[ Kamera Webcam ] ──> [ Deteksi Warna Kulit ] ──> [ Titik Tengah Tangan ] ──> [ Posisi Pedang di Layar ]
                                                                                      │
                                                                                      ▼
[ Skor & HP Pemain ] <── [ Sistem Tabrakan / Tangkisan ] <── [ Meteor & Api Berjatuhan ]
```

### 1. Bagaimana Kamera Menggerakkan Pedang?
1. **Melihat Melalui Kamera**: Saat aplikasi dibuka, kamera webcam menangkap gerakan Anda secara realtime dan langsung membalik tampilannya (*mirror*), sehingga ketika Anda menggerakkan tangan ke kanan, pedang di layar juga bergerak ke kanan selayaknya bercermin.
2. **Mengenali Warna Tangan**: Sistem membedakan area kulit tangan pemain dari latar belakang ruangan dengan memindai corak warna (*Hue*) kulit manusia.
3. **Penyaringan Bentuk**: Titik-titik cahaya yang mengganggu dibersihkan dan rongga di telapak tangan dipadatkan, menghasilkan siluet tangan yang jelas dan utuh.
4. **Menentukan Posisi Pedang**: Sistem melacak titik pusat (*centroid*) dari area tangan terbesar yang terdeteksi, kemudian menerjemahkan posisi tersebut menjadi koordinat gerakan pedang di layar secara halus (*smooth*).

### 2. Bagaimana Objek Muncul di Layar?
- **Objek Jatuh**: Meteor batu dan bola api muncul dari koordinat horizontal acak di bagian atas layar dan bergerak meluncur ke bawah menuju garis benteng pertahanan pemain.
- **Kemunculan Teratur**: Interval kemunculan objek diatur berdasarkan waktu nyata, memastikan ritme kemunculan stabil dan menantang sesuai tingkat kesulitan yang dipilih.

---

## 🎯 Aturan Permainan & Mekanisme Skor

Tujuan utama pemain adalah mempertahankan benteng dari kehancuran selama mungkin dan meraih skor tertinggi.

### 🛡️ Sistem HP (Health Points)
- Pemain memiliki **6 HP** di awal permainan.
- HP ditampilkan dalam bentuk bilah indikator hijau/merah di bagian atas layar (HUD).
- Jika HP habis mencapai **0**, benteng runtuh dan permainan dinyatakan **GAME OVER**.

### ⚔️ Mekanisme Tangkisan & Poin
Pemain cukup mengarahkan bilah pedang agar bertabrakan dengan objek yang sedang jatuh:

| Objek | Tampilan | Efek Saat Ditangkis Pedang | Efek Jika Lolos ke Dasar |
| :---: | :---: | :---: | :---: |
| **Meteor** | Batu Angkasa Berkawah | **Skor +1** (Hancur, HP Aman) | **HP -1** (Benteng Rusak) |
| **Api** | Bola Api Membara | **Skor +2** (Hancur, HP Aman) | **HP -2** (Kerusakan Parah) |

> **Catatan Tabrakan**: 
> - Setiap objek hanya memicu satu kali aksi (tidak ada kerusakan ganda).
> - Jika tangan pemain keluar dari pandangan kamera, pedang akan menjadi transparan/non-aktif sementara waktu untuk mencegah penangkisan pasif secara tidak sengaja.

---

## 🎚️ Tingkat Kesulitan (Difficulty Modes)

Tingkat kesulitan dapat dipilih secara langsung melalui Menu Utama sebelum memulai permainan:

- **EASY (Santai)**: Interval kemunculan objek lebih renggang (~1,5 detik) dengan laju jatuh perlahan. Sangat cocok untuk membiasakan diri dengan kontrol kamera.
- **MEDIUM (Standar)**: Interval objek lebih cepat (~1,0 detik) dengan pergerakan objek sedang dan kemunculan api yang lebih sering.
- **HARD (Menantang)**: Interval sangat rapat (~0,6 detik) dengan kecepatan jatuh tinggi. Menuntut kecepatan refleks dan koordinasi tangan yang gesit.

---

## 🧭 Menu & Navigasi Permainan

1. **PLAY**: Memulai sesi permainan baru menggunakan tingkat kesulitan yang sedang aktif. Skor dan HP akan di-reset kembali ke awal.
2. **DEMONSTRATION (PCV)**: Membuka layar pengujian kamera realtime untuk melihat bagaimana sistem membaca tangan Anda melalui 5 tahapan pemrosesan visual (Kamera Asli, Masking Warna Kulit, Pembersihan Noise, Pemadatan Objek, dan Titik Pusat Tangan).
3. **MODE (EASY / MEDIUM / HARD)**: Tombol pemilih mode kesulitan dengan penanda visual aktif.
4. **EXIT**: Menutup aplikasi dan melepaskan webcam secara aman.
5. **GAME OVER SCREEN**:
   - Menampilkan total skor akhir yang berhasil dikumpulkan.
   - **PLAY AGAIN**: Mengulang permainan seketika dengan mode yang sama.
   - **MAIN MENU**: Kembali ke menu utama untuk mengganti tingkat kesulitan.

---

## 🎮 Kontrol Permainan

- **Gerakan Tangan (Webcam)**: Kendalikan posisi pedang ke kiri, kanan, atas, dan bawah untuk menangkis objek.
- **Klik Mouse**: Memilih menu, mengganti mode kesulitan, dan menekan tombol pada antarmuka layar.
- **Tombol Keyboard `ESC`**: Kembali ke Menu Utama dari mode permainan atau halaman demonstrasi.

---

## 📁 Struktur Direktori Project

```text
SwordDefender/
├── main.py              # Titik masuk utama program dan siklus tampilan game
├── README.md            # Dokumentasi lengkap mekanisme dan panduan game
├── assets/              # Aset visual (sprite, latar belakang) dan audio (musik, efek suara)
│   ├── pedang.png
│   ├── meteor.png
│   ├── api.png
│   ├── backgroundmenu.png
│   ├── backgroundmain.png
│   ├── backgroundskor.png
│   ├── music_result.mp3
│   ├── sound_meteor_hit.mp3
│   └── sound_fire_hit.mp3
└── src/                 # Modul pemrosesan logika game dan pengolahan citra
    ├── __init__.py
    ├── pcv.py           # Pemrosesan kamera dan pelacakan tangan
    ├── game.py          # Logika entitas jatuh, pedang, skor, dan benturan
    └── assets.py        # Pengelola pemuatan gambar dan efek suara
```

---

## 🚀 Cara Menjalankan Game

1. Pastikan komputer terhubung dengan webcam aktif dan memiliki Python (versi 3.9 ke atas).
2. Install library yang dibutuhkan:
   ```bash
   pip install opencv-python numpy pygame
   ```
3. Jalankan game:
   ```bash
   python main.py
   ```
4. Pastikan pencahayaan ruangan Anda cukup terang agar kamera dapat mendeteksi gerakan tangan dengan optimal. Selamat bermain!
