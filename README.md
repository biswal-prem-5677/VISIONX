# 🧠 VisionX

> **"Jarvis for Vision"** — A system that doesn't just see. It understands, decides, and acts.

**VisionX** is a production-grade distributed AI vision platform. It runs on any device — from Raspberry Pi to cloud GPUs. It detects objects, tracks them across cameras, makes autonomous decisions, and triggers actions automatically.

**72-section architecture · 95 tests passing · 5 visual themes · 3D AI characters**

---

## ✨ What Makes VisionX Different

| Others | VisionX |
|--------|---------|
| ❌ Detect only | ✅ **Detect** → Understand → Decide → Act |
| ❌ Single system | ✅ Runs **everywhere** (edge + cloud) |
| ❌ No intelligence | ✅ Rule-based **decision engine** + governance |
| ❌ No automation | ✅ Full **event-action system** (Jarvis Mode) |
| ❌ No multi-device | ✅ **Cross-camera** tracking & sync |
| ❌ Basic UI | ✅ Premium **glassmorphism** + 3D characters |
| ❌ No offline | ✅ Offline-first with **durable buffering** |

---

## 🏗️ Architecture

```
Camera (CCTV / Mobile / Webcam / RTSP)
   ↓
Edge AI (YOLO detection + tracking + counting)
   ↓
Sync Layer (offline buffer → cloud sync)
   ↓
Cloud AI (face recognition, OCR, pose, analytics)
   ↓
Decision Engine (rule evaluation → governance check)
   ↓
Event Engine (email, webhook, IoT, push, alarm)
   ↓
Dashboard (React + Three.js + 3D AI Character)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ · Node.js 22+ · Git

### Backend

```bash
git clone https://github.com/biswal-prem-5677/VISIONX.git
cd VISIONX
python -m venv .venv
.\.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -m pytest tests/ -v      # Run tests (95 passing)
```

### Frontend

```bash
cd client
npm install
npm run dev                     # http://localhost:5173
```

### Docker (Full Stack)

```bash
cd docker
docker-compose up -d           # Starts all services
# Client: http://localhost:3000
# API:    http://localhost:8000
# PgSQL:  localhost:5432
# Redis:  localhost:6379
```

---

## 📁 Project Structure

```
VISIONX/
├── edge/                         # Edge AI (runs on device)
│   ├── core/
│   │   ├── pipeline.py           # Master processing pipeline
│   │   ├── camera.py             # Camera input (webcam, RTSP, IP)
│   │   ├── preprocessor.py       # CLAHE, noise reduction
│   │   ├── tracker.py            # Kalman filter tracking
│   │   ├── multi_pipeline.py     # Multi-camera multiplexer
│   │   └── cross_camera_tracker.py # Cross-camera re-ID
│   ├── modules/
│   │   ├── detection.py          # YOLOv8 object detection
│   │   ├── counting.py           # Person/object counting
│   │   ├── heatmap.py            # Spatial heatmaps
│   │   └── measurement.py        # Distance estimation
│   └── config/
│       └── edge_config.py        # Lite / Balanced / Max modes
│
├── cloud/                        # Cloud AI modules
│   ├── analytics/engine.py       # Analytics engine
│   ├── modules/                  # Face, OCR, Pose, Segmentation
│   └── ai/
│       └── model_manager.py      # Model registry & hot-swap
│
├── decision/                     # Decision engine
│   ├── engine.py                 # Rule evaluation (284 lines)
│   └── rules.py                  # Rule definitions
│
├── events/                       # Event + action system
│   ├── event_engine.py           # Core event dispatching
│   ├── actions/                  # Email, webhook, API, IoT, hardware
│   └── templates/                # Pre-built event rules
│
├── sync/                         # Sync & device management
│   ├── sync_engine.py            # Edge↔Cloud sync (outbox pattern)
│   ├── device_manager.py         # Fleet management + heartbeat
│   └── offline_buffer.py         # Durable offline queue (WAL)
│
├── server/                       # FastAPI backend
│   ├── api/
│   │   ├── main.py               # FastAPI app
│   │   ├── routes/               # Auth, events, analytics, GDPR, etc.
│   │   └── middleware/           # CORS, rate limit, auth, abuse detection
│   ├── auth/                     # JWT + OAuth2 + RBAC
│   ├── billing/                  # Stripe + plan definitions
│   ├── notifications/            # Push, email, SMS, in-app channels
│   ├── admin/                    # User mgmt, health, remote config
│   └── observability/            # Sentry + PostHog integration
│
├── client/                       # React + Vite frontend
│   ├── src/
│   │   ├── pages/                # 7 pages (Dashboard, Analytics, etc.)
│   │   ├── components/
│   │   │   ├── 3d/               # Three.js scene + AI characters
│   │   │   ├── ui/               # GlassCard, GlowButton, TiltCard
│   │   │   ├── monitoring/       # LiveFeed, BoundingBoxes
│   │   │   └── ...               # Admin, analytics, notifications
│   │   ├── stores/               # 8 Zustand stores
│   │   └── hooks/                # 9 custom hooks
│   └── public/
│       └── sw.js                 # Service Worker (offline + push)
│
├── docker/                       # Docker deployment
│   ├── Dockerfile.edge
│   ├── Dockerfile.server
│   ├── Dockerfile.client
│   ├── docker-compose.yml        # Full stack: client + API + edge + PG + Redis
│   └── nginx.conf                # Production Nginx config
│
├── .github/workflows/ci.yml     # GitHub Actions CI/CD
├── tests/                        # 95 tests (pytest)
├── implementation_plan.md        # 72-section master blueprint
└── README.md
```

---

## 🎨 5 Visual Themes

| Theme | Colors | 3D Character |
|-------|--------|-------------|
| **Obsidian** | Deep purple | The Guardian — stoic, shield fragments |
| **Cyber Neon** | Cyan glow | The Muse — ethereal, holographic rings |
| **Aurora** | Northern blue | The Guide — energetic, floating orbs |
| **Ember** | Fire orange | The Pilot — tech visor, gears |
| **Matrix** | Digital green | The Sage — meditative, green aura |

---

## ⚙️ Performance Modes

| Mode | Use Case | Input Size | Precision |
|------|----------|-----------|-----------|
| **Lite** | RPi, Mobile | 320px | INT8 |
| **Balanced** | Laptop, Desktop | 640px | FP16 |
| **Max** | Cloud GPU, Jetson | 1280px | FP32 |

---

## 🗺️ Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Edge Engine Foundation | ✅ Complete |
| **Phase 2** | Event & Decision Engine | ✅ Complete |
| **Phase 3** | Platform (FastAPI + Auth + DB) | ✅ Complete |
| **Phase 4** | Premium UI (React + Glassmorphism) | ✅ Complete |
| **Phase 5** | 3D Characters & AI Avatars | ✅ Complete |
| **Phase 6** | Sync & Multi-Device | ✅ Complete |
| **Phase 7** | Hardening & Polish | ✅ Complete |
| **Phase 8** | Global Deployment | ⬜ Next |
| **Phase 9** | Intelligence Domains | ⬜ Planned |
| **Phase 10** | MLOps & AI Agent | ⬜ Planned |

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Detection** | YOLOv8 (Ultralytics) |
| **Vision** | OpenCV, NumPy |
| **Backend** | FastAPI, Pydantic, Loguru |
| **Database** | PostgreSQL, Redis, Pinecone |
| **Auth** | JWT (PyJWT), OAuth2, RBAC |
| **Frontend** | React 19, Vite 8, TypeScript |
| **3D** | Three.js, React Three Fiber, Drei |
| **State** | Zustand (persisted) |
| **Billing** | Stripe |
| **Notifications** | Resend (email), Twilio (SMS), Web Push |
| **Observability** | Sentry, PostHog |
| **Deployment** | Docker, Nginx, GitHub Actions |
| **GDPR** | Data export, erasure, consent endpoints |

---

## 🧪 Testing

```bash
# Python backend (95 tests)
python -m pytest tests/ -v

# Frontend type-check
cd client && npx tsc --noEmit

# Frontend production build
cd client && npm run build
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*VisionX — Detect. Understand. Decide. Act.* 🧠🔥
