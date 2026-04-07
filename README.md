# 🧠 VisionX

> **"Jarvis for Vision"** — A system that doesn't just see. It understands, decides, and acts.

**VisionX** is a distributed AI vision platform that runs on any device — from Raspberry Pi to cloud GPUs. It detects objects, tracks them, makes decisions, and triggers actions automatically.

---

## ✨ What Makes VisionX Different

| Others | VisionX |
|--------|---------|
| ❌ Detect only | ✅ **Detect** → Understand → Decide → Act |
| ❌ Single system | ✅ Runs **everywhere** (edge + cloud) |
| ❌ No intelligence | ✅ Rule-based **decision engine** |
| ❌ No automation | ✅ Full **event-action system** (Jarvis Mode) |
| ❌ No multi-device | ✅ **Cross-camera** tracking & sync |

---

## 🏗️ Architecture

```
Camera (CCTV / Mobile / Webcam)
   ↓
Edge AI (fast detection + tracking)
   ↓
Important data → Sync Layer → Cloud
   ↓
Cloud AI (deep analysis: face, OCR, analytics)
   ↓
Decision Engine (rule evaluation)
   ↓
Event Engine (trigger actions)
   ↓
User Dashboard / API / Alerts / IoT / Webhook
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Webcam (or video file / RTSP stream)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/visionx.git
cd visionx

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
# Run with webcam (default)
python -m edge.core.pipeline

# Run with video file
python -m edge.core.pipeline --source path/to/video.mp4

# Run with RTSP stream
python -m edge.core.pipeline --source "rtsp://user:pass@ip:554/stream"

# Run in Lite mode (for low-power devices)
python -m edge.core.pipeline --mode lite
```

### Controls

| Key | Action |
|-----|--------|
| `q` | Quit |
| `r` | Reset tracking |
| `X` | Close window |

### Run Tests

```bash
python -m pytest tests/ -v
```

---

## 📁 Project Structure

```
visionx/
├── edge/                      # Runs on devices (local AI)
│   ├── core/
│   │   ├── camera.py          # Camera input (webcam, RTSP, IP, file)
│   │   ├── pipeline.py        # Master processing pipeline
│   │   ├── preprocessor.py    # CLAHE, noise reduction, resize
│   │   ├── tracker.py         # IoU tracking, velocity prediction
│   │   └── threading_engine.py# Multi-threaded capture/process/output
│   ├── modules/
│   │   ├── detection.py       # YOLO object detection
│   │   ├── tracking.py        # Tracking module with direction
│   │   ├── counting.py        # Object counting (global, zone, line)
│   │   └── measurement.py     # Distance & area estimation
│   ├── roi/
│   │   └── roi_engine.py      # Region of Interest management
│   └── config/
│       └── edge_config.py     # Performance modes (Lite/Balanced/Max)
│
├── shared/                    # Common logic across layers
│   ├── constants.py           # System-wide constants
│   └── models.py              # Pydantic data models
│
├── visualization/             # Visualization utilities
│   └── overlay.py             # Bounding boxes, IDs, labels, FPS
│
├── tests/                     # Unit tests
│   ├── test_detection.py
│   └── test_tracking.py
│
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚙️ Performance Modes

| Mode | Use Case | Input Size | Frame Skip | Precision |
|------|----------|-----------|------------|-----------|
| **Lite** | Mobile, Raspberry Pi | 320px | Skip 2 | INT8 |
| **Balanced** | Laptop, Desktop | 640px | None | FP16 |
| **Max** | Cloud GPU, Jetson AGX | 1280px | None | FP32 |

---

## 🗺️ Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Edge Engine Foundation | ✅ Complete |
| **Phase 2** | Intelligence (Decision + Event Engine) | ⬜ Planned |
| **Phase 3** | Platform (FastAPI + Auth + DB) | ⬜ Planned |
| **Phase 4** | Premium UI (React + Glassmorphism) | ⬜ Planned |
| **Phase 5** | 3D Characters & AI Avatars | ⬜ Planned |
| **Phase 6** | Sync & Multi-Device | ⬜ Planned |
| **Phase 7** | Hardening & Polish | ⬜ Planned |
| **Phase 8** | Global Deployment | ⬜ Planned |

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Detection** | YOLOv8 (Ultralytics) |
| **Vision** | OpenCV |
| **Models** | Pydantic |
| **Backend** | FastAPI (planned) |
| **Database** | PostgreSQL + Redis (planned) |
| **Frontend** | React + Three.js (planned) |
| **Deployment** | Docker (planned) |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*VisionX — Detect. Understand. Decide. Act.* 🧠🔥
