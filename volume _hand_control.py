import math
import time
import cv2
import numpy as np
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# ---------------- Settings (tune these) ----------------
wcam, hcam = 1280, 720     # try 1920, 1080 if your webcam supports it
MIN_RATIO = 0.25           # fingers closed -> 0 %
MAX_RATIO = 1.40           # fingers wide open -> 100 %
SMOOTHING = 0.7            # 0 = instant, closer to 1 = smoother but slower
DETECT_WIDTH = 640         # hand detection runs on a smaller image (faster)
DEBUG = False              # True prints the ratio for tuning
# --------------------------------------------------------

FONT = cv2.FONT_HERSHEY_DUPLEX

# ---------- Camera ----------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # better FPS at HD
cap.set(cv2.CAP_PROP_FRAME_WIDTH, wcam)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hcam)
cap.set(cv2.CAP_PROP_FPS, 30)

success, img = cap.read()
if not success:
    raise SystemExit("Camera not working")
H, W = img.shape[:2]
print(f"Camera resolution: {W} x {H}")

#  Hand detector (from HandTrackingModule.py) 
detector = htm.handDetector(maxHands=1, detectionCon=0.7)

#  Windows volume (pycaw)
device = AudioUtilities.GetSpeakers()
inference = device._dev.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
)
volume = cast(inference, POINTER(IAudioEndpointVolume))
volper = volume.GetMasterVolumeLevelScalar() * 100   # start from current volume

#  UI layout (scales with resolution) 
BAR_W = max(36, int(W * 0.035))
BAR_H = int(H * 0.50)
BAR_X = int(W * 0.07)
PX1 = BAR_X - 30
PX2 = BAR_X + BAR_W + 75
PY1 = max(0, int(H * 0.25) - 120)
PY2 = PY1 + 120 + BAR_H + 100
BAR_Y = PY1 + 120
PANEL_CX = (PX1 + PX2) // 2


