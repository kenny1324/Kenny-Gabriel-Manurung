# Sword Defender — Game Pertahanan Pedang Berbasis PCV

Game interaktif berbasis **Pengolahan Citra dan Video (PCV)** yang dikembangkan menggunakan **Python**, **OpenCV**, **NumPy**, dan **Pygame**.

Pemain menggerakkan tangan di depan webcam secara realtime. Sistem mendeteksi warna kulit tangan menggunakan metode pemrosesan citra digital klasik (**tanpa AI/MediaPipe/YOLO**), menghitung koordinat pusat tangan (*centroid*), lalu menggerakkan sprite pedang di layar untuk menangkis meteor dan bola api yang jatuh dari atas.

---

## 1. Fitur Utama

- **Realtime Hand Tracking Murni PCV**: Deteksi tangan menggunakan segmentasi warna kulit pada ruang warna HSV dan pencarian komponen terhubung (Connected Component Analysis).
- **Morfologi Manual Berbasis NumPy**: Operasi Erosi dan Dilasi 3×3 diimplementasikan murni dengan operasi matriks dan slicing NumPy tanpa menyembunyikan proses matematisnya.
- **Halaman Demonstrasi PCV Realtime**: Menampilkan 5 tahapan pemrosesan citra kamera secara langsung:
  1. Kamera Asli (RGB Mirrored / Flipped Horizontal)
  2. Thresholding HSV Kulit (Mask Biner Dual-Range)
  3. Morfologi Opening (Erosi → Dilasi)
  4. Morfologi Closing (Dilasi → Erosi)
  5. Connected Component (DFS 4-Arah) & Pusat Tangan (*Centroid*)
  - Disertai panel telemetri data teknis: koordinat piksel, luas komponen, status deteksi, ambang HSV, dan FPS realtime.
- **Tiga Tingkat Kesulitan**: Pilihan mode **EASY**, **MEDIUM**, dan **HARD** yang dapat langsung dipilih pada Menu Utama.
- **Sistem Pertahanan & Collision**: Tangkisan responsif berbasis tabrakan (*bounding box collision*), skor akurat, penanganan kehilangan tangan (*hand lost timeout*), dan visual bar HP.
- **Audio Berkelanjutan**: Musik latar `music_result.mp3` berjalan tanpa henti dari menu hingga game over, serta efek suara benturan terpisah untuk meteor dan api.
- **Pemuatan Aset Langsung & Ter-cache**: Memuat aset asli secara efisien dengan caching Pygame.

---

## 2. Metode Pengolahan Citra dan Video (PCV)

Sistem PCV pada Sword Defender bekerja melalui alur berikut:

```
Webcam Frame (BGR) 
       │
       ▼
Horizontal Flip (Mirroring)
       │
       ▼
Konversi Warna BGR ke HSV
       │
       ▼
Thresholding Rentang Ganda (Skin Mask)
       │
       ▼
Morfologi Opening (Erosi 3x3 → Dilasi 3x3)
       │
       ▼
Morfologi Closing (Dilasi 3x3 → Erosi 3x3)
       │
       ▼
Connected Component DFS 4-Arah
       │
       ▼
Perhitungan Centroid (Pusat Tangan)
       │
       ▼
Smoothing & Pemetaan ke Layar Game (Posisi Pedang)
```

### A. Pengambilan Frame Webcam & Mirroring
- Kamera diakses menggunakan OpenCV VideoCapture.
- Frame kamera dibalik secara horizontal menggunakan `cv2.flip(frame, 1)` sehingga pergerakan pemain terasa alami seperti bercermin.

### B. Konversi BGR ke HSV
- Kamera OpenCV secara bawaan menghasilkan format piksel **BGR** (*Blue, Green, Red*).
- Frame dikonversikan ke ruang warna **HSV** (*Hue, Saturation, Value*) menggunakan `cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)`.
- **Alasan Pemilihan HSV**: Ruang warna HSV memisahkan nilai corak warna murni (*Hue*) dari intensitas cahaya atau kecerahan (*Value*). Hal ini membuat deteksi warna kulit jauh lebih stabil terhadap bayangan dan perbedaan intensitas cahaya dibandingkan jika menggunakan ruang warna BGR/RGB secara langsung.

