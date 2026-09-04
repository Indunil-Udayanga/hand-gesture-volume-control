# Hand Gesture Volume Controller ✋🔊

Control your system's volume in real time using hand gestures, powered by computer vision. Pinch your thumb and index finger together or apart to lower or raise the volume — no mouse, no keyboard, just your hand in front of the webcam.

## Demo

The distance between your **thumb tip** and **index finger tip** is mapped to the system volume:
- 🤏 Fingers close together → Volume down
- ✋ Fingers far apart → Volume up

## Features

- Real-time hand tracking using your webcam
- 21-point hand landmark detection
- Live FPS counter overlay
- Visual volume bar and percentage display
- Reusable, class-based hand tracking module for other projects

## Tech Stack

| Library | Purpose |
|---|---|
| [OpenCV](https://opencv.org/) | Video capture, image processing, and drawing overlays |
| [MediaPipe](https://developers.google.com/mediapipe) | Hand landmark detection |
| [NumPy](https://numpy.org/) | Interpolating hand distance to volume range |
| [pycaw](https://github.com/AndreMiras/pycaw) | Controlling Windows system audio |
| [comtypes](https://pypi.org/project/comtypes/) | COM interface support required by pycaw |

## Project Structure

```
├── HandTrackingMin.py        # Minimal script: raw MediaPipe hand detection test
├── HandTrackingModule.py     # Reusable handDetector class (core module)
├── VolumeHandControl.py      # Main project: gesture-based volume control
├── VolumeHandControlMin.py   # Simplified version using the module (no volume logic)
└── README.md
```

### File Overview

- **`HandTrackingModule.py`** — Defines the `handDetector` class, which wraps MediaPipe's hands solution. It exposes:
  - `findHands(img, draw=True)` — detects hands and optionally draws landmarks/connections
  - `findPosition(img, handNo=0, draw=True)` — returns a list of `[id, x, y]` landmark positions for a given hand

- **`VolumeHandControl.py`** — The main application. It:
  1. Captures webcam video
  2. Detects the hand and locates landmark `4` (thumb tip) and `8` (index fingertip)
  3. Calculates the distance between them
  4. Maps that distance to a volume percentage using `np.interp`
  5. Sets the system's master volume via `pycaw`
  6. Displays a live volume bar, percentage, and FPS on screen

- **`HandTrackingMin.py`** / **`VolumeHandControlMin.py`** — Lightweight/testing scripts used during development to verify tracking and FPS before adding the module and volume logic.

## Requirements

- Python 3.7–3.10 (MediaPipe compatibility varies by version)
- **Windows OS** (required for `pycaw`, since it uses the Windows Core Audio API)
- A working webcam

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/hand-gesture-volume-control.git
   cd hand-gesture-volume-control
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install opencv-python mediapipe numpy pycaw comtypes
   ```

## Usage

Run the main volume control script:
```bash
python VolumeHandControl.py
```

- Show your hand to the webcam.
- Pinch your **thumb** and **index finger** together to decrease volume; spread them apart to increase it.
- Press any key or close the window to stop (add a proper quit condition like `q` key handling if desired).

To test just the hand tracking module on its own:
```bash
python HandTrackingModule.py
```

## How It Works

1. **Capture** — OpenCV grabs frames from the webcam.
2. **Detect** — Each frame is converted to RGB and passed to MediaPipe's `Hands` solution, which returns 21 landmarks per detected hand.
3. **Locate** — Landmark `4` (thumb tip) and landmark `8` (index fingertip) are extracted as pixel coordinates.
4. **Measure** — The Euclidean distance between the two points is calculated using `math.hypot`.
5. **Map** — `np.interp` scales that pixel distance (roughly 50–220 px) to a volume percentage (0–100%).
6. **Control** — `pycaw` sets the system's master volume to match, in real time.

## Known Limitations / Ideas for Improvement

- Currently Windows-only due to `pycaw`; cross-platform audio control would require a different library per OS.
- No hand-presence smoothing — volume can jitter slightly at gesture boundaries; adding a smoothing/debounce filter would help.
- No exit key handling (`cv2.waitKey(1)` doesn't check for a quit key) — consider adding `if cv2.waitKey(1) & 0xFF == ord('q'): break`.
- Only tracks one hand for volume control even if two are detected.

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements

Built using Google's [MediaPipe](https://developers.google.com/mediapipe) hand tracking solution and inspired by common OpenCV/MediaPipe gesture-control tutorials.