def rounded_mask(w, h, r):
    m = np.zeros((h, w), np.uint8)
    r = min(r, w // 2, h // 2)
    cv2.rectangle(m, (r, 0), (w - 1 - r, h - 1), 255, -1)
    cv2.rectangle(m, (0, r), (w - 1, h - 1 - r), 255, -1)
    for cx, cy in ((r, r), (w - 1 - r, r), (r, h - 1 - r), (w - 1 - r, h - 1 - r)):
        cv2.circle(m, (cx, cy), r, 255, -1)
    return m


def make_gradient(h, w):
    """Top = red, middle = yellow, bottom = green."""
    hsv = np.zeros((h, w, 3), np.uint8)
    hsv[:, :, 0] = np.linspace(0, 60, h).astype(np.uint8)[:, None]
    hsv[:, :, 1] = 220
    hsv[:, :, 2] = 255
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


# Pre-computed once (fast)
panel_mask = rounded_mask(PX2 - PX1, PY2 - PY1, 24)
panel_bool = panel_mask > 0
panel_cnt, _ = cv2.findContours(panel_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
bar_mask = rounded_mask(BAR_W, BAR_H, BAR_W // 2)
bar_bool = bar_mask > 0
bar_cnt, _ = cv2.findContours(bar_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
gradient = make_gradient(BAR_H, BAR_W)


def level_color(per):
    row = int(np.clip((BAR_H - 1) - (BAR_H - 1) * per / 100, 0, BAR_H - 1))
    return tuple(int(c) for c in gradient[row, BAR_W // 2])


def shadow_text(img, text, org, scale, color, thick=2):
    cv2.putText(img, text, (org[0] + 2, org[1] + 2), FONT, scale, (0, 0, 0), thick + 2, cv2.LINE_AA)
    cv2.putText(img, text, org, FONT, scale, color, thick, cv2.LINE_AA)


def centered_text(img, text, cx, y, scale, color, thick=2):
    (tw, _), _ = cv2.getTextSize(text, FONT, scale, thick)
    shadow_text(img, text, (cx - tw // 2, y), scale, color, thick)


def draw_speaker(img, cx, cy, s, per, color=(255, 255, 255)):
    pts = np.array([(cx - s, cy - s * 0.35), (cx - s * 0.45, cy - s * 0.35),
                    (cx + s * 0.1, cy - s * 0.85), (cx + s * 0.1, cy + s * 0.85),
                    (cx - s * 0.45, cy + s * 0.35), (cx - s, cy + s * 0.35)], np.int32)
    cv2.fillPoly(img, [pts], color, cv2.LINE_AA)
    if per < 1:   # muted -> red X
        a, b = (int(cx + s * 0.45), int(cy - s * 0.4)), (int(cx + s * 1.05), int(cy + s * 0.4))
        c, d = (int(cx + s * 0.45), int(cy + s * 0.4)), (int(cx + s * 1.05), int(cy - s * 0.4))
        cv2.line(img, a, b, (80, 80, 255), 3, cv2.LINE_AA)
        cv2.line(img, c, d, (80, 80, 255), 3, cv2.LINE_AA)
    else:         # 1 to 3 sound waves
        waves = 1 + (per > 33) + (per > 66)
        for k in range(1, waves + 1):
            r = int(s * (0.45 + 0.4 * k))
            cv2.ellipse(img, (int(cx + s * 0.1), int(cy)), (r, r), 0, -45, 45, color, 2, cv2.LINE_AA)


def draw_volume_panel(img, per):
    # Dark glass panel
    roi = img[PY1:PY2, PX1:PX2]
    roi[panel_bool] = (roi[panel_bool] * 0.30).astype(np.uint8)
    cv2.drawContours(roi, panel_cnt, -1, (110, 110, 110), 1, cv2.LINE_AA)

    # Icon + title
    col = level_color(per)
    draw_speaker(img, PANEL_CX - 8, PY1 + 38, 16, per)
    centered_text(img, "VOLUME", PANEL_CX, PY1 + 92, 0.6, (230, 230, 230), 1)

    # Bar track + gradient fill
    broi = img[BAR_Y:BAR_Y + BAR_H, BAR_X:BAR_X + BAR_W]
    broi[bar_bool] = (55, 55, 55)
    fill_h = int(BAR_H * per / 100)
    if fill_h > 0:
        fm = bar_bool.copy()
        fm[:BAR_H - fill_h, :] = False
        broi[fm] = gradient[fm]
    cv2.drawContours(broi, bar_cnt, -1, (255, 255, 255), 2, cv2.LINE_AA)

    # Knob
    ky = BAR_Y + BAR_H - fill_h
    kx = BAR_X + BAR_W // 2
    cv2.circle(img, (kx, ky), BAR_W // 2 + 3, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(img, (kx, ky), BAR_W // 2 - 4, col, -1, cv2.LINE_AA)

    # Scale ticks
    for v in (0, 25, 50, 75, 100):
        ty = BAR_Y + BAR_H - int(BAR_H * v / 100)
        tx = BAR_X + BAR_W + 10
        cv2.line(img, (tx, ty), (tx + 10, ty), (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(img, str(v), (tx + 16, ty + 5), FONT, 0.45, (200, 200, 200), 1, cv2.LINE_AA)

    # Percentage
    centered_text(img, f"{int(round(per))}%", PANEL_CX, BAR_Y + BAR_H + 68, 1.3, col, 2)


pTime = time.time()
fps = 0

while True:
    success, img = cap.read()
    if not success:
        print("Camera not working")
        break

    img = cv2.flip(img, 1)  # mirror view

    # Detect on a small copy (fast); skeleton is drawn on the full HD image
    img = detector.findHands(img, detectWidth=DETECT_WIDTH)
    lmList = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        x1, y1 = lmList[4][1], lmList[4][2]   # thumb tip
        x2, y2 = lmList[8][1], lmList[8][2]   # index tip
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        length = math.hypot(x2 - x1, y2 - y1)

        # Hand size = wrist (0) to index knuckle (5).
        # Dividing by it makes the result independent of camera distance.
        handSize = math.hypot(lmList[5][1] - lmList[0][1],
                              lmList[5][2] - lmList[0][2])

        if handSize > 0:
            ratio = length / handSize
            if DEBUG:
                print(f"ratio: {ratio:.2f}")

            target = np.interp(ratio, [MIN_RATIO, MAX_RATIO], [0, 100])
            volper = SMOOTHING * volper + (1 - SMOOTHING) * target
            volume.SetMasterVolumeLevelScalar(volper / 100, None)

            # Fingertip visuals, colored by the current level
            col = level_color(volper)
            cv2.line(img, (x1, y1), (x2, y2), col, 4, cv2.LINE_AA)
            for p in ((x1, y1), (x2, y2)):
                cv2.circle(img, p, 14, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.circle(img, p, 11, col, -1, cv2.LINE_AA)
            cv2.circle(img, (cx, cy), 8,
                       (255, 0, 255) if volper < 2 else (255, 255, 255),
                       -1, cv2.LINE_AA)

    draw_volume_panel(img, volper)

    # FPS (smoothed) + hint
    cTime = time.time()
    if cTime != pTime:
        fps = 0.9 * fps + 0.1 * (1 / (cTime - pTime))
    pTime = cTime
    shadow_text(img, f"FPS {int(fps)}", (W - 150, 40), 0.8, (255, 255, 255), 1)
    shadow_text(img, "Press Q to quit", (20, H - 20), 0.55, (220, 220, 220), 1)

    cv2.imshow("Hand Volume Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):   # press q to quit
        break

cap.release()
cv2.destroyAllWindows()
