# 🧠 VisionX

> **"Jarvis for Vision"** — A system that doesn't just see. It understands, decides, and acts.

**VisionX** is a distributed AI vision platform. It runs on any device — from Raspberry Pi to cloud GPUs. It detects objects, tracks them, evaluates rules, checks each action against a privacy policy, and then acts.

**191 tests passing · edge-first architecture · governance-gated actions**

> ### ⚠️ Project status: pre-production prototype
>
> The vision pipeline (detect → track → decide → govern → act) works and is tested.
> The SaaS platform around it does **not** yet exist: **no database schema, no
> multi-tenancy, no object storage, no durable job queue.** Nothing survives a restart.
>
> **Do not deploy this to production.** See **[MASTER_BLUEPRINT.md](MASTER_BLUEPRINT.md)**
> for what is actually built, **[ENGINEERING_REVIEW.md](ENGINEERING_REVIEW.md)**
> for the independent audit (verdict: 🟠 Requires Major Redesign), and
> **[EXECUTION_TRACKER.md](EXECUTION_TRACKER.md)** for every known defect and its status.

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
python -m pytest tests/ -v      # Run tests (191 passing)
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
├── tests/                        # 191 tests (pytest, incl. HTTP + WebSocket)
├── EXECUTION_RULES.md            # Binding rules for every change
├── EXECUTION_TRACKER.md          # Defect log + run log
├── MASTER_BLUEPRINT.md           # What is actually built
├── ENGINEERING_REVIEW.md         # Independent audit
├── implementation_plan.md        # 72-section vision doc (non-binding)
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

A capability counts as **Done** only if it is *reachable* from the UI or a mounted
route, *durable* across a restart, and *tested* through its real interface.

| Capability | Status | Notes |
|---|---|---|
| Edge pipeline (detect · track · ROI · count) | ✅ Done | Tested |
| Decision engine (rules · cooldown · priority) | ✅ Done | Tested |
| Governance gate (privacy · consent · confidence) | ✅ Done | Tested |
| Auth (bcrypt · JWT fail-closed · token types) | ✅ Done | Tested |
| REST API (12 routers mounted) | ✅ Reachable | Data is volatile |
| WebSocket live feed (`/ws/vision`) | ✅ Done | Tested over real socket |
| React dashboard | 🟡 Partial | Blocked by backend gaps |
| Event dispatch (email · webhook) | 🟡 Partial | Retries 3× with backoff, then dead-letters — **queue is in-memory, lost on restart** |
| Sync layer (outbox) | 🟡 Partial | Transport stubbed |
| Event history API (`/api/v1/events`) | ⬜ Not built | Returns `501` — never a fake empty result |
| **Persistence (Postgres schema)** | ⬜ Not built | **Blocking for V1** |
| **Multi-tenancy (`org_id` + RLS)** | ⬜ Not built | **Blocking for V1** |
| **Object storage + clip capture** | ⬜ Not built | **Blocking for V1** |
| **Durable action queue (survives restart)** | ⬜ Not built | **Blocking for V1** — retry exists, durability does not |
| Camera onboarding UX | ⬜ Not built | The activation bottleneck |
| Landing page · signup · login UI | ⬜ Not built | No acquisition surface |
| Billing · notifications · usage | 🔵 Deferred | Code exists; post-validation |

Ordered plan with dependencies: **[MASTER_BLUEPRINT.md](MASTER_BLUEPRINT.md) → Development Roadmap**.

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Detection** | YOLOv8 (Ultralytics) — ⚠️ AGPL-3.0, see License below |
| **Vision** | OpenCV, NumPy |
| **Backend** | FastAPI, Pydantic, Loguru |
| **Database** | PostgreSQL, Redis *(connection stubs — no schema yet)* |
| **Auth** | JWT (PyJWT), bcrypt, RBAC |
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

All four gates must pass before any commit:

```bash
python -m pytest tests/ -q                      # 191 tests
ruff check . --select E,W,F --ignore E501       # backend lint
cd client && npx tsc --noEmit                   # frontend types
cd client && npm run build                      # production build
```

Rules governing every change: **[EXECUTION_RULES.md](EXECUTION_RULES.md)**.
Known defects and their status: **[EXECUTION_TRACKER.md](EXECUTION_TRACKER.md)**.

---

## 📄 License

VisionX source is MIT — see [LICENSE](LICENSE).

> ⚠️ **Unresolved dependency licensing.** Ultralytics YOLOv8 is **AGPL-3.0**, which is
> incompatible with closed-source commercial distribution. Before any commercial use,
> either obtain an Ultralytics commercial licence or migrate to a permissively-licensed
> detector. Tracked in [ENGINEERING_REVIEW.md](ENGINEERING_REVIEW.md) §10.5.

---

*VisionX — Detect. Understand. Decide. Act.* 🧠🔥