### C. Thresholding Warna Kulit (Dual-Range Hue)
- Warna kulit manusia didominasi oleh spektrum merah. Pada lingkaran *Hue* OpenCV (nilai 0 hingga 179), warna merah terbagi di dua kutub: rentang nilai rendah (0–20) dan rentang nilai tinggi (160–180).
- Oleh karena itu, diterapkan dua rentang ambang batas:
  - **Rentang 1**: Lower `[0, 30, 60]`, Upper `[20, 255, 255]`
  - **Rentang 2**: Lower `[160, 30, 60]`, Upper `[180, 255, 255]`
- Kedua mask digabungkan menggunakan operasi logika OR (`cv2.bitwise_or`), menghasilkan mask biner dengan nilai 255 (putih) untuk area kulit dan 0 (hitam) untuk latar belakang.

### D. Operasi Morfologi Manual dengan NumPy
Operasi morfologi diimplementasikan murni dengan operasi matriks NumPy (kernel persegi 3×3 dengan *zero-padding*):
1. **Erosi (Erosion)**:
   - Suatu piksel bernilai foreground (255) jika dan hanya jika **seluruh 9 tetangga** dalam kernel 3×3 juga bernilai foreground.
   - Fungsi: Mengikis batas luar objek putih dan melenyapkan bintik-bintik *noise* kecil di latar belakang.
2. **Dilasi (Dilation)**:
   - Suatu piksel bernilai foreground (255) jika **minimal satu tetangga** dalam kernel 3×3 bernilai foreground.
   - Fungsi: Memperbesar area objek, menutup lubang kecil pada objek, dan menyambungkan bagian yang terputus.

### E. Opening dan Closing
- **Opening** (`Dilation(Erosion(Mask))`): Menghilangkan tonjolan-tonjolan tipis dan bintik *noise* terisolasi tanpa mengurangi ukuran umum tangan.
- **Closing** (`Erosion(Dilation(Mask))`): Menutup celah kecil dan rongga internal (*holes*) di dalam area telapak tangan sehingga bentuk tangan menjadi padat (*solid*).

### F. Connected Component Menggunakan DFS (Depth-First Search)
- Mask hasil morfologi ditelusuri menggunakan algoritma **DFS 4-Arah** (*up, down, left, right*) berbasis *stack* eksplisit (menghindari batas rekursi Python).
- Setiap komponen dihitung:
  - **Luas (Area)**: Jumlah piksel foreground yang terhubung.
  - **Centroid**: Titik pusat massa:
    $$\bar{x} = \frac{\sum x}{A}, \quad \bar{y} = \frac{\sum y}{A}$$
- Komponen difilter berdasarkan batas luas minimum (`MIN_AREA=35`) dan maksimum (`MAX_AREA=8000`) untuk menolak debu/noise kecil maupun dinding latar belakang yang terlalu luas. Komponen terbesar yang valid dipilih sebagai tangan pemain.

### G. Pelacakan Tangan & Smoothing
- Titik pusat tangan dipetakan dari resolusi pemrosesan ke koordinat layar permainan ($800 \times 600$).
- Diterapkan peredam getaran (*Exponential Moving Average smoothing*):
  $$P_{\text{baru}} = \alpha \cdot P_{\text{target}} + (1 - \alpha) \cdot P_{\text{lama}}$$
- Jika tangan tidak terdeteksi sementara, pedang mempertahankan posisi terakhirnya. Jika tangan hilang melebihi batas waktu (0,6 detik), tabrakan pedang dinonaktifkan agar tidak terjadi tangkisan pasif.

---

## 3. Struktur Direktori Project

```text
SwordDefender/
├── .gitignore           # File pengabaian git (cache, virtual env, dll)
├── main.py              # Entry point utama, state machine (Menu, Game, Demo, GameOver)
├── requirements.txt     # Daftar dependensi library Python
├── README.md            # Dokumentasi lengkap proyek
├── assets/              # Folder aset gambar dan audio
│   ├── pedang.png
│   ├── meteor.png
│   ├── api.png
│   ├── backgroundmenu.png
│   ├── backgroundmain.png
│   ├── backgroundskor.png
│   ├── music_result.mp3
│   ├── sound_meteor_hit.mp3
│   └── sound_fire_hit.mp3
└── src/
    ├── __init__.py      # Package initializer
    ├── pcv.py           # Pipeline PCV, webcam, HSV, morfologi manual, DFS, tracking
    ├── game.py          # Logika gameplay, entitas meteor/api/pedang, collision, HUD
    └── assets.py        # Pengelola pemuatan aset gambar dan audio dengan caching
```

