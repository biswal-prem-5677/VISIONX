# 🧠 VisionX — Master Implementation Plan

> **"Jarvis for Vision"** — A system that doesn't just see. It understands, decides, and acts.

---

## Table of Contents — Build Status

> ✅ = Code exists & implemented | ⚠️ = Partial/stub | ❌ = Not started | 📋 = Design only (no code needed)

1. [System Identity](#1-system-identity) 📋
2. [Architecture Overview](#2-architecture-overview) 📋
3. [Directory Structure](#3-directory-structure) ✅ BUILT
4. [Layer-by-Layer Design](#4-layer-by-layer-design) ✅ ALL 6 LAYERS BUILT
5. [AI Pipeline (Master Pipeline)](#5-ai-pipeline-master-pipeline) ✅ `edge/core/pipeline.py`
6. [Complete Feature Set](#6-complete-feature-set) ✅ ALL MODULES BUILT
7. [User Experience — 4 Modes](#7-user-experience--4-modes) ✅ 7 PAGES BUILT
8. [Premium Spatial UI](#8-premium-spatial-ui) ✅ Glass + 3D + all components built
9. [5 Visual Themes (Modes)](#9-5-visual-themes-modes) ✅ CSS + Store done
10. [3D Characters & AI Avatars](#10-3d-characters--ai-avatars) ❌ Not started
11. [Security (Zero Trust)](#11-security-zero-trust) ✅ JWT, RBAC, OAuth built
12. [Anti-Abuse & Misuse Prevention](#12-anti-abuse--misuse-prevention) ✅ `abuse_detector.py`
13. [Scalability & Reliability](#13-scalability--reliability) 📋
14. [Observability & Monitoring](#14-observability--monitoring) ⚠️ Design only
15. [Crash Resilience & Recovery](#15-crash-resilience--recovery) ✅ Backend + CrashBoundary built
16. [State Recovery & Session Continuity](#16-state-recovery--session-continuity) ✅ Zustand persist + useStateRecovery built
17. [Offline-First Architecture](#17-offline-first-architecture) ⚠️ Hooks + banner built, no Service Worker yet
18. [Data Persistence & Reinstall Recovery](#18-data-persistence--reinstall-recovery) 📋 Design only
19. [Privacy, Cookies & Compliance](#19-privacy-cookies--compliance) ✅ CookieBanner built
20. [Monetization System](#20-monetization-system) ✅ Stripe + Feature gates built
21. [Data Architecture](#21-data-architecture) ✅ Postgres + Redis + Pinecone built
22. [Integration Layer](#22-integration-layer) ✅ All 4 action types built
23. [Jarvis-Level Capabilities](#23-jarvis-level-capabilities) ✅ Decision + Event engines built
24. [Help Center & User Support](#24-help-center--user-support) ✅ Backend + Frontend built
25. [Notification Service (Full System)](#25-notification-service-full-system) ⚠️ Engine built, channels stub only
26. [Admin Dashboard (God Mode)](#26-admin-dashboard-god-mode) ✅ Backend + Frontend built
27. [Feature Usage Tracking & Analytics](#27-feature-usage-tracking--analytics) ✅ Backend built
28. [User Dashboard (Separate from Admin)](#28-user-dashboard-separate-from-admin) ✅ Backend + Frontend built
29. [Device Ecosystem & Deployment](#29-device-ecosystem--deployment) ❌ No Docker yet
30. [Performance Engineering](#30-performance-engineering) ⚠️ Config done, profiling not done
31. [Pre-Production Checklist](#31-pre-production-checklist) ❌ Not executed yet
32. [Phased Execution Roadmap](#32-phased-execution-roadmap) 📋
33. [Verification Plan](#33-verification-plan) ✅ Test files exist
34. [Open Questions](#34-open-questions) 📋

---

## 1. System Identity

| Attribute | Value |
|---|---|
| **Product Name** | VisionX |
| **Tagline** | "Write once → Run everywhere → Scale infinitely" |
| **Core Identity** | Distributed AI Vision Platform · SaaS Product · Vision Operating System |
| **What it does** | Detect → Understand → Decide → Act |
| **Competitors it matches** | Cognex, SenseTime (in concept and ambition) |

### What Makes VisionX Different

| Others | VisionX |
|---|---|
| ❌ Detect only | ✅ Detect |
| ❌ No intelligence | ✅ Understand |
| ❌ No action | ✅ Decide |
| ❌ Single system only | ✅ Act |
| ❌ No edge/cloud split | ✅ Runs everywhere |
| ❌ No multi-device support | ✅ Edge + Cloud hybrid |
| | ✅ Scalable globally |

---

## 2. Architecture Overview

### The 5-Layer Distributed Architecture

This **replaces** any single-system architecture. VisionX is built as a distributed, device-agnostic platform from day one.

```
┌─────────────────────────────────────────────────────────────┐
│                    1. DEVICE LAYER                          │
│         Mobile · CCTV · Desktop · Webcam · IP Cam          │
│              (Camera input, local UI)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. EDGE ENGINE                             │
│          Local AI Processing (ultra-low latency)            │
│     Detection · Tracking · Basic Alerts · Preprocessing    │
│         OpenCV · ONNX Runtime · TensorRT                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 3. SYNC LAYER                               │
│        Edge ↔ Cloud Communication                          │
│    Data Streaming · Model Updates · Event Syncing          │
│    Buffering · Retries · Offline→Online Recovery           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               4. CLOUD AI ENGINE                            │
│       Heavy Processing (server-side)                        │
│   Face Recognition · OCR · Analytics · Learning            │
│   Decision Engine · Event Engine                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            5. PLATFORM SERVICES                             │
│    API (FastAPI) · Database · Auth · Billing               │
│    Notification Service · Analytics Service                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               6. CLIENT LAYER                               │
│        Dashboard · Mobile App · Config UI                  │
│    React + Three.js + Glassmorphism · WebSockets           │
└─────────────────────────────────────────────────────────────┘
```

### System Data Flow (Global)

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

### Connectivity Map

```
Detection ──→ Tracking ──→ Counting
Detection ──→ OCR ──→ Text Output
Detection ──→ Face ──→ Identity Match
Tracking ──→ Behavior ──→ Decision
Decision ──→ Event ──→ Action
```

---

## 3. Directory Structure

This is the **final** module placement — organized by deployment layer, not by feature.

```
visionx/
│
├── edge/                          # Runs on devices (local AI)
│   ├── core/
│   │   ├── camera.py              # Camera input (webcam, RTSP, IP, file)
│   │   ├── pipeline.py            # Master processing pipeline
│   │   ├── preprocessor.py        # CLAHE, noise reduction, edge detection
│   │   ├── tracker.py             # ID assignment, movement tracking, occlusion
│   │   └── threading_engine.py    # Capture / Processing / Output threads
│   │
│   ├── modules/
│   │   ├── detection.py           # YOLO object detection
│   │   ├── tracking.py            # DeepSORT / ByteTrack
│   │   ├── counting.py            # People & object counting
│   │   └── measurement.py         # Distance & area estimation
│   │
│   ├── roi/
│   │   └── roi_engine.py          # Region of Interest management
│   │
│   └── config/
│       └── edge_config.py         # Performance modes (Lite/Balanced/Max)
│
├── cloud/                         # Runs on server (heavy AI)
│   ├── modules/
│   │   ├── face.py                # Face recognition + database matching
│   │   ├── ocr.py                 # Text/plate/document reading
│   │   ├── pose.py                # Skeleton + action recognition
│   │   ├── segmentation.py        # Pixel-level object understanding
│   │   ├── speed.py               # Object movement speed estimation
│   │   └── behavior.py            # Loitering, suspicious movement
│   │
│   ├── analytics/
│   │   ├── engine.py              # Analytics aggregation
│   │   ├── heatmaps.py            # Spatial heatmap generation
│   │   └── reports.py             # Report generation
│   │
│   └── ai/
│       ├── model_manager.py       # Model versioning, remote updates
│       └── embeddings.py          # Embedding generation & storage
│
├── decision/                      # Intelligence layer
│   ├── engine.py                  # Rule evaluation engine
│   └── rules.py                   # Rule definitions & templates
│
├── events/                        # Jarvis Core — action trigger system
│   ├── event_engine.py            # Event processing & dispatch
│   ├── actions/
│   │   ├── email.py               # Email via Resend
│   │   ├── webhook.py             # External webhook calls
│   │   ├── api_call.py            # REST API triggers
│   │   ├── iot.py                 # IoT device signals
│   │   ├── notification.py        # Push notifications
│   │   └── hardware.py            # Buzzer, PLC, relay triggers
│   └── templates/
│       └── event_templates.py     # Pre-built event templates
│
├── sync/                          # Edge ↔ Cloud communication
│   ├── sync_engine.py             # Streaming, buffering, retries
│   ├── device_manager.py          # Device registration & tracking
│   └── offline_buffer.py          # Offline → online recovery queue
│
├── platform/                      # Backend services
│   ├── api/
│   │   ├── main.py                # FastAPI application entry
│   │   ├── routes/
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── vision.py          # Vision processing endpoints
│   │   │   ├── events.py          # Event management endpoints
│   │   │   ├── analytics.py       # Analytics endpoints
│   │   │   ├── config.py          # Configuration endpoints
│   │   │   ├── devices.py         # Device management endpoints
│   │   │   ├── billing.py         # Subscription/billing endpoints
│   │   │   ├── admin.py           # ⭐ Admin god-mode endpoints
│   │   │   ├── help.py            # ⭐ Help center / support endpoints
│   │   │   ├── notifications.py   # ⭐ Notification management endpoints
│   │   │   └── usage_tracking.py  # ⭐ Feature usage analytics endpoints
│   │   ├── middleware/
│   │   │   ├── auth_middleware.py  # JWT verification
│   │   │   ├── rate_limiter.py    # Redis-based rate limiting
│   │   │   ├── abuse_detector.py  # ⭐ Anti-abuse / misuse detection
│   │   │   └── cors.py            # CORS configuration
│   │   └── websockets/
│   │       └── live_feed.py       # Real-time WebSocket streaming
│   │
│   ├── auth/
│   │   ├── jwt_handler.py         # JWT token management
│   │   ├── oauth.py               # OAuth2 providers
│   │   ├── device_auth.py         # Device token authentication
│   │   ├── rbac.py                # Role-based access control
│   │   └── admin_takeover.py      # ⭐ Admin impersonation (audit-logged)
│   │
│   ├── billing/
│   │   ├── stripe_service.py      # Stripe integration
│   │   ├── plans.py               # Subscription plan definitions
│   │   └── feature_gates.py       # Feature gating logic
│   │
│   ├── admin/                         # ⭐ Admin subsystem
│   │   ├── dashboard_service.py       # Admin dashboard data aggregation
│   │   ├── user_management.py         # User CRUD, ban, restrict, impersonate
│   │   ├── system_health.py           # System-wide health monitoring
│   │   └── remote_config.py           # Push config changes to all users
│   │
│   ├── notifications/                 # ⭐ Notification subsystem
│   │   ├── notification_engine.py     # Central notification dispatcher
│   │   ├── channels/
│   │   │   ├── push.py                # Web push / mobile push
│   │   │   ├── email.py               # Email via Resend
│   │   │   ├── in_app.py              # In-app notification bell
│   │   │   └── sms.py                 # SMS (Twilio)
│   │   └── templates.py              # Notification templates
│   │
│   ├── crash_reporting/               # ⭐ Crash resilience subsystem
│   │   ├── crash_collector.py         # Collect crash reports from clients
│   │   ├── crash_analyzer.py          # Aggregate & prioritize crashes
│   │   └── auto_recovery.py           # State snapshot & recovery logic
│   │
│   ├── usage_tracking/                # ⭐ Feature usage analytics
│   │   ├── tracker.py                 # Track every feature interaction
│   │   ├── aggregator.py              # Aggregate by feature/location/time
│   │   └── reports.py                 # Usage reports for admin
│   │
│   ├── help/                          # ⭐ Help & support system
│   │   ├── knowledge_base.py          # FAQ, guides, articles
│   │   ├── ticket_system.py           # Support ticket CRUD
│   │   ├── live_chat.py               # Real-time support chat
│   │   └── onboarding.py              # Interactive onboarding flows
│   │
│   └── db/
│       ├── postgres.py            # PostgreSQL connection & models
│       ├── redis_client.py        # Redis for real-time + caching
│       └── pinecone_client.py     # Pinecone for embeddings
│
├── client/                        # Frontend application
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css              # Global styles + CSS variables
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx        # Glassmorphic navigation sidebar
│   │   │   │   ├── Header.tsx         # Top bar with mode switcher
│   │   │   │   └── GlassPanel.tsx     # Reusable glass material component
│   │   │   │
│   │   │   ├── monitoring/
│   │   │   │   ├── LiveFeed.tsx       # Real-time camera feed display
│   │   │   │   ├── BoundingBoxes.tsx  # Detection overlay renderer
│   │   │   │   ├── AlertPanel.tsx     # Live alert notifications
│   │   │   │   └── StatusBar.tsx      # FPS, latency, connection status
│   │   │   │
│   │   │   ├── analytics/
│   │   │   │   ├── Charts.tsx         # Time-series graphs
│   │   │   │   ├── Heatmap.tsx        # Spatial heatmap viewer
│   │   │   │   ├── EventHistory.tsx   # Past event browser
│   │   │   │   └── CounterCards.tsx   # Object count displays
│   │   │   │
│   │   │   ├── config/
│   │   │   │   ├── ModuleToggles.tsx  # Enable/disable AI modules
│   │   │   │   ├── RuleBuilder.tsx    # Visual rule definition
│   │   │   │   ├── DeviceManager.tsx  # Camera/device management
│   │   │   │   └── PerformanceMode.tsx# Lite/Balanced/Max selector
│   │   │   │
│   │   │   ├── automation/
│   │   │   │   ├── AutomationBuilder.tsx  # "If this → do this" builder
│   │   │   │   ├── ActionSelector.tsx     # Choose action type
│   │   │   │   └── EventLog.tsx           # Automation execution log
│   │   │   │
│   │   │   ├── 3d/
│   │   │   │   ├── Scene.tsx          # React Three Fiber scene container
│   │   │   │   ├── Background.tsx     # Animated background (per theme)
│   │   │   │   ├── Character.tsx      # AI character component
│   │   │   │   ├── FloatingObjects.tsx# Ambient 3D objects
│   │   │   │   └── GazeTracker.tsx    # Cursor/gaze following logic
│   │   │   │
│   │   │   ├── admin/                     # ⭐ Admin dashboard components
│   │   │   │   ├── AdminOverview.tsx       # System-wide stats & health
│   │   │   │   ├── UserTable.tsx           # All users, search, filter, actions
│   │   │   │   ├── UserTakeover.tsx        # Impersonate user session (audit-logged)
│   │   │   │   ├── SystemHealth.tsx        # CPU, GPU, memory, API health
│   │   │   │   ├── CrashReports.tsx        # Crash log viewer & analyzer
│   │   │   │   ├── FeatureUsageMap.tsx     # Global feature usage heatmap
│   │   │   │   ├── RemoteConfig.tsx        # Push config/restrictions live
│   │   │   │   └── AbuseLog.tsx            # Suspicious activity log
│   │   │   │
│   │   │   ├── help/                      # ⭐ Help center components
│   │   │   │   ├── HelpSearch.tsx          # Searchable knowledge base
│   │   │   │   ├── ArticleViewer.tsx       # Help article renderer
│   │   │   │   ├── TicketForm.tsx          # Submit support ticket
│   │   │   │   ├── TicketList.tsx          # View ticket history
│   │   │   │   ├── LiveChat.tsx            # Real-time support chat widget
│   │   │   │   ├── OnboardingWizard.tsx    # Step-by-step onboarding
│   │   │   │   └── ContextualHelp.tsx      # "?" tooltips on every feature
│   │   │   │
│   │   │   ├── notifications/             # ⭐ Notification components
│   │   │   │   ├── NotificationBell.tsx    # Header bell with badge count
│   │   │   │   ├── NotificationPanel.tsx   # Dropdown notification list
│   │   │   │   ├── NotificationPrefs.tsx   # User notification preferences
│   │   │   │   └── NotificationToast.tsx   # Floating toast alerts
│   │   │   │
│   │   │   ├── offline/                   # ⭐ Offline UI components
│   │   │   │   ├── OfflineBanner.tsx       # "You are offline" indicator
│   │   │   │   ├── SyncStatus.tsx          # Sync progress indicator
│   │   │   │   └── OfflineFeatures.tsx     # Available offline features panel
│   │   │   │
│   │   │   ├── user-dashboard/            # ⭐ User-specific dashboard
│   │   │   │   ├── UserOverview.tsx        # Personal stats & quick actions
│   │   │   │   ├── MyDevices.tsx           # User's cameras & devices
│   │   │   │   ├── MyEvents.tsx            # User's event history
│   │   │   │   ├── UsageStats.tsx          # User's own feature usage
│   │   │   │   ├── AccountSettings.tsx     # Profile, security, preferences
│   │   │   │   └── BillingPanel.tsx        # Subscription & invoices
│   │   │   │
│   │   │   └── ui/
│   │   │       ├── GlassCard.tsx      # Glassmorphic card component
│   │   │       ├── GlowButton.tsx     # Glowing interactive button
│   │   │       ├── TiltCard.tsx       # Parallax hover tilt effect
│   │   │       ├── NeomorphicInput.tsx# Premium input fields
│   │   │       ├── CookieBanner.tsx   # GDPR cookie consent
│   │   │       ├── CrashBoundary.tsx  # ⭐ Error boundary + crash reporter
│   │   │       ├── LoadingState.tsx   # ⭐ Skeleton/shimmer loading
│   │   │       ├── EmptyState.tsx     # ⭐ No-data placeholder
│   │   │       └── ErrorState.tsx     # ⭐ Error fallback UI
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # MODE 1: Live Monitoring
│   │   │   ├── Analytics.tsx          # MODE 2: Analytics Dashboard
│   │   │   ├── Settings.tsx           # MODE 3: Configuration
│   │   │   ├── Automation.tsx         # MODE 4: Automation (Jarvis Mode)
│   │   │   ├── AdminDashboard.tsx     # ⭐ Admin god-mode page
│   │   │   ├── HelpCenter.tsx         # ⭐ Help & support page
│   │   │   └── UserHome.tsx           # ⭐ User personal dashboard page
│   │   │
│   │   ├── stores/
│   │   │   ├── themeStore.ts          # Zustand: 5 visual themes
│   │   │   ├── visionStore.ts         # Zustand: detection state
│   │   │   ├── eventStore.ts          # Zustand: event/alert state
│   │   │   ├── authStore.ts           # Zustand: auth state
│   │   │   ├── notificationStore.ts   # ⭐ Zustand: notifications state
│   │   │   ├── offlineStore.ts        # ⭐ Zustand: offline queue & sync state
│   │   │   └── crashStore.ts          # ⭐ Zustand: crash recovery state
│   │   │
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts        # Real-time data connection
│   │   │   ├── useHaptics.ts          # Web Haptics API integration
│   │   │   ├── useGaze.ts             # Cursor tracking for 3D
│   │   │   ├── useTheme.ts            # Theme switching logic
│   │   │   ├── useOffline.ts          # ⭐ Network status detection
│   │   │   ├── useCrashReporter.ts    # ⭐ Error capture & report
│   │   │   ├── useNotifications.ts    # ⭐ Notification subscription
│   │   │   └── useStateRecovery.ts    # ⭐ Auto-save/restore app state
│   │   │
│   │   ├── themes/
│   │   │   ├── midnight.ts            # Dark mode palette
│   │   │   ├── cloud.ts              # Light mode palette
│   │   │   ├── nebula.ts             # Creative mode palette
│   │   │   ├── forest.ts             # Focus mode palette
│   │   │   └── solar.ts              # Performance mode palette
│   │   │
│   │   └── utils/
│   │       ├── api.ts                 # API client
│   │       └── constants.ts           # App constants
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── visualization/                 # Shared visualization utils
│   └── overlay.py                 # Bounding boxes, IDs, labels, FPS
│
├── shared/                        # Common logic across edge & cloud
│   ├── models/                    # Data models & schemas
│   ├── utils/                     # Shared utilities
│   └── constants.py               # System constants
│
├── data/
│   ├── logs/                      # Event & system logs
│   ├── embeddings/                # Vector embeddings storage
│   └── media/                     # Captured images/video clips
│
├── docker/
│   ├── Dockerfile.edge            # Edge container
│   ├── Dockerfile.cloud           # Cloud container
│   ├── Dockerfile.platform        # Platform services container
│   └── docker-compose.yml         # Full system orchestration
│
├── tests/
│   ├── test_detection.py
│   ├── test_tracking.py
│   ├── test_pipeline.py
│   ├── test_decision.py
│   ├── test_events.py
│   └── test_api.py
│
├── requirements.txt               # Python dependencies
├── README.md
└── .env.example                   # Environment variables template
```

---

## 4. Layer-by-Layer Design

### 🟢 Layer 1: Device Layer

**Where it runs:** Mobile, CCTV, Laptop, Webcam, IP Camera

| Responsibility | Detail |
|---|---|
| Camera Input | Support webcam, RTSP, IP camera, video files |
| Frame Capture | Multi-threaded capture engine |
| Local UI | Lightweight display (bounding boxes, FPS) |
| Device Identity | Each device registers with unique token |

**Supported Sources:**
- USB Webcam → OpenCV `VideoCapture(0)`
- RTSP Stream → `VideoCapture("rtsp://...")`
- IP Camera → HTTP stream
- Video File → `VideoCapture("video.mp4")`
- Mobile Camera → Native camera SDK via Capacitor

---

### 🔵 Layer 2: Edge Engine

**Where it runs:** Locally on the device (laptop, Jetson, Raspberry Pi, mobile)

| Component | Purpose |
|---|---|
| `preprocessor.py` | CLAHE enhancement, noise reduction, edge detection |
| `detection.py` | YOLO object detection (person, car, phone, etc.) |
| `tracking.py` | Unique ID assignment, movement tracking, occlusion handling |
| `counting.py` | People count, object count per ROI |
| `measurement.py` | Distance estimation, area calculation |
| `roi_engine.py` | Focus processing on specific regions |
| `threading_engine.py` | Separate threads for capture, processing, output |

**Tech Stack:**
- OpenCV (capture + preprocessing)
- ONNX Runtime (cross-platform inference)
- TensorRT (GPU-accelerated on NVIDIA devices)
- YOLOv8/v9 (detection models)
- DeepSORT / ByteTrack (tracking)

**Performance Modes:**

| Mode | Use Case | Config |
|---|---|---|
| **Lite** | Mobile, Raspberry Pi | 320px input, skip frames, INT8 |
| **Balanced** | Laptop, Desktop | 640px input, every frame, FP16 |
| **Max** | Cloud GPU, Jetson AGX | 1280px input, batch inference, FP32 |

---

### 🟣 Layer 3: Sync Layer

**Purpose:** Edge ↔ Cloud communication bridge

| Component | Purpose |
|---|---|
| `sync_engine.py` | Data streaming, retries, compression |
| `device_manager.py` | Register devices, track active cameras, health checks |
| `offline_buffer.py` | Queue events when offline, sync when reconnected |

**Key Behaviors:**
- **Normal:** Real-time streaming of filtered events to cloud
- **Slow Connection:** Batch & compress, send summaries only
- **Offline:** Buffer all events locally, auto-sync on reconnection
- **Model Updates:** Cloud pushes updated models to edge devices

---

### 🟡 Layer 4: Cloud AI Engine

**Where it runs:** Server (AWS/GCP/self-hosted)

| Component | Purpose |
|---|---|
| `face.py` | Face recognition, database matching, blacklist/whitelist |
| `ocr.py` | Number plates, labels, documents, signage |
| `pose.py` | Human skeleton detection, action recognition |
| `segmentation.py` | Pixel-level object understanding |
| `speed.py` | Object movement speed estimation |
| `behavior.py` | Loitering detection, suspicious movement analysis |
| `model_manager.py` | Model versioning, A/B testing, remote deployment |
| `embeddings.py` | Generate and store vector embeddings (Pinecone) |

---

### 🔴 Layer 5: Platform Services

**Microservices Architecture:**

| Service | Responsibility |
|---|---|
| **Auth Service** | JWT/OAuth, device tokens, RBAC |
| **Vision Service** | AI processing API endpoints |
| **Tracking Service** | Real-time object tracking state |
| **Billing Service** | Stripe subscriptions, feature gating |
| **Notification Service** | Email (Resend), push, SMS |
| **Analytics Service** | Aggregation, reports, heatmaps |
| **Config Service** | Remote configuration, rule updates |

**Communication:**
- REST APIs (CRUD operations)
- WebSockets (real-time live feed, alerts)
- Event queues (async processing)

---

### 🌐 Layer 6: Client Layer

**See sections [8](#8-premium-spatial-ui), [9](#9-5-visual-themes-modes), [10](#10-3d-characters--ai-avatars) for full UI design.**

---

## 5. AI Pipeline (Master Pipeline)

The heart of VisionX. Every frame flows through this pipeline:

```
┌──────────────────┐
│   Camera Input   │  ← webcam / RTSP / IP / file / mobile
└────────┬─────────┘
         ▼
┌──────────────────┐
│  Preprocessing   │  ← CLAHE · noise reduction · edge detection
│     Engine       │
└────────┬─────────┘
         ▼
┌──────────────────┐
│    AI Engine     │  ← Detection / OCR / Face / Pose / Segmentation
│  (modular)       │     (only enabled modules run)
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Tracking Engine  │  ← Assign unique IDs · track movement · handle occlusion
└────────┬─────────┘
         ▼
┌──────────────────┐
│  Feature Layer   │  ← Count · Measure · Speed · Behavior analysis
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Decision Engine  │  ← Evaluate rules:
│                  │     IF person_count > 10 → crowd alert
│                  │     IF no helmet → violation
│                  │     IF face == blacklist → alarm
└────────┬─────────┘
         ▼
┌──────────────────┐
│  Event Engine    │  ← Trigger actions:
│  (JARVIS CORE)   │     Send email · Log to DB · Call API
│                  │     Trigger webhook · IoT signal · Buzzer
└────────┬─────────┘
         ▼
┌──────────────────┐
│  Output Layer    │  ← UI (bounding boxes, IDs, labels, FPS)
│                  │     API (JSON) · Logs · Dashboard
└──────────────────┘
```

### Edge vs Cloud Split

| Stage | Edge (local) | Cloud (server) |
|---|---|---|
| Preprocessing | ✅ | — |
| Detection | ✅ | ✅ (advanced) |
| Tracking | ✅ | — |
| OCR | — | ✅ |
| Face Recognition | — | ✅ |
| Pose Estimation | — | ✅ |
| Segmentation | — | ✅ |
| Counting | ✅ | — |
| Speed Estimation | ✅ | — |
| Behavior Analysis | — | ✅ |
| Decision Engine | ✅ (basic) | ✅ (full) |
| Event Engine | ✅ (basic) | ✅ (full) |

---

## 6. Complete Feature Set

### 👁️ A. Perception Layer

| # | Feature | Description | Location |
|---|---|---|---|
| 1 | **Object Detection** | YOLO detects person, car, phone, custom objects | Edge |
| 2 | **Tracking System** | Unique IDs, movement tracking, occlusion handling | Edge |
| 3 | **OCR (Text Vision)** | Read number plates, labels, documents | Cloud |
| 4 | **Face Recognition** | Identify people, match with database | Cloud |
| 5 | **Pose Estimation** | Human skeleton, action recognition | Cloud |
| 6 | **Segmentation** | Pixel-level object understanding | Cloud |

### ⚙️ B. Processing Layer

| # | Feature | Description |
|---|---|---|
| 1 | **Image Enhancement** | CLAHE, noise reduction, edge detection |
| 2 | **ROI Engine** | Focus only on important regions |
| 3 | **Multi-threading** | Capture thread, processing thread, output thread |

### 📏 C. Analytics Layer

| # | Feature | Description |
|---|---|---|
| 1 | **Counting** | People count, object count (per ROI, directional) |
| 2 | **Measurement** | Distance estimation, area calculation |
| 3 | **Speed Estimation** | Object movement speed (km/h or m/s) |
| 4 | **Behavior Analysis** | Loitering detection, suspicious movement |
| 5 | **Heatmaps** | Spatial activity density over time |

### 🧠 D. Intelligence Layer (Decision Engine)

**Rule Examples:**

| Condition | Action |
|---|---|
| `person_count > 10` | Crowd alert |
| `no helmet detected` | Safety violation |
| `face == blacklist` | Sound alarm |
| `object missing from zone` | Defect detection |
| `person in restricted area` | Intrusion alert |
| `loitering > 5 min` | Suspicious behavior |

### ⚡ E. Event Engine (Jarvis Core)

**Event Types:** Alert · Notification · Automation trigger · API call · Hardware signal

**Available Actions:**

| Action | Implementation |
|---|---|
| Send email | Resend API |
| Log to database | PostgreSQL insert |
| Call external API | HTTP request |
| Trigger webhook | POST to URL |
| Activate IoT device | MQTT/HTTP signal |
| Push notification | Web push / mobile push |
| Trigger buzzer/alarm | Serial/GPIO signal |
| Store image/clip | Save to cloud storage |

**Example Chain:**
```
Helmet missing detected
   → Send alert to supervisor (email)
   → Store violation image (cloud storage)
   → Trigger buzzer on site (IoT)
   → Log event with timestamp (database)
```

### 🌐 F. Output Layer

| Output | Detail |
|---|---|
| **Visualization** | Bounding boxes, IDs, labels, FPS overlay |
| **API** | JSON output via FastAPI for external integration |
| **Logs** | Events, history, captured images |
| **Dashboard** | Live feed, analytics, real-time alerts |

---

## 7. User Experience — 4 Modes

### 🟢 MODE 1 — Live Monitoring

**What the user sees:**
- Real-time camera feed(s)
- Bounding boxes with labels + unique IDs
- Detection confidence scores
- Live alerts appearing (e.g., "Helmet missing ⚠️", "Crowd threshold exceeded 🚨")
- FPS counter, latency indicator
- Multi-camera grid view

**Components:** `LiveFeed.tsx`, `BoundingBoxes.tsx`, `AlertPanel.tsx`, `StatusBar.tsx`

---

### 🔵 MODE 2 — Analytics Dashboard

**What the user sees:**
- Past event logs (searchable, filterable)
- Object counts over time (line charts, bar charts)
- Spatial heatmaps
- Event history timeline
- Export reports (PDF, CSV)

**Components:** `Charts.tsx`, `Heatmap.tsx`, `EventHistory.tsx`, `CounterCards.tsx`

---

### 🟡 MODE 3 — Configuration

**What the user sees:**
- Toggle AI modules on/off (Detection ✔️, OCR ✔️, Face ✔️, Pose ✔️)
- Set detection rules (visual builder: dropdown → condition → threshold)
- Manage devices/cameras
- Select performance mode (Lite / Balanced / Max)
- Configure ROI zones (drag-and-draw on video feed)

**Components:** `ModuleToggles.tsx`, `RuleBuilder.tsx`, `DeviceManager.tsx`, `PerformanceMode.tsx`

---

### 🔴 MODE 4 — Automation (Jarvis Mode 🔥)

**What the user sees:**
- Visual automation builder: **"If ___ happens → Do ___"**
- Pre-built templates (intrusion, safety, quality control)
- Action selector (email, webhook, IoT, API, notification)
- Automation execution log (what triggered, when, result)
- Active automation status

**Components:** `AutomationBuilder.tsx`, `ActionSelector.tsx`, `EventLog.tsx`

**Examples the user can build:**
- If intrusion → send email + sound alarm
- If product defect → reject item + log
- If person recognized → log entry + unlock door
- If fire detected → trigger alarm + notify fire department

---

## 8. Premium Spatial UI

### Design Philosophy

> The UI must feel like **Apple Vision Pro meets Minority Report** — spatial, glassy, alive. The user should be **wowed at first glance**.

### Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | React 18 + TypeScript |
| **Build Tool** | Vite |
| **Styling** | Tailwind CSS v4 + CSS custom properties |
| **3D Engine** | Three.js via React Three Fiber (`@react-three/fiber`) |
| **3D Helpers** | `@react-three/drei` (OrbitControls, Environment, etc.) |
| **Animations** | Framer Motion (layout, gestures, physics-based) |
| **State** | Zustand (lightweight, multiple stores) |
| **Charts** | Recharts or Visx |
| **WebSockets** | Native WebSocket API + custom hook |
| **Tilt Effect** | react-parallax-tilt |
| **Haptics** | Navigator.vibrate() API |
| **Icons** | Lucide React |
| **Font** | Inter (Google Fonts) |

### Glassmorphism Design System

```css
/* Core Glass Material */
.glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Glass with gradient border (light edge simulation) */
.glass-premium {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(24px);
  border: 1px solid transparent;
  border-image: linear-gradient(
    to bottom right,
    rgba(255, 255, 255, 0.4),
    rgba(255, 255, 255, 0.1)
  ) 1;
  border-radius: 20px;
}

/* Glow effect for interactive elements */
.glow {
  box-shadow:
    0 0 15px rgba(56, 189, 248, 0.3),
    0 0 45px rgba(56, 189, 248, 0.1);
}
```

### Key UI Components

| Component | Visual | Behavior |
|---|---|---|
| `GlassPanel` | Frosted glass surface | Background adapts to theme |
| `GlassCard` | Elevated glass card with edge glow | Hover lifts with shadow |
| `TiltCard` | Parallax hover effect | Tilts toward cursor (react-parallax-tilt) |
| `GlowButton` | Pulsing glow border | Ripple on click + haptic |
| `NeomorphicInput` | Inset glass input field | Focus glow animation |
| `Sidebar` | Glass sidebar with icon nav | Active item glow indicator |

### Interactive Behaviors

- **Hover Effects:** Cards lift 4px, shadow deepens, glow intensifies
- **Click Feedback:** Ripple animation + haptic vibration (mobile)
- **Scroll:** Parallax depth on background layers
- **Transitions:** Page transitions with Framer Motion (slide + fade + scale)
- **Loading States:** Skeleton screens with glass shimmer animation
- **Tooltips:** Glass tooltips with arrow, appear on hover with spring animation

---

## 9. 5 Visual Themes (Modes)

Each theme changes: background color, glass tint, accent glow, 3D scene, character personality, and interaction physics.

### Theme Definitions

| # | Theme | Background | Glass Surface | Accent / Glow | Physics |
|---|---|---|---|---|---|
| 1 | **Midnight** (Dark) | `#0f172a` Deep Slate | `rgba(30, 41, 59, 0.7)` | `#38bdf8` Sky Blue + `#818cf8` Indigo | Smooth, slow, "heavy" |
| 2 | **Cloud** (Light) | `#e2e8f0` Blue Grey | `rgba(255, 255, 255, 0.6)` | `#0ea5e9` Ocean Blue | Bouncy, snappy |
| 3 | **Nebula** (Creative) | `#050505` Pure Black | `rgba(255, 255, 255, 0.05)` | `#10b981` Emerald + `#a855f7` Purple | Fluid, follows gaze |
| 4 | **Forest** (Focus) | `#0a1f0a` Deep Emerald | `rgba(255, 255, 255, 0.08)` | `#10b981` Emerald + `#84cc16` Lime | Natural, swaying |
| 5 | **Solar** (Performance) | `#271a18` Dark Bronze | `rgba(255, 255, 255, 0.1)` | `#f59e0b` Amber + `#f43f5e` Rose | Aggressive, precision |

### Theme Implementation

Each theme is a TypeScript object stored in `themes/`:

```typescript
// themes/midnight.ts
export const midnight = {
  name: 'Midnight',
  colors: {
    background: '#0f172a',
    surface: 'rgba(30, 41, 59, 0.7)',
    accent: '#38bdf8',
    accentSecondary: '#818cf8',
    text: '#f8fafc',
    textMuted: '#94a3b8',
    border: 'rgba(255, 255, 255, 0.1)',
    glow: 'rgba(56, 189, 248, 0.3)',
  },
  physics: {
    stiffness: 100,
    damping: 15,
    mass: 1.5,
  },
  character: {
    archetype: 'Guardian',
    personality: 'Stoic, glowing eyes, minimal gestures',
    idleAnimation: 'idle_watchful',
  },
  background3D: {
    particleCount: 200,
    particleColor: '#38bdf8',
    speed: 0.3,
    mouseInfluence: 0.5,
  },
};
```

### Theme Switching

- Managed by Zustand store (`themeStore.ts`)
- CSS variables update instantly via `document.documentElement.style.setProperty()`
- 3D scene transitions smoothly (particle colors fade, character swaps)
- No page reload — everything is reactive

---

## 10. 3D Characters & AI Avatars

### Character Archetypes (One per Theme)

| Theme | Character | Visual | Behavior |
|---|---|---|---|
| Midnight | **The Guardian** | Stoic, glowing eyes, dark armor | Minimal gestures, watchful |
| Cloud | **The Guide** | Airy, energetic, white outfit | Large hand gestures, encouraging |
| Nebula | **The Muse** | Ethereal, floating, light trails | Follows cursor closely |
| Forest | **The Sage** | Calm, cross-legged, slow breathing | Natural, meditative |
| Solar | **The Pilot** | Tech-focused, holographic visor | Sharp, precision movements |

### Implementation

| Feature | Tech |
|---|---|
| Avatar Rendering | React Three Fiber + `.glb` models |
| Gaze Tracking | `useFrame` hook — head/eyes follow mouse position |
| Lip Sync | WebAudio API → frequency analysis → Viseme mapping |
| Expressions | Morph Targets (smile, squint, frown, surprise) |
| Idle Logic | If inactive 30s → "bored" animation to re-engage user |
| Interactive Tooltips | Character looks at hovered button, performs "point" animation |

### 3D Background Elements

Each theme has a unique animated background:
- **Midnight:** Slowly rotating star field, blue nebula particles
- **Cloud:** Floating white orbs, soft light rays
- **Nebula:** Cosmic dust clouds, purple/green aurora
- **Forest:** Floating leaf particles, organic shapes
- **Solar:** Solar flares, ember particles, heat distortion

All backgrounds respond to mouse movement (parallax effect).

---

## 11. Security (Zero Trust)

### 🔐 Identity & Access

| Layer | Implementation |
|---|---|
| User Auth | JWT + OAuth2 (Google, GitHub) |
| Device Auth | Unique device tokens (each camera = identity) |
| RBAC | Admin · Operator · Viewer · API-only |
| Session | Refresh tokens, auto-expire |

### 🔒 Data Protection

| Layer | Implementation |
|---|---|
| Transport | TLS 1.3 everywhere (HTTPS) |
| At Rest | Encrypt face data, logs, video metadata |
| API | API key + JWT for all endpoints |
| Secrets | Environment variables, never hardcoded |

### 🚨 Threat Defense

| Threat | Defense |
|---|---|
| DDoS | Cloudflare protection |
| Rate limiting | Redis-based rate limiter |
| Injection | Input sanitization, parameterized queries |
| Brute force | Account lockout after N failures |

### 🧠 AI Security (Unique Layer)

| Threat | Defense |
|---|---|
| Adversarial frames | Input validation (frame integrity checks) |
| Model theft | Model encryption, API-only access |
| Abuse detection | Anomalous usage pattern detection |
| Fake inputs | Frame hash verification |

---

## 12. Anti-Abuse & Misuse Prevention ⭐ NEW

> **Goal:** Make it impossible for the system to be used illegally, hacked, or misused.

### 🛡️ Content & Usage Safeguards

| Safeguard | Implementation |
|---|---|
| **Content Fingerprinting** | Hash all processed frames; detect if someone feeds manipulated/deepfake input |
| **Usage Anomaly Detection** | ML-based detection of unusual patterns (e.g., 10,000 face lookups in 1 hour) |
| **Geo-fencing** | Restrict certain features by region (e.g., facial recognition disabled in EU for GDPR) |
| **Terms Violation Auto-Flag** | Auto-detect and flag accounts running surveillance-style mass tracking |
| **Watermarking** | Invisible watermarks on exported images/videos for traceability |

### 🔒 Anti-Hacking Measures

| Attack Vector | Defense |
|---|---|
| **API Abuse** | Rate limiting + API key rotation + IP allowlisting |
| **Session Hijacking** | HttpOnly cookies, SameSite=Strict, short-lived tokens |
| **XSS / CSRF** | CSP headers, CSRF tokens, input sanitization |
| **SQL Injection** | ORM-only queries, parameterized statements, no raw SQL |
| **Privilege Escalation** | Server-side role checks on every endpoint (never trust client) |
| **Man-in-the-Middle** | HSTS, certificate pinning (mobile), TLS 1.3 |
| **Replay Attacks** | Request nonces, timestamp validation |
| **Credential Stuffing** | CAPTCHA after 3 failed attempts, breach password checks |

### 📋 Admin Audit Trail

Every admin action is logged permanently:

```
{
  "admin_id": "uuid",
  "action": "user_takeover | ban_user | config_change | feature_restrict",
  "target_user_id": "uuid",
  "timestamp": "ISO-8601",
  "ip_address": "xxx.xxx.xxx.xxx",
  "reason": "string",
  "changes": { "before": {}, "after": {} }
}
```

### 🚫 Misuse Prevention Policies

- Face recognition **requires explicit consent** per applicable law
- Automated alerts if system is used for mass surveillance beyond authorized scope
- Export logs are watermarked with user ID + timestamp
- All API access logged; suspicious patterns auto-reported to admin
- Feature disable kill-switch: admin can instantly disable any feature globally or per-user

---

## 13. Scalability & Reliability

### Scalability Architecture

```
Users → CDN (Cloudflare) → API Gateway → Microservices → Databases
```

| Strategy | Detail |
|---|---|
| Horizontal scaling | Stateless services, add instances as needed |
| Load balancing | Nginx / cloud LB across service instances |
| CDN | Cloudflare for static assets + global edge |
| Multi-region | Deploy to multiple cloud regions |
| Database scaling | Read replicas, connection pooling |

### Reliability (99.9% uptime target)

| System | Detail |
|---|---|
| Auto-restart | Docker health checks + restart policies |
| Failover | If cloud fails → edge continues working locally |
| Backup DB | Automated PostgreSQL backups |
| Retry logic | Exponential backoff for all external calls |
| Circuit breakers | Prevent cascade failures |
| Graceful fallback | If detection fails → use last known state |

### Docker Deployment

```yaml
# docker-compose.yml (simplified)
services:
  edge:
    build: ./docker/Dockerfile.edge
    volumes: [./edge:/app/edge]
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]  # if available

  cloud:
    build: ./docker/Dockerfile.cloud
    depends_on: [postgres, redis]

  platform:
    build: ./docker/Dockerfile.platform
    depends_on: [postgres, redis, pinecone]
    ports: ["8000:8000"]

  client:
    build: ./client
    ports: ["3000:3000"]

  postgres:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

---

## 14. Observability & Monitoring

| Tool | Purpose |
|---|---|
| **Sentry** | Error tracking, crash reports |
| **PostHog** | Product analytics, user behavior |
| **Custom Metrics** | FPS drops, API failures, detection accuracy |

### Metrics Dashboard (Internal)

| Metric | Target |
|---|---|
| Frame processing | < 50ms |
| API response time | < 200ms |
| Dashboard refresh | Real-time (WebSocket) |
| Detection accuracy | > 90% mAP |
| System uptime | 99.9% |
| Active devices | Tracked per user |
| Crash-free users | > 99% |
| Feature usage by location | Tracked globally |

---

## 15. Crash Resilience & Recovery ⭐ NEW

> **Goal:** If ANY user's app crashes, admin knows immediately AND the user loses nothing.

### 🔥 Crash Reporting Pipeline

```
App Crash / Unhandled Error
   ↓
CrashBoundary.tsx catches error (React Error Boundary)
   ↓
Crash payload sent to server:
  - stack trace
  - device info (OS, browser, screen size)
  - last 50 user actions (breadcrumbs)
  - app state snapshot
  - user ID + session ID
   ↓
Server: crash_collector.py stores in DB
   ↓
Admin Dashboard: CrashReports.tsx shows real-time crash feed
   ↓
Notification sent to admin (push + email if severity = critical)
```

### Client-Side Implementation

| Component | Purpose |
|---|---|
| `CrashBoundary.tsx` | React Error Boundary — catches render errors, shows fallback UI |
| `useCrashReporter.ts` | Hook that captures unhandled errors + promise rejections |
| `window.onerror` | Global JS error handler |
| `window.onunhandledrejection` | Catches async failures |
| **Breadcrumbs** | Circular buffer of last 50 user actions (clicks, navigations, API calls) |

### Crash Report Schema

```json
{
  "crash_id": "uuid",
  "user_id": "uuid",
  "session_id": "uuid",
  "timestamp": "ISO-8601",
  "error_message": "string",
  "stack_trace": "string",
  "breadcrumbs": ["click:settings", "api:GET /config", "error:timeout"],
  "device": { "os": "Windows 11", "browser": "Chrome 120", "screen": "1920x1080" },
  "app_state_snapshot": { "current_page": "Dashboard", "theme": "midnight" },
  "severity": "critical | error | warning"
}
```

### Targets

| Metric | Target |
|---|---|
| Crash-free users | > 99% |
| Crash report delivery | < 5 seconds to admin |
| Cold start crash | 0 (tested explicitly) |
| Background→foreground crash | 0 |
| Process death recovery | Full state restore |

---

## 16. State Recovery & Session Continuity ⭐ NEW

> **Goal:** If app crashes, internet dies, user kills the app, or refreshes — **NOTHING is lost. Everything resumes exactly where it was.**

### 🔄 How State is Preserved

| Scenario | Recovery Strategy |
|---|---|
| **App crash** | State auto-saved to `localStorage` every 5 seconds + on every significant action |
| **Internet drops** | Operations queued in offline store; auto-replay on reconnect |
| **User kills app** | `beforeunload` event saves full state snapshot |
| **Browser refresh** | Zustand `persist` middleware restores all stores from `localStorage` |
| **Tab close + reopen** | `sessionStorage` + `localStorage` dual backup |
| **Device reboot** | `localStorage` persists; cloud sync fills gaps |

### Implementation

```typescript
// Every Zustand store uses persist middleware
import { persist } from 'zustand/middleware';

const useVisionStore = create(
  persist(
    (set) => ({
      detections: [],
      activeCamera: null,
      // ... state
    }),
    {
      name: 'visionx-vision-state',
      storage: createJSONStorage(() => localStorage),
      // Auto-save on every state change
    }
  )
);
```

### `useStateRecovery.ts` Hook

- On mount: checks `localStorage` for saved state
- Detects if last session crashed (flag set on clean exit)
- If crash detected: shows "Resume where you left off?" prompt
- Periodic snapshots every 5 seconds to `localStorage`
- On `beforeunload`: emergency full-state dump
- On reconnect after offline: merges local changes with server state

### State Categories

| State | Storage | Survives Crash? | Survives Reinstall? |
|---|---|---|---|
| UI state (page, scroll, theme) | localStorage | ✅ | ❌ (see §18) |
| Detection config | localStorage + server | ✅ | ✅ |
| Pending actions | IndexedDB | ✅ | ❌ (see §18) |
| User preferences | Server (primary) | ✅ | ✅ |
| Event history | Server | ✅ | ✅ |
| Automation rules | Server | ✅ | ✅ |

---

## 17. Offline-First Architecture ⭐ NEW

> **Goal:** The app must be USEFUL even without internet — not just show "No connection."

### 📱 Offline Feature Matrix

| Feature | Offline? | How |
|---|---|---|
| **View last dashboard** | ✅ | Cached in Service Worker |
| **View recent events** | ✅ | Cached in IndexedDB |
| **Edge AI detection** | ✅ | Runs entirely on-device |
| **Local tracking** | ✅ | Runs entirely on-device |
| **View help articles** | ✅ | Pre-cached knowledge base |
| **Create automation rules** | ✅ | Saved locally, synced later |
| **Change settings** | ✅ | Queued, applied on reconnect |
| **View analytics** | ⚠️ Partial | Last-fetched data shown with "stale" indicator |
| **Face recognition** | ❌ | Requires cloud |
| **OCR** | ❌ | Requires cloud |
| **Send notifications** | ❌ | Queued, sent on reconnect |

### Service Worker Strategy

```
Install → Cache critical assets (HTML, CSS, JS, fonts, icons)
Activate → Clean old caches
Fetch → Network-first for API, Cache-first for assets
Background Sync → Queue failed requests, replay when online
```

### Offline UI Indicators

| Indicator | Behavior |
|---|---|
| `OfflineBanner.tsx` | Glassmorphic amber banner: "You're offline — some features limited" |
| `SyncStatus.tsx` | Shows pending sync count: "3 actions waiting to sync" |
| Stale data badge | Small "⏱️ 5 min ago" on cached data cards |
| Feature dimming | Cloud-only features visually dimmed with lock icon |

### Reconnection Behavior

1. `useOffline.ts` detects network recovery via `navigator.onLine` + heartbeat ping
2. Offline queue replays in order (FIFO)
3. Conflict resolution: **server wins** for shared state, **client wins** for local preferences
4. Sync progress shown in `SyncStatus.tsx`
5. Once synced: banner disappears, features re-enable with smooth animation

---

## 18. Data Persistence & Reinstall Recovery ⭐ NEW

> **Goal:** If user uninstalls and reinstalls — ALL history, data, settings, automation rules are restored as if nothing happened.

### 🗄️ Cloud-First Data Strategy

**Rule: The server is the source of truth. The client is a cache.**

| Data | Stored On Server? | Restored On Reinstall? |
|---|---|---|
| User profile & preferences | ✅ | ✅ |
| Event history & logs | ✅ | ✅ |
| Automation rules | ✅ | ✅ |
| Device configurations | ✅ | ✅ |
| Theme preference | ✅ | ✅ |
| Analytics data | ✅ | ✅ |
| Notification history | ✅ | ✅ |
| Support tickets | ✅ | ✅ |
| Subscription/billing state | ✅ (Stripe) | ✅ |
| Captured images/clips | ✅ (Cloud Storage) | ✅ (on-demand download) |

### Reinstall Flow

```
User reinstalls app
   ↓
Login (JWT / OAuth)
   ↓
Server returns full user profile + preferences
   ↓
Client hydrates all Zustand stores from server data
   ↓
Devices auto-reconnect via device tokens
   ↓
Event history loads on-demand (paginated)
   ↓
Everything is back — zero data loss
```

### Key Design Decisions

- **Never rely on localStorage for critical data** — it's a cache only
- **All user-generated content synced to server within 5 seconds**
- **Server-side user export** available (GDPR): full JSON dump of all user data
- **Deleted account grace period**: 30 days before permanent deletion
- **Media files**: stored in cloud storage, thumbnails cached locally

---

## 19. Privacy, Cookies & Compliance

### GDPR Compliance

| Requirement | Implementation |
|---|---|
| Cookie consent banner | `CookieBanner.tsx` — opt-in before tracking |
| Data export | API endpoint to export all user data |
| Data deletion | API endpoint to delete all user data |
| Privacy policy | Legal page with clear data usage terms |
| Data retention | Configurable retention periods, auto-delete |

### Cookie Usage

| Cookie | Purpose | Category |
|---|---|---|
| Session | Login state | Essential |
| Preferences | Theme, layout | Functional |
| Analytics | PostHog | Optional (requires consent) |

### Data Lifecycle

```
Capture → Process → Store → Analyze → Archive → Delete
```

- All face data encrypted at rest
- Video frames processed in-memory, not stored by default
- Event images stored with configurable retention
- User can request full data deletion

---

## 20. Monetization System

### Payment Provider: Stripe

### Subscription Plans

| Plan | Price | Features |
|---|---|---|
| **Free** | $0/mo | Basic detection, 1 camera, limited events |
| **Pro** | $29/mo | Tracking + OCR, 5 cameras, full analytics |
| **Enterprise** | $99/mo | All modules, unlimited cameras, API access, priority support |

### Feature Gating

```python
# platform/billing/feature_gates.py
PLAN_FEATURES = {
  'free': ['detection', 'counting'],
  'pro': ['detection', 'counting', 'tracking', 'ocr', 'analytics'],
  'enterprise': ['detection', 'counting', 'tracking', 'ocr', 'face',
                  'pose', 'segmentation', 'analytics', 'api', 'automation'],
}
```

### Controls

| Control | Detail |
|---|---|
| API rate limits | Per plan (Free: 100/hr, Pro: 1000/hr, Enterprise: unlimited) |
| Camera limits | Per plan |
| Feature toggles | Server-side gating |
| Usage metering | Track API calls, processing time |

---

## 21. Data Architecture

### Storage Layers

| Data Type | System | Purpose |
|---|---|---|
| Structured Logs | **PostgreSQL** | Events, users, devices, rules, billing |
| Real-time State | **Redis** | Active detections, session cache, rate limits |
| Vector Embeddings | **Pinecone** | Face embeddings, pattern memory |
| Media Files | **Cloud Storage** (S3/GCS) | Captured images, video clips |

### Database Schema (PostgreSQL — Key Tables)

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    role VARCHAR DEFAULT 'viewer',
    plan VARCHAR DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Devices
CREATE TABLE devices (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR,
    type VARCHAR,  -- 'webcam', 'rtsp', 'ip_camera'
    source VARCHAR,
    status VARCHAR DEFAULT 'inactive',
    last_seen TIMESTAMP
);

-- Events
CREATE TABLE events (
    id UUID PRIMARY KEY,
    device_id UUID REFERENCES devices(id),
    event_type VARCHAR,
    details JSONB,
    image_url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Rules
CREATE TABLE rules (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    condition JSONB,
    actions JSONB,
    enabled BOOLEAN DEFAULT TRUE
);

-- Automations
CREATE TABLE automations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    trigger_rule_id UUID REFERENCES rules(id),
    action_type VARCHAR,
    action_config JSONB,
    last_triggered TIMESTAMP,
    enabled BOOLEAN DEFAULT TRUE
);

-- ⭐ Crash Reports
CREATE TABLE crash_reports (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id UUID,
    error_message TEXT,
    stack_trace TEXT,
    breadcrumbs JSONB,
    device_info JSONB,
    app_state JSONB,
    severity VARCHAR DEFAULT 'error',
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ⭐ Support Tickets
CREATE TABLE support_tickets (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    category VARCHAR,
    subject VARCHAR,
    description TEXT,
    priority VARCHAR DEFAULT 'medium',
    status VARCHAR DEFAULT 'open',
    assigned_admin_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ⭐ Admin Audit Log
CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY,
    admin_id UUID REFERENCES users(id),
    action VARCHAR NOT NULL,
    target_user_id UUID,
    ip_address VARCHAR,
    reason TEXT,
    changes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ⭐ Help Articles
CREATE TABLE help_articles (
    id UUID PRIMARY KEY,
    title VARCHAR NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR,
    tags VARCHAR[],
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 22. Integration Layer

### External Systems

| System | Protocol | Use Case |
|---|---|---|
| **Robots/PLC** | Modbus TCP, OPC-UA | Industrial automation |
| **IoT Devices** | MQTT, HTTP | Sensors, alarms, relays |
| **External APIs** | REST | Third-party integrations |
| **Webhooks** | HTTP POST | Event notifications |
| **Email** | Resend API | Alert emails |
| **Cloud Storage** | S3/GCS SDK | Media archival |

---

## 23. Jarvis-Level Capabilities

These are the features that elevate VisionX from "a detection system" to "an intelligent agent."

### 🔥 1. Context-Aware System

- Understand **scene context**, not just objects
- Example: "person **running** in **restricted area**" → not just "person detected"
- Combines: detection + pose + ROI + behavior → contextual understanding

### 🔥 2. Memory System (Pinecone)

- Store embeddings of detected faces, objects, patterns
- Recognize returning individuals
- Pattern learning over time (e.g., "this vehicle appears every day at 3 PM")

### 🔥 3. Self-Improving System

- Analyze detection logs for false positives/negatives
- Flag low-confidence detections for review
- Feedback loop: user corrections improve future accuracy
- A/B test models automatically

### 🔥 4. Multi-Camera Intelligence

- Cross-camera tracking (person moves from Camera A to Camera B)
- Global scene understanding across all feeds
- Unified event timeline across devices

### 🔥 5. Automation System (Vision → Action)

- Complete event chain: **Detect → Decide → Act**
- User-definable automation rules (visual builder)
- Pre-built templates for common scenarios
- Example: Detect fire → trigger alarm + notify fire department + store video

---

## 24. Help Center & User Support ⭐ NEW

> **Goal:** Users should NEVER feel stuck. Help is always one click away.

### 📚 Knowledge Base

| Feature | Detail |
|---|---|
| **Searchable FAQ** | Full-text search across all articles |
| **Getting Started Guides** | Step-by-step setup for each feature |
| **Video Tutorials** | Embedded walkthrough videos |
| **Contextual Help** | "?" icon on every feature — click to see relevant article |
| **Release Notes** | Changelog for every update |

### 🎫 Support Ticket System

- User submits ticket with category, description, screenshots
- Auto-assigned priority (low/medium/high/critical)
- Admin sees all tickets in Admin Dashboard
- Status tracking: Open → In Progress → Resolved → Closed
- Email notifications at each status change

### 💬 Live Chat

- WebSocket-based real-time chat widget
- Appears as floating glassmorphic bubble (bottom-right)
- Admin can respond from Admin Dashboard
- Chat history preserved per user

### 🚀 Onboarding Wizard

- First-time user gets guided setup:
  1. Welcome → Connect Camera → Enable Detection → Set First Rule → Done!
- Skippable, resumable, tracks completion
- Completion progress shown in user dashboard

### Components

| Frontend | Backend |
|---|---|
| `HelpSearch.tsx` | `help/knowledge_base.py` |
| `ArticleViewer.tsx` | `help/knowledge_base.py` |
| `TicketForm.tsx` / `TicketList.tsx` | `help/ticket_system.py` |
| `LiveChat.tsx` | `help/live_chat.py` |
| `OnboardingWizard.tsx` | `help/onboarding.py` |
| `ContextualHelp.tsx` | Static mapping per feature |

---

## 25. Notification Service (Full System) ⭐ NEW

> **Goal:** Notify users about EVERYTHING — updates, alerts, features, billing, security — across ALL channels.

### 📢 Notification Types

| Category | Examples |
|---|---|
| **System Alerts** | Detection events, threshold exceeded, device offline |
| **Product Updates** | New features, version updates, maintenance windows |
| **Billing** | Payment success, renewal reminder, plan upgrade available |
| **Security** | New login detected, password changed, suspicious activity |
| **Support** | Ticket response, live chat message |
| **Automation** | Rule triggered, action completed, action failed |
| **Admin Broadcast** | System-wide announcements from admin |

### 📬 Delivery Channels

| Channel | Tech | Use Case |
|---|---|---|
| **In-App Bell** | WebSocket + Zustand | Real-time, always visible |
| **Push Notification** | Web Push API / FCM | When app is in background/closed |
| **Email** | Resend API | Critical alerts, billing, summaries |
| **SMS** | Twilio | Emergency-level alerts only |
| **Toast** | Framer Motion popup | Transient, in-context alerts |

### 🔧 User Notification Preferences

Users can control per-category, per-channel:

```
Detection Alerts:  [✅ In-App]  [✅ Push]  [❌ Email]  [❌ SMS]
Product Updates:   [✅ In-App]  [❌ Push]  [✅ Email]  [❌ SMS]
Billing:           [✅ In-App]  [✅ Push]  [✅ Email]  [✅ SMS]
Security:          [✅ In-App]  [✅ Push]  [✅ Email]  [✅ SMS]
```

### Notification Schema

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    type VARCHAR,          -- 'alert', 'update', 'billing', 'security', 'broadcast'
    title VARCHAR,
    message TEXT,
    channel VARCHAR[],     -- ['in_app', 'push', 'email']
    read BOOLEAN DEFAULT FALSE,
    action_url VARCHAR,    -- Deep link to relevant page
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 26. Admin Dashboard (God Mode) ⭐ NEW

> **Goal:** Admin can control ANYTHING from ANYWHERE — any query, all access, any change, any restriction, any time.

### 🎛️ Admin Capabilities

| Capability | Detail |
|---|---|
| **View all users** | Search, filter by plan/status/location, sort |
| **User takeover** | Impersonate any user's session to debug their issue (audit-logged) |
| **Ban / Restrict user** | Immediately disable account or restrict specific features |
| **View all crashes** | Real-time crash feed with stack traces, breadcrumbs, device info |
| **View all events** | Global event timeline across all users and devices |
| **System health** | CPU, GPU, memory, API response times, database stats |
| **Feature usage map** | Which features most used, by whom, from where (see §27) |
| **Remote config** | Push config changes to all users or specific segments |
| **Broadcast notifications** | Send announcements to all users or segments |
| **Manage subscriptions** | Override plans, grant trials, issue refunds |
| **View support tickets** | All tickets, assign, respond, resolve |
| **Live chat responses** | Respond to user chats from admin panel |
| **Kill switch** | Instantly disable any feature globally or per-user |
| **Audit log** | Every admin action logged with who/when/what/why |

### 🔐 Admin Takeover (Impersonation)

This is for solving user queries by seeing exactly what they see:

```
Admin clicks "Takeover" on user row
   ↓
Server generates temporary impersonation token
   ↓
Admin sees the user's dashboard exactly as they see it
   ↓
Banner shown: "👁️ Admin viewing as user@email.com"
   ↓
All actions logged to admin audit trail
   ↓
Admin clicks "End Session" → returns to admin dashboard
```

**Safeguards:**
- Only super-admin role can impersonate
- Time-limited session (max 30 minutes)
- Every action during takeover logged with `admin_impersonation` flag
- User is NOT notified (to avoid confusion), but audit trail is permanent

### Admin Dashboard Pages

| Page | Content |
|---|---|
| **Overview** | Total users, active devices, events/hour, crash rate, revenue |
| **Users** | User table with search, actions (takeover, ban, message) |
| **Crashes** | Crash feed, severity chart, affected users |
| **Feature Usage** | Usage heatmap by feature × location |
| **System Health** | Infrastructure metrics, API latency, DB status |
| **Config** | Remote feature flags, kill switches |
| **Support** | Ticket queue, live chats |
| **Audit Log** | Every admin action ever taken |

---

## 27. Feature Usage Tracking & Analytics ⭐ NEW

> **Goal:** Know exactly which feature is most used, by whom, from where — globally.

### 📊 What Gets Tracked

| Event | Data Captured |
|---|---|
| **Feature used** | Feature name, timestamp, user ID, duration |
| **Page visited** | Page name, time spent, scroll depth |
| **Button clicked** | Button ID, context (which page, which section) |
| **API called** | Endpoint, method, response time, status code |
| **Detection run** | Module used, objects detected, processing time |
| **Rule triggered** | Rule ID, trigger condition, actions executed |

### 🌍 Location-Wise Analytics

- **GeoIP lookup** on every API request → map user to country/city
- Aggregated views: "Detection module used 15,000 times today — 40% India, 25% USA, 15% Germany"
- Visual heatmap on admin dashboard world map

### 📈 Admin Analytics Views

| View | What Admin Sees |
|---|---|
| **Feature Ranking** | Bar chart: most → least used features |
| **Usage Over Time** | Line chart: feature usage trends (daily/weekly/monthly) |
| **Geographic Map** | World heatmap: where is VisionX used most |
| **User Cohorts** | Which plan tier uses which features most |
| **Drop-off Funnel** | Where do users stop in the onboarding flow |
| **Session Duration** | Average time spent per user per session |

### Implementation

```python
# platform/usage_tracking/tracker.py
class UsageTracker:
    async def track(self, event: UsageEvent):
        """Track a feature usage event"""
        await self.db.insert('usage_events', {
            'user_id': event.user_id,
            'feature': event.feature,
            'action': event.action,
            'geo_location': await self.geoip.lookup(event.ip),
            'device_type': event.device_type,
            'timestamp': datetime.utcnow(),
            'metadata': event.metadata
        })
```

### Usage Events Schema

```sql
CREATE TABLE usage_events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    feature VARCHAR NOT NULL,       -- 'detection', 'ocr', 'automation', etc.
    action VARCHAR NOT NULL,        -- 'used', 'configured', 'viewed'
    geo_country VARCHAR,
    geo_city VARCHAR,
    device_type VARCHAR,            -- 'web', 'mobile', 'edge'
    session_id UUID,
    duration_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usage_feature ON usage_events(feature);
CREATE INDEX idx_usage_geo ON usage_events(geo_country);
CREATE INDEX idx_usage_time ON usage_events(created_at);
```

---

## 28. User Dashboard (Separate from Admin) ⭐ NEW

> **Goal:** Every user gets their OWN interactive dashboard — personal, clean, useful.

### 🏠 User Dashboard vs Admin Dashboard

| Feature | User Dashboard | Admin Dashboard |
|---|---|---|
| **Sees** | Own data only | ALL users' data |
| **Controls** | Own cameras, rules, settings | Everything system-wide |
| **Analytics** | Own usage stats | Global usage analytics |
| **Support** | Submit tickets, chat | View & respond to all tickets |
| **Billing** | Own subscription | Override any subscription |
| **Events** | Own events only | All events globally |

### 📋 User Dashboard Sections

| Section | Content |
|---|---|
| **Overview** | Quick stats: active cameras, events today, detection count |
| **My Devices** | List of connected cameras, status, last seen, quick actions |
| **My Events** | Personal event timeline with search and filters |
| **My Usage** | Which features YOU used, how often, usage trends |
| **Account** | Profile, password, 2FA, notification preferences |
| **Billing** | Current plan, upgrade options, invoice history, payment method |
| **Help** | Quick links to FAQ, support ticket status, chat |

### UX Essentials (from Pre-Production Checklist)

Every screen in the user dashboard implements:

| State | Implementation |
|---|---|
| **Loading** | `LoadingState.tsx` — Glassmorphic skeleton/shimmer animation |
| **Empty** | `EmptyState.tsx` — Friendly illustration + "Get started" CTA |
| **Error** | `ErrorState.tsx` — Clear message + retry button + help link |
| **Success** | Toast notification with smooth animation |
| **Offline** | `OfflineBanner.tsx` — Indicates cached data with stale indicator |

---

## 29. Device Ecosystem & Deployment

### Supported Environments

| Environment | Stack | Key Feature |
|---|---|---|
| 📱 **Mobile** | React Native / Flutter + ONNX/TFLite | On-device ML, camera input |
| 💻 **Desktop** | Electron or native Python app | Full pipeline, multi-camera |
| 🌐 **Web** | React + Vite (our client) | Dashboard, analytics, config |
| 📹 **CCTV** | Python edge engine + RTSP | Continuous monitoring |
| 🤖 **Edge** | Jetson/RPi + ONNX/TensorRT | Offline AI, low latency |
| ☁️ **Cloud** | Docker + FastAPI + GPU | Heavy processing, APIs |

### Latency Strategy

> **Rule: "Do fast things locally, heavy things in cloud"**

| Task | Where | Target Latency |
|---|---|---|
| Detection | Edge | < 30ms |
| Tracking | Edge | < 10ms |
| Face Recognition | Cloud | < 200ms |
| OCR | Cloud | < 150ms |
| Analytics | Cloud | < 500ms |

---

## 30. Performance Engineering

| Technique | Detail |
|---|---|
| Model quantization | INT8 for edge, FP16 for balanced, FP32 for max |
| Async processing | Non-blocking frame processing pipeline |
| Batch inference | Process multiple frames at once (GPU) |
| GPU pipelines | TensorRT optimization on NVIDIA hardware |
| Frame skipping | Adaptive skip based on CPU/GPU load |
| Region of Interest | Process only relevant frame areas |
| Redis caching | Cache frequent queries and recent detections |
| CDN delivery | Cloudflare for global static asset delivery |

---

## 31. Pre-Production Checklist ⭐ NEW

> Adapted from your mobile pre-production checklist — expanded to cover web, edge, and cross-platform.

### ✅ 1. Crash-Free Experience

- [ ] React Error Boundary wraps entire app (`CrashBoundary.tsx`)
- [ ] Global `window.onerror` + `onunhandledrejection` handlers
- [ ] Crash reports sent to server within 5 seconds
- [ ] Test: cold start (fresh load)
- [ ] Test: background → foreground (tab switch)
- [ ] Test: process death restore (kill tab, reopen)
- [ ] No crashes on null API responses
- [ ] No crashes on config/theme changes
- [ ] 👉 Target: Crash-free users > 99%

### ✅ 2. Performance & Smoothness

- [ ] App launch time < 3 seconds (lazy load heavy modules)
- [ ] No heavy computation on main thread (use Web Workers)
- [ ] Proper async/await usage — no blocking calls
- [ ] Avoid unnecessary React re-renders (memo, useMemo, useCallback)
- [ ] 3D scenes use `useFrame` efficiently — no memory leaks
- [ ] 👉 Check with Chrome DevTools Performance tab

### ✅ 3. State / Lifecycle Safety

- [ ] Handle: tab visibility change (`visibilitychange` event)
- [ ] Handle: browser back/forward navigation
- [ ] Use Zustand `persist` for all critical stores
- [ ] `useStateRecovery.ts` auto-saves every 5 seconds
- [ ] `beforeunload` saves emergency state dump
- [ ] 👉 No data loss on refresh, tab switch, or crash

### ✅ 4. Network Handling

- [ ] API timeouts configured (10s default)
- [ ] Graceful error handling: no internet, 500 errors, timeouts
- [ ] Proper UI states shown: loading / success / error / empty / offline
- [ ] Retry with exponential backoff on transient failures
- [ ] Offline queue for failed mutations
- [ ] 👉 NEVER crash on API failure

### ✅ 5. Security (Critical)

- [ ] No API keys in client-side code — use server proxy
- [ ] HTTPS only — HSTS headers set
- [ ] Code obfuscation enabled (Vite build minification)
- [ ] Secure storage: HttpOnly cookies for tokens
- [ ] CSP headers configured
- [ ] CSRF protection on all mutations
- [ ] Rate limiting on all API endpoints
- [ ] 👉 Run OWASP ZAP scan before launch

### ✅ 6. Logging & Analytics

- [ ] Sentry initialized for error tracking
- [ ] PostHog initialized for product analytics
- [ ] Track: page visits, feature usage, drop-offs
- [ ] Usage events sent to `usage_tracking` service
- [ ] 👉 Without analytics → no product decisions

### ✅ 7. Testing

- [ ] Unit tests: Zustand stores, utility functions
- [ ] Integration tests: API routes (pytest)
- [ ] Component tests: key UI components
- [ ] Edge cases tested: slow internet, empty state, retry flows
- [ ] 👉 Minimum safety net before scaling

### ✅ 8. Architecture Sanity

- [ ] No business logic in components — use stores/hooks
- [ ] API calls abstracted through `api.ts` — no raw fetch in components
- [ ] Server-side: Repository pattern for DB access
- [ ] Server-side: No direct DB calls from route handlers
- [ ] 👉 Follow: SRP (Single Responsibility) + DIP (Dependency Inversion)

### ✅ 9. State Management

- [ ] State survives: re-render, route change, theme switch
- [ ] Zustand stores use `persist` middleware correctly
- [ ] No stale closures in WebSocket handlers
- [ ] 👉 Avoid UI glitches / resets on any user action

### ✅ 10. Build & Release

- [ ] Test PRODUCTION build (not just dev server)
- [ ] Enable: minification, tree-shaking, code splitting
- [ ] Asset optimization: compress images, lazy-load 3D models
- [ ] Versioning: Git tags + semantic versioning
- [ ] Source maps: uploaded to Sentry (not shipped to client)

### ✅ 11. Permissions & Compliance

- [ ] Only request necessary permissions (camera, notifications)
- [ ] Handle permission denial gracefully with fallback UI
- [ ] Privacy Policy page
- [ ] Cookie consent banner (GDPR)
- [ ] Data export + deletion endpoints (GDPR)

### ✅ 12. UX Essentials

- [ ] `LoadingState.tsx` everywhere data loads
- [ ] `EmptyState.tsx` when no data (not blank screen)
- [ ] `ErrorState.tsx` on failures (not just console.error)
- [ ] Proper back navigation (browser history works)
- [ ] Smooth page transitions (Framer Motion)
- [ ] 👉 UX polish = retention

### ✅ 13. Main Thread Protection (ANR Prevention)

- [ ] WebSocket message processing offloaded to worker
- [ ] Heavy frame processing runs in Web Worker / edge engine
- [ ] No synchronous localStorage reads on render path
- [ ] Debounce/throttle frequent event handlers (scroll, resize, mouse)

### ✅ 14. Offline / Edge Handling

- [ ] Service Worker registered and caching critical assets
- [ ] `useOffline.ts` detects network status changes
- [ ] Fallback UI shown for cloud-dependent features
- [ ] Offline queue replays on reconnect
- [ ] No data corruption from partial syncs

### ✅ 15. Post-Launch Readiness

- [ ] Monitor: crashes (Sentry), usage (PostHog), API health
- [ ] Ability to push quick fixes (Vercel instant deploy)
- [ ] Rollback capability (Git revert + redeploy)
- [ ] Feature flags for gradual rollout
- [ ] Admin kill switch for problematic features

---

## 32. Phased Execution Roadmap

### Phase 1: Foundation (Weeks 1–3) ✅ COMPLETE

> **Goal:** Core engine that works with a webcam, detects objects, and displays results.
> 
> **Completed:** 2026-04-07 | **Tests:** 26/26 passing | **Milestone:** Achieved ✅

| Task | Files | Status |
|---|---|---|
| Project scaffolding | Directory structure, dependencies | ✅ |
| Camera input engine | `edge/core/camera.py` | ✅ |
| Preprocessing engine | `edge/core/preprocessor.py` | ✅ |
| YOLO detection module | `edge/modules/detection.py` | ✅ |
| Tracking engine (DeepSORT) | `edge/core/tracker.py`, `edge/modules/tracking.py` | ✅ |
| Multi-threaded pipeline | `edge/core/threading_engine.py`, `edge/core/pipeline.py` | ✅ |
| Basic visualization | `visualization/overlay.py` | ✅ |
| ROI engine | `edge/roi/roi_engine.py` | ✅ |
| Counting module | `edge/modules/counting.py` | ✅ |
| Measurement module | `edge/modules/measurement.py` | ✅ |
| Performance modes | `edge/config/edge_config.py` | ✅ |
| Unit tests | `tests/test_detection.py`, `tests/test_tracking.py` | ✅ |

**Milestone:** Run `python -m edge.core.pipeline` → see webcam with bounding boxes + IDs + FPS. ✅

---

### Phase 2: Intelligence (Weeks 4–6) ✅ COMPLETE

> **Goal:** Decision engine + Event engine (Jarvis Core) + cloud modules.
> 
> **Completed:** 2026-04-07 | **Tests:** 49/49 passing | **Milestone:** Achieved ✅

| Task | Files | Status |
|---|---|---|
| Decision engine | `decision/engine.py`, `decision/rules.py` | ✅ |
| Event engine | `events/event_engine.py` | ✅ |
| Event actions (email, webhook, etc.) | `events/actions/*.py` | ✅ |
| OCR module | `cloud/modules/ocr.py` | ✅ |
| Face recognition module | `cloud/modules/face.py` | ✅ |
| Pose estimation module | `cloud/modules/pose.py` | ✅ |
| Counting module | `edge/modules/counting.py` | ✅ (Phase 1) |
| Measurement module | `edge/modules/measurement.py` | ✅ (Phase 1) |
| Speed estimation | `cloud/modules/speed.py` | ✅ |
| Behavior analysis | `cloud/modules/behavior.py` | ✅ |
| Segmentation | `cloud/modules/segmentation.py` | ✅ |
| Analytics engine | `cloud/analytics/engine.py` | ✅ |

**Milestone:** Define a rule "if person > 3 → send email" → receive email when triggered. ✅

---

### Phase 3: Platform (Weeks 7–9) ✅ COMPLETE

> **Goal:** FastAPI backend, auth, database, billing.
> 
> **Completed:** 2026-04-07 | **Tests:** 83/83 passing | **Milestone:** Achieved ✅
> 
> **Note:** `platform/` renamed to `server/` to avoid Python stdlib conflict.

| Task | Files | Status |
|---|---|---|
| FastAPI application | `server/api/main.py` | ✅ |
| API routes | `server/api/routes/*.py` | ✅ |
| JWT authentication | `server/auth/jwt_handler.py` | ✅ |
| OAuth2 integration | `server/auth/oauth.py` | ✅ |
| Device authentication | `server/auth/device_auth.py` | ✅ |
| RBAC + Admin takeover | `server/auth/rbac.py`, `admin_takeover.py` | ✅ |
| PostgreSQL setup | `server/db/postgres.py` | ✅ |
| Redis client | `server/db/redis_client.py` | ✅ |
| Pinecone client | `server/db/pinecone_client.py` | ✅ |
| Stripe billing | `server/billing/stripe_service.py` | ✅ |
| Feature gating | `server/billing/feature_gates.py` | ✅ |
| Rate limiting + abuse detection | `rate_limiter.py`, `abuse_detector.py` | ✅ |
| WebSocket streaming | `server/api/websockets/live_feed.py` | ✅ |
| Notification engine | `server/notifications/*` | ✅ |
| Help & support system | `server/help/*` | ✅ |
| Usage tracking service | `server/usage_tracking/*` | ✅ |
| Admin management service | `server/admin/*` | ✅ |
| Crash reporting collector | `server/crash_reporting/*` | ✅ |

**Milestone:** Full backend with auth, billing, notifications, admin, help, crash reporting, and usage tracking. ✅

---

### Phase 4: Premium UI (Weeks 10–14)

> **Goal:** Full glassmorphic dashboard with 5 themes, 3D backgrounds, 4 user modes.

| Task | Files | Status |
|---|---|---|
| Vite + React + TypeScript setup | `client/` | ✅ Done |
| Design system (CSS variables, glass components) | `client/src/index.css` | ✅ Done (10KB, 5 themes) |
| 5 Theme definitions (CSS) | `index.css` data-theme selectors | ✅ Done (in CSS) |
| Theme store + switcher | `client/src/stores/themeStore.ts` | ✅ Done (Zustand + persist) |
| App store (mode + sidebar) | `client/src/stores/appStore.ts` | ✅ Done |
| GlassCard component | `GlassCard.tsx` + `GlassCard.css` | ✅ Done (dual-mode) |
| GlassPanel component | `GlassPanel.tsx` | ✅ Done |
| GlowButton component | `GlowButton.tsx` + `GlowButton.css` | ✅ Done |
| Layout: Sidebar | `Sidebar.tsx` + `Sidebar.css` | ✅ Done |
| Layout: Header | `Header.tsx` + `Header.css` | ✅ Done |
| App.tsx (mode routing) | `App.tsx` | ✅ Done (7 modes + CrashBoundary) |
| MODE 1: Dashboard page | `Dashboard.tsx` (8.5KB) | ✅ Done |
| MODE 2: Analytics page | `Analytics.tsx` (9.3KB) | ✅ Done (recharts) |
| MODE 3: Settings page | `Settings.tsx` (9.5KB) | ✅ Done |
| MODE 4: Automation page | `Automation.tsx` (10.3KB) | ✅ Done |
| Help Center page | `HelpCenter.tsx` (10.5KB) | ✅ Done |
| TiltCard component | `TiltCard.tsx` (2.1KB) | ✅ Done |
| NeomorphicInput component | `NeomorphicInput.tsx` (1.9KB) | ✅ Done |
| React Three Fiber 3D scenes | `Scene.tsx` (1.7KB) | ✅ Done |
| Animated backgrounds (per theme) | `Background.tsx`, `FloatingObjects.tsx` | ✅ Done |
| Gaze tracking | `GazeTracker.tsx`, `useGaze.ts` | ✅ Done |
| WebSocket integration hook | `useWebSocket.ts` (2.8KB) | ✅ Done |
| Haptic feedback hook | `useHaptics.ts` (1.1KB) | ✅ Done |
| Cookie consent banner | `CookieBanner.tsx` (2.6KB) | ✅ Done |
| User Dashboard page | `UserHome.tsx` (6.3KB) | ✅ Done |
| Admin Dashboard page | `AdminDashboard.tsx` (9.0KB) | ✅ Done |
| Notification bell + panel | `NotificationPanel.tsx` (in Header + hooks) | ✅ Done |
| Offline banner + sync status | `OfflineBanner.tsx`, `SyncStatus.tsx` | ✅ Done |
| Crash Boundary | `CrashBoundary.tsx` + `useCrashReporter.ts` | ✅ Done |
| Loading/Empty/Error states | `LoadingState.tsx`, `EmptyState.tsx`, `ErrorState.tsx` | ✅ Done |
| State recovery hook | `useStateRecovery.ts` (2.3KB) | ✅ Done |
| Offline hook | `useOffline.ts` (1.4KB) | ✅ Done |
| Onboarding wizard | `OnboardingWizard.tsx` (5.6KB) | ✅ Done |
| Vision store | `visionStore.ts` (1.2KB) | ✅ Done |
| Event store | `eventStore.ts` (1.4KB) | ✅ Done |
| Auth store | `authStore.ts` (1.2KB) | ✅ Done |
| API client utility | `utils/api.ts` (2.1KB) | ✅ Done |
| App constants | `utils/constants.ts` (1.3KB) | ✅ Done |

**Milestone:** ✅ **Phase 4 COMPLETE** — All 38 items built. 7 pages, 5 themes, 13 UI components, 7 hooks, 5 stores, 4 3D components, 2 utils.

---

### Phase 5: 3D Characters (Weeks 15–16)

> **Goal:** AI character per theme with gaze tracking, expressions, and lip sync.

| Task | Files |
|---|---|
| Character `.glb` models (5 archetypes) | Asset files |
| Character renderer | `Character.tsx` |
| Gaze following (head + eyes) | `useFrame` hook |
| Morph target expressions | Expression controller |
| Lip sync (WebAudio → Visemes) | Audio analysis pipeline |
| Idle behavior (bored animation after 30s) | Idle state machine |
| Interactive tooltips (character points at hovered UI) | Tooltip integration |

**Milestone:** Character follows cursor, reacts to user interactions, changes with theme.

---

### Phase 6: Sync & Multi-Device (Weeks 17–19)

> **Goal:** Edge ↔ Cloud sync, device management, offline recovery.

| Task | Files |
|---|---|
| Sync engine | `sync/sync_engine.py` |
| Device manager | `sync/device_manager.py` |
| Offline buffer | `sync/offline_buffer.py` |
| Model manager | `cloud/ai/model_manager.py` |
| Multi-camera support | Pipeline multiplexing |
| Cross-camera tracking | Shared tracking state |

**Milestone:** Add multiple cameras, see cross-camera events, survive internet outage.

---

### Phase 7: Hardening & Polish (Weeks 20–22)

> **Goal:** Security, compliance, observability, performance optimization.

| Task | Files |
|---|---|
| Sentry integration | Error tracking setup |
| PostHog integration | Analytics setup |
| GDPR compliance | Data export/delete endpoints |
| Security hardening | Rate limiting, input validation, anti-abuse |
| Docker containers | `docker/Dockerfile.*` |
| docker-compose setup | `docker/docker-compose.yml` |
| Performance optimization | Quantization, caching, CDN |
| Load testing | Stress test API + WebSocket |
| Pre-production checklist | Run all 15 checklist categories (§31) |
| Service Worker setup | Offline caching, background sync |
| Crash recovery testing | Cold start, tab kill, refresh, offline |
| State persistence testing | Verify zero data loss across all scenarios |
| Documentation | README, API docs |

**Milestone:** Production-ready, secured, monitored, crash-resilient, offline-capable system.

---

### Phase 8: Global Deployment (Weeks 23–24)

> **Goal:** Deploy to cloud, CDN, multi-region readiness.

| Task | Files |
|---|---|
| Cloud deployment | AWS/GCP/Vercel |
| CDN setup (Cloudflare) | DNS + caching rules |
| CI/CD pipeline | GitHub Actions |
| Multi-region prep | Database replication, edge nodes |
| Mobile app foundation | React Native / Flutter scaffold |
| Edge device support | Jetson/RPi optimization |

**Milestone:** Live, globally accessible VisionX platform.

---

## 33. Verification Plan

### Automated Tests

| Test | Command |
|---|---|
| Unit tests (Python) | `pytest tests/ -v` |
| API tests | `pytest tests/test_api.py -v` |
| Frontend build | `cd client && npm run build` |
| Lint (Python) | `ruff check .` |
| Lint (TypeScript) | `cd client && npm run lint` |
| Type check | `cd client && npx tsc --noEmit` |

### Integration Tests

- Start full docker-compose stack
- Send test frames through pipeline
- Verify detection → tracking → decision → event chain
- Verify WebSocket delivers real-time updates to dashboard
- Verify Stripe webhook processes subscription changes
- ⭐ Verify crash report delivery: throw error → appears in admin dashboard < 5s
- ⭐ Verify offline queue: disconnect → perform actions → reconnect → verify sync
- ⭐ Verify state recovery: kill app → reopen → verify state restored
- ⭐ Verify admin takeover: impersonate user → verify audit log entry
- ⭐ Verify notification delivery: trigger event → verify in-app + email received
- ⭐ Verify reinstall recovery: clear localStorage → login → verify data restored

### Manual Verification

- Open dashboard, verify live camera feed with bounding boxes
- Switch between 5 themes, verify smooth transitions
- Create automation rule, verify event triggers correctly
- Test offline mode, verify sync recovery
- Test on mobile browser for responsiveness
- ⭐ Test admin dashboard: view users, takeover, crash reports, usage map
- ⭐ Test help center: search articles, submit ticket, live chat
- ⭐ Test notification preferences: toggle channels, verify delivery
- ⭐ Test onboarding wizard: complete flow as new user
- ⭐ Run all 15 pre-production checklist categories

---

## 34. Open Questions

> [!IMPORTANT]
> **Please review and provide feedback on the following decisions:**

### Architecture Decisions

1. **Starting Focus:** Should we begin with **Phase 1 (Edge Engine)** as planned, or would you prefer to start with the **UI (Phase 4)** first to have a visual prototype?

2. **YOLO Version:** Should we use **YOLOv8** (mature, well-documented) or **YOLOv9/v10** (newer, potentially better accuracy)?

3. **Tracking Algorithm:** **DeepSORT** (proven, widely used) vs **ByteTrack** (faster, fewer dependencies)?

### UI Decisions

4. **Tailwind CSS Version:** You mentioned Tailwind CSS — should we use **Tailwind v3** (stable) or **Tailwind v4** (latest, CSS-first)?

5. **3D Character Models:** Should we use:
   - **Ready Player Me** avatars (realistic, customizable)
   - **Stylized low-poly** characters (lighter, faster to load)
   - **Abstract geometric** forms (most performant, futuristic feel)

6. **3D Background Complexity:** Full Three.js particle systems, or lighter **CSS-only** animated backgrounds with a few Three.js accent elements?

### Platform Decisions

7. **Database Provider:** Self-hosted PostgreSQL, or managed (Supabase/Neon)?

8. **Deployment Target:** Primary cloud provider preference? (AWS, GCP, Vercel, self-hosted)

9. **Mobile App:** Build native mobile app now, or focus on responsive web first?

### Scope Decisions

10. **Phase Priority:** Given the scope, should we treat Phases 5–8 as "future roadmap" and focus execution on Phases 1–4 first?

---

> [!NOTE]
> This plan captures **every intention** from your raw vision **plus all new requirements**: help center, notifications, admin god-mode, feature usage tracking, user dashboard, crash resilience, state recovery, offline-first architecture, data persistence, anti-abuse/anti-hacking, and the full pre-production checklist. **Nothing has been reduced** — only organized, structured, and made actionable.
>
> The system is designed as a **distributed, device-agnostic, crash-resilient, offline-capable, admin-controllable platform** from day one.

---

*VisionX — Detect. Understand. Decide. Act.* 🧠🔥
