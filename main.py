"""
================================================================================
  RETROLENS: AR Hand Tracking Filter Portal (Python OpenCV + MediaPipe)
  - Desain & Fitur 100% Persis Video TikTok "RETROLENS Pake Python".
  - Mode: 3D (Full 5 Jari) & 2D (Jempol-Telunjuk) [Toggle: Tekan 'c' / Kepal 2 Tangan].
  - Ganti Filter: Sentuh Jempol-Kelingking (🤙) / Gestur OK (👌👌) / Tombol 'n' & 'p'.
  - Efek Fist Mode (👊): Layar Merah Membara + Suara 'lawan.wav'.
  - Visual Skeleton Tangan Emas & Garis Penghubung 3D Antar Ujung Jari.
================================================================================
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import math
import winsound
import os
import warnings

# Sembunyikan pesan deprecation warning protobuf bawaan MediaPipe
warnings.filterwarnings("ignore", category=UserWarning)

# --- PATH AUDIO SUARA ---
AUDIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lawan.wav")

# --- DAFTAR FILTER RETROLENS ---
FILTER_NAMES = [
    "PIXELATE",
    "CARTOON (RAINBOW WAVE)",
    "DUAL-TONE (POP ART)",
    "SKETCH",
    "RGB GLITCH",
    "THERMAL (HEATMAP)",
    "CYBERPUNK (NEON)",
    "FROSTED GLASS BLUR",
    "SEPIA RETRO",
    "INVERT (X-RAY)"
]
current_filter_idx = 0

# --- DAFTAR MODE LENSA PORTAL ---
MODES = [
    "2D (4 Titik Persegi Panjang)",
    "3D (Prisma 5 Jari)"
]
current_mode_idx = 0

# Timer & Cooldown Gestur
last_gesture_switch_time = 0.0
last_mode_toggle_time = 0.0
last_sound_play_time = 0.0
is_fist_prev = False

# Toast Notifikasi
toast_message = ""
toast_timer = 0.0


# =====================================================================
# 1. HELPER: WARNA PELANGI DINAMIS & TOAST
# =====================================================================
def get_rainbow_color(speed=90.0, offset=0.0):
    """Menghasilkan warna BGR pelangi dinamis."""
    hue = int((time.time() * speed + offset) % 180)
    hsv_pixel = np.uint8([[[hue, 255, 255]]])
    bgr_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)[0][0]
    return (int(bgr_pixel[0]), int(bgr_pixel[1]), int(bgr_pixel[2]))


def set_toast(msg, duration=1.8):
    """Menampilkan pop-up notifikasi di layar."""
    global toast_message, toast_timer
    toast_message = msg
    toast_timer = time.time() + duration


def play_lawan_sound():
    """Memutar audio lawan.wav secara non-blocking."""
    global last_sound_play_time
    if os.path.exists(AUDIO_FILE) and (time.time() - last_sound_play_time > 0.8):
        last_sound_play_time = time.time()
        try:
            winsound.PlaySound(AUDIO_FILE, winsound.SND_ASYNC | winsound.SND_FILENAME)
        except Exception as e:
            print(f"Audio error: {e}")


# =====================================================================
# 2. HELPER: DETEKSI GESTUR TANGAN
# =====================================================================
def is_hand_fist(hand_lm):
    """
    Mendeteksi apakah tangan benar-benar mengepal (Fist 👊) secara presisi:
    - Ke-4 jari (Telunjuk, Tengah, Manis, Kelingking) HARUS terlipat erat ke telapak.
    - Ujung tiap jari harus lebih dekat ke pergelangan tangan (wrist) daripada sendi PIP dan MCP.
    - Ibu jari tidak boleh terentang bebas.
    """
    wrist = hand_lm[0]
    
    # Format: (Tip, PIP, MCP)
    fingers = [
        (8, 6, 5),    # Telunjuk
        (12, 10, 9),  # Tengah
        (16, 14, 13), # Manis
        (20, 18, 17)  # Kelingking
    ]
    
    closed_count = 0
    for tip_idx, pip_idx, mcp_idx in fingers:
        d_tip = math.hypot(hand_lm[tip_idx].x - wrist.x, hand_lm[tip_idx].y - wrist.y)
        d_pip = math.hypot(hand_lm[pip_idx].x - wrist.x, hand_lm[pip_idx].y - wrist.y)
        d_mcp = math.hypot(hand_lm[mcp_idx].x - wrist.x, hand_lm[mcp_idx].y - wrist.y)

        # Ujung jari harus lebih pendek dibanding sendi PIP dan MCP secara tegas
        if (d_tip < d_pip) and (d_tip < d_mcp * 0.88):
            closed_count += 1

    # Cek jempol agar tidak terentang
    d_thumb_tip = math.hypot(hand_lm[4].x - wrist.x, hand_lm[4].y - wrist.y)
    d_thumb_mcp = math.hypot(hand_lm[2].x - wrist.x, hand_lm[2].y - wrist.y)
    thumb_closed = (d_thumb_tip < d_thumb_mcp * 1.30)

    # Hanya bernilai True jika seluruh 4 jari terlipat erat (4/4) dan jempol menutup
    return (closed_count == 4) and thumb_closed


def check_thumb_pinky_touch(hand_lm, w, h):
    """
    Mendeteksi gestur sentuh Jempol dan Kelingking pada 1 tangan.
    Sesuai petunjuk di video: [Sentuh Jempol-Kelingking].
    """
    thumb = (int(hand_lm[4].x * w), int(hand_lm[4].y * h))
    pinky = (int(hand_lm[20].x * w), int(hand_lm[20].y * h))
    dist = math.hypot(thumb[0] - pinky[0], thumb[1] - pinky[1])
    center = ((thumb[0] + pinky[0]) // 2, (thumb[1] + pinky[1]) // 2)
    return (dist < 40), center


def check_double_ok_gesture(h1, h2, w, h):
    """Mendeteksi gestur kedua tangan OK sign bersentuhan (👌👌)."""
    t1 = (int(h1[4].x * w), int(h1[4].y * h))
    i1 = (int(h1[8].x * w), int(h1[8].y * h))
    t2 = (int(h2[4].x * w), int(h2[4].y * h))
    i2 = (int(h2[8].x * w), int(h2[8].y * h))

    dist_pinch1 = math.hypot(i1[0] - t1[0], i1[1] - t1[1])
    dist_pinch2 = math.hypot(i2[0] - t2[0], i2[1] - t2[1])

    is_ok1 = dist_pinch1 < 42
    is_ok2 = dist_pinch2 < 42

    center1 = ((t1[0] + i1[0]) // 2, (t1[1] + i1[1]) // 2)
    center2 = ((t2[0] + i2[0]) // 2, (t2[1] + i2[1]) // 2)

    dist_touch = math.hypot(center1[0] - center2[0], center1[1] - center2[1])
    is_touching = (dist_touch < 75)
    return (is_ok1 and is_ok2 and is_touching), center1, center2


# =====================================================================
# 3. HELPER: MENGGAMBAR SKELETON EMAS TANGAN (GOLDEN SKELETON)
# =====================================================================
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Jempol
    (0, 5), (5, 6), (6, 7), (7, 8),        # Telunjuk
    (5, 9), (9, 10), (10, 11), (11, 12),   # Tengah
    (9, 13), (13, 14), (14, 15), (15, 16), # Manis
    (13, 17), (17, 18), (18, 19), (19, 20),# Kelingking
    (0, 17)                                # Telapak
]

def draw_golden_hand_landmarks(frame, hand_lm, w, h):
    """Menggambar skeleton tangan berwarna emas elegan persis seperti di video."""
    gold_color = (10, 220, 255)   # Kuning Emas BGR
    white_core = (255, 255, 255)
    
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lm]

    # Garis penghubung sendi
    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(frame, pts[start_idx], pts[end_idx], gold_color, 2, cv2.LINE_AA)

    # Titik sendi & ujung jari
    for i, pt in enumerate(pts):
        if i in [4, 8, 12, 16, 20]:
            # Ujung jari: Lingkaran lebih besar bercahaya
            cv2.circle(frame, pt, 7, gold_color, -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 4, white_core, -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 9, (255, 255, 255), 1, cv2.LINE_AA)
        else:
            cv2.circle(frame, pt, 4, gold_color, -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 2, white_core, -1, cv2.LINE_AA)


# =====================================================================
# 3.5 HELPER: WIREFRAME PORTAL 3D DENGAN PEWARNAAN GRADIEN 3D (CYAN ➔ MAGENTA)
# =====================================================================
def get_3d_depth_color(y_val, y_min, y_span):
    """
    Menghasilkan warna gradien 3D vertikal:
    - Atas (Langit-langit / jari atas): Neon Cyan / Ice Blue (255, 230, 40)
    - Bawah (Dasar / lantai / jempol bawah): Cyberpunk Neon Magenta / Hot Pink (230, 40, 245)
    """
    ratio = float(np.clip((y_val - y_min) / y_span, 0.0, 1.0))
    b = int((1.0 - ratio) * 255 + ratio * 230)
    g = int((1.0 - ratio) * 230 + ratio * 40)
    r = int((1.0 - ratio) * 40 + ratio * 245)
    return (b, g, r)


def draw_3d_wireframe_portal(frame, h1_tips, h2_tips, h1_z, h2_z, hull):
    """
    Menggambar wireframe 3D prisma/kristal AR dengan nuansa kedalaman 3D nyata:
    - Warna Atas: Neon Cyan / Ice Blue.
    - Warna Bawah: Neon Magenta / Hot Pink (efek lantai/bayangan 3D).
    - 5 Garis Rusuk Utama (Longitudinal Ribs) antar ujung jari.
    - Garis Silang Diagonal 3D (X-Cross Lattice) antar jari bersebelahan.
    - Cincin Penampang Ruang 3D (Spatial Depth Rings).
    - Node Ujung Jari dengan skala Z-depth & warna gradien vertikal.
    """
    overlay = frame.copy()
    y_min = float(np.min(hull[:, 0, 1]))
    y_max = float(np.max(hull[:, 0, 1]))
    y_span = max(1.0, y_max - y_min)

    # 1. Garis Rusuk Utama Antar-Jari (Longitudinal Ribs) dengan Warna Gradien
    for p1, p2 in zip(h1_tips, h2_tips):
        avg_y = (p1[1] + p2[1]) / 2.0
        line_col = get_3d_depth_color(avg_y, y_min, y_span)
        cv2.line(overlay, p1, p2, line_col, 2, cv2.LINE_AA)
        cv2.line(overlay, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

    # 2. Garis Silang Diagonal 3D (X-Cross Lattice)
    for i in range(len(h1_tips) - 1):
        mid_y1 = (h1_tips[i][1] + h2_tips[i + 1][1]) / 2.0
        mid_y2 = (h1_tips[i + 1][1] + h2_tips[i][1]) / 2.0
        col1 = get_3d_depth_color(mid_y1, y_min, y_span)
        col2 = get_3d_depth_color(mid_y2, y_min, y_span)
        cv2.line(overlay, h1_tips[i], h2_tips[i + 1], col1, 1, cv2.LINE_AA)
        cv2.line(overlay, h1_tips[i + 1], h2_tips[i], col2, 1, cv2.LINE_AA)

    # 3. Perimeter Arch Tiap Tangan (Warna Sesuai Posisi Y)
    for i in range(len(h1_tips) - 1):
        avg_y1 = (h1_tips[i][1] + h1_tips[i + 1][1]) / 2.0
        avg_y2 = (h2_tips[i][1] + h2_tips[i + 1][1]) / 2.0
        cv2.line(overlay, h1_tips[i], h1_tips[i + 1], get_3d_depth_color(avg_y1, y_min, y_span), 2, cv2.LINE_AA)
        cv2.line(overlay, h2_tips[i], h2_tips[i + 1], get_3d_depth_color(avg_y2, y_min, y_span), 2, cv2.LINE_AA)

    # 4. Penampang Ruang 3D (Spatial Depth Rings di kedalaman 35% dan 70%)
    for t in [0.35, 0.70]:
        mid_pts = []
        for p1, p2 in zip(h1_tips, h2_tips):
            mx = int((1.0 - t) * p1[0] + t * p2[0])
            my = int((1.0 - t) * p1[1] + t * p2[1])
            mid_pts.append((mx, my))
        for i in range(len(mid_pts) - 1):
            ring_y = (mid_pts[i][1] + mid_pts[i + 1][1]) / 2.0
            cv2.line(overlay, mid_pts[i], mid_pts[i + 1], get_3d_depth_color(ring_y, y_min, y_span), 1, cv2.LINE_AA)

    # Blending wireframe 3D semi-transparan
    cv2.addWeighted(overlay, 0.88, frame, 0.12, 0, frame)

    # 5. Dual Layer Border (Outer Glow Gradien Vertikal + Inner Crisp Line)
    n_hull = len(hull)
    for i in range(n_hull):
        pt_a = tuple(hull[i][0])
        pt_b = tuple(hull[(i + 1) % n_hull][0])
        edge_y = (pt_a[1] + pt_b[1]) / 2.0
        edge_col = get_3d_depth_color(edge_y, y_min, y_span)
        # Glow Luar Tebal
        cv2.line(frame, pt_a, pt_b, edge_col, 5, cv2.LINE_AA)
        # Garis Inti Putih Terang
        cv2.line(frame, pt_a, pt_b, (255, 255, 255), 2, cv2.LINE_AA)

    # 6. Node Ujung Jari dengan Skala Perspektif 3D & Warna Berdasarkan Posisi Y
    for p, z in zip(h1_tips, h1_z):
        r = int(np.clip(7 - z * 24, 4, 13))
        node_col = get_3d_depth_color(p[1], y_min, y_span)
        cv2.circle(frame, p, r + 4, node_col, -1, cv2.LINE_AA)
        cv2.circle(frame, p, r, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, p, r + 5, (255, 255, 255), 1, cv2.LINE_AA)

    for p, z in zip(h2_tips, h2_z):
        r = int(np.clip(7 - z * 24, 4, 13))
        node_col = get_3d_depth_color(p[1], y_min, y_span)
        cv2.circle(frame, p, r + 4, node_col, -1, cv2.LINE_AA)
        cv2.circle(frame, p, r, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, p, r + 5, (255, 255, 255), 1, cv2.LINE_AA)


# =====================================================================
# 4. HELPER: FILTER RETROLENS PERSIS TIKTOK
# =====================================================================
def apply_retro_filter(frame_roi, mode_idx, rainbow_bgr, t_sec):
    """Menerapkan filter visual retro yang identik dengan video TikTok."""
    h, w, _ = frame_roi.shape
    if h == 0 or w == 0:
        return frame_roi

    # 1. PIXELATE (MOSAIC + GLITCH HEADER)
    if mode_idx == 0:
        px = max(8, min(32, w // 16, h // 16))
        small = cv2.resize(frame_roi, (max(1, w // px), max(1, h // px)), interpolation=cv2.INTER_LINEAR)
        pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        # Glitch warna tipis
        shift = 8
        if w > shift * 2:
            pixelated[:, shift:, 0] = pixelated[:, :-shift, 0]
            pixelated[:, :-shift, 2] = pixelated[:, shift:, 2]
        return pixelated

    # 2. CARTOON (RAINBOW WAVE / GELOMBANG PELANGI DIAGONAL PERSIS GAMBAR 2)
    elif mode_idx == 1:
        # Menghasilkan garis pelangi diagonal bergerak
        y_coords, x_coords = np.mgrid[0:h, 0:w]
        phase = ((x_coords + y_coords * 1.5) * 0.15 - t_sec * 6.0) % (2 * np.pi)
        wave_hue = ((np.sin(phase) + 1.0) * 0.5 * 179).astype(np.uint8)
        
        hsv_wave = np.zeros((h, w, 3), dtype=np.uint8)
        hsv_wave[:, :, 0] = wave_hue
        hsv_wave[:, :, 1] = 255
        hsv_wave[:, :, 2] = 255
        bgr_wave = cv2.cvtColor(hsv_wave, cv2.COLOR_HSV2BGR)
        return bgr_wave

    # 3. DUAL-TONE (POP ART COLOR BLOCK PERSIS GAMBAR 3)
    elif mode_idx == 2:
        gray = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)
        pop_art = np.zeros_like(frame_roi)
        
        # 4 Palet warna pop-art (Cyan, Kuning, Magenta, Oranye)
        mask1 = gray < 64
        mask2 = (gray >= 64) & (gray < 128)
        mask3 = (gray >= 128) & (gray < 192)
        mask4 = gray >= 192

        pop_art[mask1] = (255, 0, 180)   # Magenta / Ungu
        pop_art[mask2] = (0, 140, 255)   # Oranye
        pop_art[mask3] = (0, 255, 255)   # Kuning Terang
        pop_art[mask4] = (255, 255, 0)   # Cyan / Aqua
        return pop_art

    # 4. SKETCH (PENCIL SKETCH PERSIS GAMBAR 4)
    elif mode_idx == 3:
        gray = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2GRAY)
        inv = cv2.bitwise_not(gray)
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        sketch_bgr = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        # Efek pixel glitch di baris atas seperti di screenshot
        top_h = max(1, h // 5)
        top_roi = sketch_bgr[0:top_h, :]
        small_top = cv2.resize(top_roi, (max(1, w // 18), max(1, top_h // 12)), interpolation=cv2.INTER_LINEAR)
        sketch_bgr[0:top_h, :] = cv2.resize(small_top, (w, top_h), interpolation=cv2.INTER_NEAREST)
        return sketch_bgr

    # 5. RGB GLITCH / CHROMATIC ABERRATION
    elif mode_idx == 4:
        glitch = frame_roi.copy()
        shift = 16
        if w > shift * 2:
            glitch[:, shift:, 0] = frame_roi[:, :-shift, 0]
            glitch[:, :-shift, 2] = frame_roi[:, shift:, 2]
        return glitch

    # 6. THERMAL (HEATMAP / JET)
    elif mode_idx == 5:
        return cv2.applyColorMap(frame_roi, cv2.COLORMAP_JET)

    # 7. CYBERPUNK (NEON MAGMA)
    elif mode_idx == 6:
        hsv = cv2.cvtColor(frame_roi, cv2.COLOR_BGR2HSV)
        hsv[:, :, 0] = (hsv[:, :, 0].astype(int) + 35) % 180
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.4)
        neon = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        return cv2.applyColorMap(neon, cv2.COLORMAP_MAGMA)

    # 8. FROSTED GLASS BLUR
    elif mode_idx == 7:
        ksize = 35
        blur = cv2.GaussianBlur(frame_roi, (ksize, ksize), 0)
        return cv2.addWeighted(blur, 0.88, np.full_like(blur, 240), 0.12, 0)

    # 9. SEPIA RETRO
    elif mode_idx == 8:
        kernel = np.array([
            [0.272, 0.534, 0.131],
            [0.349, 0.686, 0.168],
            [0.393, 0.769, 0.189]
        ])
        sepia = cv2.transform(frame_roi, kernel)
        return np.clip(sepia, 0, 255).astype(np.uint8)

    # 10. INVERT / X-RAY
    elif mode_idx == 9:
        return cv2.bitwise_not(frame_roi)

    return frame_roi


# =====================================================================
# 5. HELPER: HEADER UI PERSIS VIDEO TIKTOK
# =====================================================================
def draw_tiktok_retrolens_header(frame, mode_text, filter_name, fps):
    """
    Menggambar header teks di sudut kiri atas persis tampilan video TikTok:
      MODE: 2D (4 Titik Persegi Panjang) / 3D (Prisma 5 Jari) [Tekan 'm'/'c' / Kepal 2 Tangan]
      FILTER: <NAME> [Sentuh Jempol-Kelingking / 'n' / 'p']
    """
    h, w, _ = frame.shape

    # Warna Kuning Terang untuk MODE (persis screenshot)
    yellow_color = (0, 240, 255)
    # Warna Putih Terang untuk FILTER (persis screenshot)
    white_color = (255, 255, 255)

    mode_line = f"MODE: {mode_text} [Tekan 'm'/'c' / Kepal 2 Tangan]"
    filter_line = f"FILTER: {filter_name} [Sentuh Jempol-Kelingking / 'n' / 'p']"

    # Bayangan teks (drop shadow hitam) untuk kontras tinggi di latar apapun
    cv2.putText(frame, mode_line, (22, 36), cv2.FONT_HERSHEY_DUPLEX, 0.60, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame, mode_line, (20, 34), cv2.FONT_HERSHEY_DUPLEX, 0.60, yellow_color, 1, cv2.LINE_AA)

    cv2.putText(frame, filter_line, (22, 66), cv2.FONT_HERSHEY_DUPLEX, 0.58, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame, filter_line, (20, 64), cv2.FONT_HERSHEY_DUPLEX, 0.58, white_color, 1, cv2.LINE_AA)

    # Toast Notifikasi di Bagian Tengah Bawah
    global toast_message, toast_timer
    if time.time() < toast_timer and toast_message:
        tw = 480
        tx = (w - tw) // 2
        ty = h - 65
        overlay = frame.copy()
        cv2.rectangle(overlay, (tx, ty), (tx + tw, ty + 36), (20, 20, 25), -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        cv2.rectangle(frame, (tx, ty), (tx + tw, ty + 36), (0, 220, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, toast_message, (tx + 15, ty + 24),
                    cv2.FONT_HERSHEY_DUPLEX, 0.44, (0, 240, 255), 1, cv2.LINE_AA)


# =====================================================================
# 6. MAIN APPLICATION LOOP
# =====================================================================
def main():
    global current_filter_idx, current_mode_idx, last_gesture_switch_time
    global last_mode_toggle_time, is_fist_prev

    # MediaPipe Hands (Ultra Fast & Smooth)
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=0,              # Complexity 0 = Ultra Smooth 60+ FPS
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    prev_time = time.time()

    print("\n" + "=" * 70)
    print("  RETROLENS: AR HAND TRACKING FILTER PORTAL")
    print("  --------------------------------------------------")
    print("  2 PILIHAN MODE PORTAL:")
    print("    1. MODE 2D (4 Titik): Persegi panjang bersih (Jempol & Telunjuk).")
    print("    2. MODE 3D (Prisma 5 Jari): Wireframe kristal 3D berkedalaman.")
    print("  KONTROL & GESTUR:")
    print("    • Ganti Mode: Tekan 'm' atau 'c' / Kepalkan KEDUA Tangan bersamaan.")
    print("    • Ganti Filter: Sentuh Jempol-Kelingking (🤙) / OK Sign (👌👌) / 'n' / 'p'.")
    print("    • Fist Mode: Kepalkan SATU Tangan (👊) -> Layar Merah + lawan.wav.")
    print("    • Tombol 'q' / ESC untuk Keluar.")
    print("=" * 70 + "\n")

    set_toast("Siap! Gunakan 'm'/'c' untuk ganti Mode 2D/3D ✨", 3.0)

    fist_streak_single = 0
    fist_streak_double = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Kamera tidak terdeteksi. Keluar...")
            break

        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 30.0
        prev_time = curr_time

        # Flip horizontal untuk mirror alami
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rainbow_color = get_rainbow_color(speed=90.0)

        # Konversi ke RGB untuk MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        hands_count = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
        fist_hands_count = 0
        hand_lm_list = []

        if results.multi_hand_landmarks:
            for hand_lm in results.multi_hand_landmarks:
                hand_lm_list.append(hand_lm.landmark)
                if is_hand_fist(hand_lm.landmark):
                    fist_hands_count += 1

        # Hitung streak frame agar stabil dan tidak terlalu sensitif
        if fist_hands_count == 2:
            fist_streak_double += 1
            fist_streak_single = 0
        elif fist_hands_count == 1:
            fist_streak_single += 1
            fist_streak_double = 0
        else:
            fist_streak_single = 0
            fist_streak_double = 0

        # =============================================================
        # 1. KONDISI: KEPAL KEDUA TANGAN (TOGGLE MODE 2D / 3D)
        # =============================================================
        if fist_streak_double >= 3:
            if curr_time - last_mode_toggle_time > 1.2:
                last_mode_toggle_time = curr_time
                current_mode_idx = (current_mode_idx + 1) % len(MODES)
                set_toast(f"🔄 MODE: {MODES[current_mode_idx]}", 1.8)

        # =============================================================
        # 2. KONDISI: SATU TANGAN MENGEPAL (FIST 👊) -> LAYAR MERAH + SUARA
        # =============================================================
        elif fist_streak_single >= 3:
            if not is_fist_prev:
                play_lawan_sound()
                set_toast("👊 FIST / RAGE MODE AKTIF!", 1.5)
            is_fist_prev = True

            # Layar Merah Membara
            red_overlay = np.zeros_like(frame)
            red_overlay[:, :, 2] = 235
            red_overlay[:, :, 0] = 20
            red_overlay[:, :, 1] = 20
            frame = cv2.addWeighted(frame, 0.35, red_overlay, 0.65, 0)
            cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 255), 16, cv2.LINE_AA)

            # Banner Lawan
            cv2.putText(frame, "LAWAN! 👊", (w // 2 - 100, 60),
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

        else:
            is_fist_prev = False

            # =========================================================
            # 3. KONDISI: GESTUR GANTI FILTER (Jempol-Kelingking & OK Sign)
            # =========================================================
            trigger_filter_change = False
            spark_center = None

            # Cek Jempol-Kelingking pada masing-masing tangan
            for lm in hand_lm_list:
                is_touch, c_pt = check_thumb_pinky_touch(lm, w, h)
                if is_touch:
                    trigger_filter_change = True
                    spark_center = c_pt
                    break

            # Cek Gestur OK Sign (👌👌) jika ada 2 tangan
            if not trigger_filter_change and len(hand_lm_list) >= 2:
                is_ok_touch, c1, c2 = check_double_ok_gesture(hand_lm_list[0], hand_lm_list[1], w, h)
                if is_ok_touch:
                    trigger_filter_change = True
                    spark_center = ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2)

            if trigger_filter_change:
                if spark_center:
                    cv2.circle(frame, spark_center, 24, (255, 255, 255), 3, cv2.LINE_AA)
                    cv2.circle(frame, spark_center, 34, rainbow_color, 2, cv2.LINE_AA)

                if curr_time - last_gesture_switch_time > 0.8:
                    last_gesture_switch_time = curr_time
                    current_filter_idx = (current_filter_idx + 1) % len(FILTER_NAMES)
                    set_toast(f"✨ FILTER: {FILTER_NAMES[current_filter_idx]}", 1.8)

            # =========================================================
            # 4. GAMBAR SKELETON EMAS PADA SEMUA TANGAN
            # =========================================================
            for lm in hand_lm_list:
                draw_golden_hand_landmarks(frame, lm, w, h)

            # =========================================================
            # 5. PEMBUATAN PORTAL LENSA RETROLENS (MODE 1: 2D vs MODE 2: 3D)
            # =========================================================
            is_3d_mode = ("3D" in MODES[current_mode_idx])
            portal_points = []
            h1_tips = []
            h2_tips = []
            h1_z = []
            h2_z = []

            if len(hand_lm_list) >= 2:
                h1 = hand_lm_list[0]
                h2 = hand_lm_list[1]

                if is_3d_mode:
                    # MODE 2: 3D PRISMA (10 UJUNG JARI KEDUA TANGAN)
                    tip_indices = [4, 8, 12, 16, 20]
                    h1_tips = [(int(h1[idx].x * w), int(h1[idx].y * h)) for idx in tip_indices]
                    h2_tips = [(int(h2[idx].x * w), int(h2[idx].y * h)) for idx in tip_indices]
                    h1_z = [h1[idx].z for idx in tip_indices]
                    h2_z = [h2[idx].z for idx in tip_indices]
                    portal_points = h1_tips + h2_tips
                else:
                    # MODE 1: 2D PERSEGI PANJANG (4 TITIK: JEMPOL & TELUNJUK)
                    h1_thumb = (int(h1[4].x * w), int(h1[4].y * h))
                    h1_index = (int(h1[8].x * w), int(h1[8].y * h))
                    h2_index = (int(h2[8].x * w), int(h2[8].y * h))
                    h2_thumb = (int(h2[4].x * w), int(h2[4].y * h))
                    portal_points = [h1_thumb, h1_index, h2_index, h2_thumb]

            elif len(hand_lm_list) == 1:
                # Jika 1 tangan
                h1 = hand_lm_list[0]
                if is_3d_mode:
                    tip_indices = [4, 8, 12, 16, 20]
                    portal_points = [(int(h1[idx].x * w), int(h1[idx].y * h)) for idx in tip_indices]
                    portal_points.append((int(h1[0].x * w), int(h1[0].y * h)))  # Pergelangan
                else:
                    # 4 Titik pada 1 tangan (Jempol, Telunjuk, Kelingking, Pergelangan)
                    portal_points = [
                        (int(h1[4].x * w), int(h1[4].y * h)),
                        (int(h1[8].x * w), int(h1[8].y * h)),
                        (int(h1[20].x * w), int(h1[20].y * h)),
                        (int(h1[0].x * w), int(h1[0].y * h))
                    ]

            # Render Filter ke dalam Lensa Polygon Convex Hull
            if len(portal_points) >= 3:
                pts_arr = np.array(portal_points, dtype=np.int32)
                hull = cv2.convexHull(pts_arr)
                area = cv2.contourArea(hull)

                if area > 1200:
                    # Bounding Box ROI untuk pemrosesan super cepat 60+ FPS
                    rx, ry, rw, rh = cv2.boundingRect(hull)
                    rx = max(0, rx)
                    ry = max(0, ry)
                    rw = min(w - rx, rw)
                    rh = min(h - ry, rh)

                    if rw > 10 and rh > 10:
                        roi_frame = frame[ry:ry + rh, rx:rx + rw]
                        roi_filtered = apply_retro_filter(roi_frame, current_filter_idx, rainbow_color, curr_time)

                        # Efek Pencahayaan Kedalaman 3D Vertikal (Khusus Mode 3D)
                        if is_3d_mode:
                            grad_y = np.linspace(0.0, 1.0, rh, dtype=np.float32).reshape(rh, 1)
                            b_col = ((1.0 - grad_y) * 230 + grad_y * 200).astype(np.uint8)
                            g_col = ((1.0 - grad_y) * 210 + grad_y * 30).astype(np.uint8)
                            r_col = ((1.0 - grad_y) * 30 + grad_y * 220).astype(np.uint8)

                            tint_3d = cv2.merge([
                                np.tile(b_col, (1, rw)),
                                np.tile(g_col, (1, rw)),
                                np.tile(r_col, (1, rw))
                            ])
                            roi_filtered = cv2.addWeighted(roi_filtered, 0.84, tint_3d, 0.16, 0)

                        # Mask lokal ROI
                        roi_hull = hull - np.array([rx, ry])
                        mask_roi = np.zeros((rh, rw), dtype=np.uint8)
                        cv2.fillPoly(mask_roi, [roi_hull], 255)
                        mask_roi_inv = cv2.bitwise_not(mask_roi)

                        bg_roi = cv2.bitwise_and(roi_frame, roi_frame, mask=mask_roi_inv)
                        fg_roi = cv2.bitwise_and(roi_filtered, roi_filtered, mask=mask_roi)
                        frame[ry:ry + rh, rx:rx + rw] = cv2.add(bg_roi, fg_roi)

                    # Visualisasi Lensa: MODE 3D vs MODE 2D
                    if is_3d_mode and len(hand_lm_list) >= 2:
                        # Render Wireframe 3D Prisma Berkedalaman Nyata
                        draw_3d_wireframe_portal(frame, h1_tips, h2_tips, h1_z, h2_z, hull)
                    else:
                        # MODE 1 (2D PERSEGI PANJANG): Garis Border Bersih Rapi + 4 Node Emas
                        cv2.polylines(frame, [hull], isClosed=True, color=(10, 220, 255), thickness=5, lineType=cv2.LINE_AA)
                        cv2.polylines(frame, [hull], isClosed=True, color=(255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
                        for pt in hull:
                            cv2.circle(frame, tuple(pt[0]), 8, (10, 220, 255), -1, cv2.LINE_AA)
                            cv2.circle(frame, tuple(pt[0]), 5, (255, 255, 255), -1, cv2.LINE_AA)
                            cv2.circle(frame, tuple(pt[0]), 10, (255, 255, 255), 1, cv2.LINE_AA)

        # Gambar Header Teks RetroLens TikTok di Pojok Kiri Atas
        draw_tiktok_retrolens_header(frame, MODES[current_mode_idx], FILTER_NAMES[current_filter_idx], fps)

        # Tampilkan Jendela Kamera
        cv2.imshow("RETROLENS Pake Python", frame)

        # Kontrol Keyboard
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('m') or key == ord('M') or key == ord('c') or key == ord('C'):
            current_mode_idx = (current_mode_idx + 1) % len(MODES)
            set_toast(f"Mode: {MODES[current_mode_idx]}")
        elif key == ord('n') or key == ord('N') or key == ord(' ') or key == 9:
            current_filter_idx = (current_filter_idx + 1) % len(FILTER_NAMES)
            set_toast(f"Filter: {FILTER_NAMES[current_filter_idx]}")
        elif key == ord('p') or key == ord('P'):
            current_filter_idx = (current_filter_idx - 1) % len(FILTER_NAMES)
            set_toast(f"Filter: {FILTER_NAMES[current_filter_idx]}")
        elif ord('0') <= key <= ord('9'):
            idx = (key - ord('1')) % 10
            current_filter_idx = idx
            set_toast(f"Filter: {FILTER_NAMES[current_filter_idx]}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