---

## 4. Instalasi dan Cara Menjalankan

### A. Prasyarat
- Python 3.9+ (direkomendasikan Python 3.12).
- Webcam yang terhubung ke komputer.

### B. Instalasi Dependensi
Buka terminal / PowerShell di direktori `SwordDefender`, lalu jalankan:

```bash
pip install -r requirements.txt
```

Isi dependensi di `requirements.txt`:
- `opencv-python>=4.8.0`
- `numpy>=1.24.0`
- `pygame>=2.5.0`

### C. Menjalankan Game
Jalankan perintah:

```bash
python main.py
```

---

## 5. Kontrol Permainan

- **Webcam (Tangan Pemain)**: Gerakkan telapak tangan di depan kamera untuk mengarahkan pedang ke posisi meteor atau api yang jatuh.
- **Mouse**: Klik kiri pada tombol antarmuka (PLAY, DEMONSTRATION, EASY/MEDIUM/HARD, EXIT, PLAY AGAIN, MAIN MENU).
- **Keyboard**:
  - `ESC` pada gameplay: Kembali ke Menu Utama.
  - `ESC` atau `M` pada halaman Demonstrasi: Kembali ke Menu Utama.

---

## 6. Tingkat Kesulitan (Difficulty Modes)

Pemain dapat memilih tingkat kesulitan langsung dari Menu Utama sebelum menekan **PLAY**:

| Mode | Interval Spawn | Kecepatan Meteor | Kecepatan Api | Peluang Api | Karakteristik |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **EASY** | ~1,5 detik | 170 – 230 px/s | 190 – 250 px/s | 20% | Objek jatuh santai, kepadatan rendah |
| **MEDIUM** | ~1,0 detik | 250 – 330 px/s | 280 – 360 px/s | 30% | Kecepatan sedang, ritme stabil |
| **HARD** | ~0,6 detik | 350 – 440 px/s | 380 – 490 px/s | 35% | Jatuh sangat cepat, menuntut refleks tinggi |

---

## 7. Aturan Skor dan HP

- **HP Awal Pemain**: `6`
- **Tangkisan Berhasil**:
  - **Meteor**: Ditangkis pedang $\rightarrow$ Skor `+1`, HP tidak berkurang, efek suara meteor berbunyi.
  - **Api**: Ditangkis pedang $\rightarrow$ Skor `+2`, HP tidak berkurang, efek suara api berbunyi.
- **Objek Lolos ke Dasar Layar**:
  - **Meteor**: Mencapai dasar arena $\rightarrow$ HP berkurang `1`.
  - **Api**: Mencapai dasar arena $\rightarrow$ HP berkurang `2`.
- **Game Over**:
  - Terjadi ketika HP pemain bernilai `0` atau kurang.
  - Pemain dapat memilih **PLAY AGAIN** untuk mengulang langsung dengan mode yang sama atau **MAIN MENU** untuk kembali ke menu awal.

---

## 8. Panduan Troubleshooting

1. **Webcam Tidak Terdeteksi / Gagal Dibuka**:
   - Pastikan webcam terhubung dan tidak sedang digunakan oleh aplikasi lain (seperti Zoom, Teams, Google Meet, atau browser).
   - Jika memiliki lebih dari satu kamera, Anda dapat mengganti indeks kamera pada baris inisialisasi di `main.py` (`CameraManager(camera_index=0)` menjadi `camera_index=1`).
2. **Pedang Tidak Mengikuti Tangan**:
   - Buka menu **DEMONSTRATION** untuk melihat hasil segmentasi kamera secara langsung.
   - Pastikan pencahayaan ruangan cukup terang dan merata.
   - Hindari berada persis di depan dinding atau objek yang memiliki warna serupa dengan warna kulit (krem/cokelat kayu).
