# 🖐️ RETROLENS AR Hand Tracking Filter Portal (Python + MediaPipe)

Aplikasi filter AR interaktif berbasis gestur tangan menggunakan **OpenCV** dan **MediaPipe**, terinspirasi dan 100% identik dengan filter viral **"RETROLENS Pake Python"** di TikTok.

---

## 📸 Fitur Utama Sesuai Video:

1. **Portal 3D Lensa (Full 5 Jari)**:
   - Menghubungkan seluruh 10 ujung jari dari kedua tangan membentuk portal prisma 3D AR transparan dengan garis penghubung antar-jari.
   - Dilengkapi garis batas putih bersih *(White Clean Border)* dan simpul bercahaya emas.
2. **Skeleton Tangan Emas *(Golden Hands)***:
   - Garis sendi dan titik ujung jari digambar dengan warna emas elegan dan inti putih persis di video.
3. **Filter Visual Identik**:
   - **PIXELATE**: Efek mozaik retro + glitch baris atas.
   - **CARTOON (RAINBOW WAVE)**: Gelombang pelangi diagonal animasi persis gambar kedua.
   - **DUAL-TONE (POP ART)**: Kuantisasi warna cerah (Cyan, Magenta, Kuning, Oranye) persis gambar ketiga.
   - **SKETCH**: Sketsa pensil + glitch strip atas persis gambar keempat.
   - **RGB GLITCH**: Efek distorsi chromatic aberration dinamis.
   - **THERMAL (HEATMAP)**, **CYBERPUNK (NEON)**, **FROSTED GLASS**, **SEPIA**, & **INVERT (X-RAY)**.
4. **Kontrol Gestur Tangan Alami**:
   - **Ganti Filter**: Sentuh Ujung Jempol & Kelingking (`🤙`) ATAU Gestur OK Bersentuhan (`👌👌`).
   - **Ganti Mode (3D ⟷ 2D)**: Tekan tombol `'c'` ATAU Kepalkan **KEDUA Tangan** bersamaan.
   - **Fist Mode (`👊`)**: Kepalkan **SATU Tangan** untuk mengaktifkan **Layar Merah Membara** dan memutar audio `lawan.wav`.

---

## 🎮 Kontrol & Shortcut:

| Aksi | Gestur Tangan | Shortcut Keyboard |
| :--- | :--- | :--- |
| **Ganti Filter Berikutnya** | Sentuh Jempol - Kelingking / OK (`👌👌`) | `n`, `SPACE`, `TAB` |
| **Ganti Filter Sebelumnya** | - | `p` |
| **Pilih Filter Langsung** | - | Angka `1` s/d `0` |
| **Ganti Mode (3D / 2D)** | Kepalkan Kedua Tangan | `c` |
| **Layar Merah + Suara** | Kepalkan 1 Tangan (`👊`) | - |
| **Keluar Aplikasi** | - | `q` atau `ESC` |

---

## 🚀 Cara Menjalankan:

Cukup klik dua kali file **`run.bat`**, atau jalankan melalui terminal:

```bash
venv\Scripts\activate
python main.py
```
