# 🖐️ RETROLENS AR Hand Tracking Filter Portal (Python + MediaPipe)

Aplikasi filter AR interaktif berbasis gestur tangan menggunakan **OpenCV** dan **MediaPipe**, terinspirasi dan 100% identik dengan filter viral **"RETROLENS Pake Python"** di TikTok.

---

## 📸 2 Pilihan Mode Portal Lensa:

1. **MODE 1: 2D (4 Titik Persegi Panjang)**:
   - Menggunakan **4 titik saja** (Jempol & Telunjuk dari kedua tangan: *Thumb 1, Index 1, Index 2, Thumb 2*).
   - Membentuk portal bingkai persegi panjang yang bersih, rapi, dan minimalis dengan 4 node emas di sudut dan border glow.
2. **MODE 2: 3D (Prisma 5 Jari)**:
   - Menghubungkan seluruh **10 ujung jari** dari kedua tangan membentuk prisma 3D AR holografis.
   - Dilengkapi *Longitudinal Ribs*, *X-Cross Lattice Mesh*, cincin penampang kedalaman (*Spatial Depth Rings*), pencahayaan vertikal gradien 3D (Cyan atas ➔ Magenta lantai bawah), dan skala node berbasis Z-depth.

---

## 🎮 Kontrol & Shortcut:

| Aksi | Gestur Tangan | Shortcut Keyboard |
| :--- | :--- | :--- |
| **Ganti Mode (2D ⟷ 3D)** | Kepalkan KEDUA Tangan bersamaan | `m` atau `c` |
| **Ganti Filter Berikutnya** | Sentuh Jempol - Kelingking (`🤙`) / OK (`👌👌`) | `n`, `SPACE`, `TAB` |
| **Ganti Filter Sebelumnya** | - | `p` |
| **Pilih Filter Langsung** | - | Angka `1` s/d `0` |
| **Fist Mode (Layar Merah + Suara)** | Kepalkan SATU Tangan (`👊`) | - |
| **Keluar Aplikasi** | - | `q` atau `ESC` |

---

## 🚀 Cara Menjalankan:

Cukup klik dua kali file **`run.bat`**, atau jalankan melalui terminal:

```bash
venv\Scripts\activate
python main.py
```
