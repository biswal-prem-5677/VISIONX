# VisionX — Execution Tracker

**Status:** Living record. Updated in the same change as the work it describes.
**Governing rules:** [EXECUTION_RULES.md](EXECUTION_RULES.md)
**Source of findings:** [ENGINEERING_REVIEW.md](ENGINEERING_REVIEW.md) (audit at commit `fe5f055`)

> **Definition of Done (R0):** Reachable · Correct · Tested · Gated · Recorded.
> A row is `Fixed` only when all five hold. Nothing is ever deleted from this
> file — superseded rows are struck through and annotated.

> **Honesty note (R10).** This file was created at the *end* of Run 1, not
> during it. Rows DEF-001 … DEF-020 are therefore reconstructed from the working
> tree and the review, not recorded as the work happened. From Run 2 onward,
> rows are opened the moment a defect is found, per R4.

---

## Status legend

| Mark | Meaning |
|---|---|
| ✅ Fixed | Satisfies R0 in full |
| 🟡 Partial | Improved, but does not yet satisfy R0 — successor row named |
| ⬜ Open | Found, logged, not started |
| 🔵 Deferred | Deliberately not now, with a reason |

---

## Defects

### Security — R6 class (fixed before feature work)

| ID | Sev | Defect | Evidence | Status | Verification |
|---|---|---|---|---|---|
| DEF-001 | 🔴 Critical | Passwords stored and compared in **plaintext**; hardcoded `admin123` super-admin | review S1 · `auth.py:61,76,105` | ✅ Fixed | `server/auth/password.py` (bcrypt, scrypt fallback, SHA-256 pre-hash, timing-safe verify). Bootstrap admin now from `BOOTSTRAP_ADMIN_PASSWORD`; generates a random one-time credential and logs it if unset. `test_http.py::test_legacy_hardcoded_password_no_longer_works` |
| DEF-002 | 🔴 Critical | **JWT secret fails open** — silently defaults to a secret published in this repo | review S2 · `jwt_handler.py:49` | ✅ Fixed | `_resolve_secret()` raises `RuntimeError` at construction in production for missing / fallback / <32-char secrets. Dev keeps the fallback with a warning. `test_security.py` |
| DEF-003 | 🔴 Critical | **RBAC never enforced** — `rbac.py` fully implemented and tested, called by zero route handlers; each route hand-parsed `Authorization` | review S3 · `rbac.py` vs `routes/*.py` | ✅ Fixed | `server/api/dependencies.py` — `get_current_user` / `require_permission`. All 12 routers now declare an auth posture. `test_http.py`, `test_security.py` |
| DEF-004 | 🟠 High | **Governance privacy policy inverted** — `blocked_actions` evaluated before `blocked_zones` and returned immediately, so `face_recognition` / `record_video` were blocked in **every** zone, not just private ones. Made `biometric_consent` unreachable dead code | review S5 · `governance.py:139-172` | ✅ Fixed | `_policy_applies()` scope gate runs first. `tests/test_governance.py` (250 lines) covers zone scoping and the previously-unreachable consent policy |
| DEF-005 | 🟡 Medium | **SSRF** — webhook / api_call / iot actions fetched user-supplied URLs with no allowlist or private-range block | review A10, R18 | ✅ Fixed | `shared/url_safety.py` → `validate_outbound_url()`, wired into all three actions. `tests/test_security.py` |
| DEF-006 | 🟠 High | A 30-day **refresh token authenticated normal requests** — no token-type separation | found during DEF-003 | ✅ Fixed | Token `type` claim asserted on verify. `test_http.py::test_refresh_token_cannot_be_used_as_access_token` |
| DEF-016 | 🔴 Critical | `passlib[bcrypt]` declared in requirements and **never imported**; also broken with `bcrypt>=4.1` (raises on any input) — root cause of DEF-001 | review §12 | ✅ Fixed | Replaced with `bcrypt>=4.1.0` in `requirements.txt` + `requirements-ci.txt`; `password.py` documents why passlib was dropped rather than pinned |

### Reachability — code that read as shipped but could not run

| ID | Sev | Defect | Evidence | Status | Verification |
|---|---|---|---|---|---|
| DEF-007 | 🟠 High | **5 of 12 routers never mounted** (billing, config, help, notifications, usage_tracking) — dead code presenting as features | review §5 · `main.py:148-154` | ✅ Fixed | All 12 mounted. `test_http.py::TestRouterMounting` parametrized over every prefix — a regression guard, not a one-time fix |
| DEF-008 | 🟠 High | **No WebSocket endpoint existed.** `ws_manager` referenced nowhere; frontend dialled `/ws/vision` → connection refused. The core UX of the product did not function | review §3, R13 · `live_feed.py:119` | ✅ Fixed | `@app.websocket("/ws/vision")` in `main.py:177`. `test_http.py::TestWebSocket` connects over a real socket (status, ping/pong, subscribe, unsubscribe) |
| DEF-009 | 🟠 High | **nginx `proxy_pass` trailing slash stripped the `/api` prefix** — `/api/v1/auth/login` reached the backend as `/v1/auth/login`. Every API call would have 404'd in production | found while fixing DEF-008 | ✅ Fixed | `docker/nginx.conf` — slash removed, reason documented inline. Not covered by an automated test (needs a container); noted as a gap in DEF-024 |
| DEF-010 | 🟡 Medium | Client `API_BASE` hardcoded `http://localhost:8000/api/v1` — bypassed both proxies, broke anywhere but a dev laptop | `client/src/utils/api.ts:6` | ✅ Fixed | Same-origin `/api/v1` default; `VITE_API_URL` still overrides |
| DEF-011 | 🟡 Medium | **No Vite dev proxy** for `/api` or `/ws` — `useVisionStream` dialled the Vite server itself, so the live feed silently never connected in development | found while fixing DEF-010 | ✅ Fixed | `client/vite.config.ts` proxies both, `ws: true`, mirroring nginx |
| DEF-021 | 🟠 High | `/api/v1/events` and `/events/stats` returned hardcoded `{"events": [], "total": 0}` **from no backing store** — an absent store was indistinguishable from an absence of events | found this run (R5) | ✅ Fixed | Both return `501` with `{code, message, tracker_id}`. `test_http.py::TestEventEndpointsAreHonest` asserts the 200-with-`total:0` regression cannot return |

### Reliability — R7 class (fail loud, not silent)

| ID | Sev | Defect | Evidence | Status | Verification |
|---|---|---|---|---|---|
| DEF-013 | 🔴 Critical | **Failed actions were logged and discarded** — no retry, no dead-letter queue. For an alerting product a silently dropped alert is the worst failure mode: the customer believes the system is working | review §13.1 · `event_engine.py:141-164` | 🟡 Partial | Bounded retry (3 attempts, exponential backoff) + in-memory dead-letter queue (`deque(maxlen=500)`, R8) + `replay_dead_letters()`. `test_events.py` covers permanent failure, transient recovery, and unregistered actions. **Not durable** — see DEF-022. **Not inspectable via the API** — see DEF-023 |
| DEF-014 | 🟠 High | An `async def execute()` action handler would be submitted to a thread pool, return a coroutine that was never awaited, and be **recorded as a success**. The alert never sent | found while fixing DEF-013 | ✅ Fixed | `register_action()` rejects async handlers; `_dispatch_action` raises `TypeError` on a returned awaitable and closes it. `test_events.py` |
| DEF-015 | 🟡 Medium | No executor shutdown — interpreter exit could kill a worker mid-action, leaving a half-sent alert recorded neither way | found while fixing DEF-013 | ✅ Fixed | `EventEngine.shutdown(wait=True)` drains in-flight dispatches |
| DEF-012 | 🟡 Medium | Two hand-built JSON error strings inconsistent with FastAPI's shape; no request correlation | review §5 · `main.py:78,87` | ✅ Fixed | Single `_error_response()` emitting `{error: {code, message, request_id}}`; `X-Request-ID` accepted and echoed on every response. `test_http.py` |

### Testing

| ID | Sev | Defect | Evidence | Status | Verification |
|---|---|---|---|---|---|
| DEF-017 | 🟠 High | **"95 tests passing" was cited as production evidence; all 95 were unit tests.** `test_api.py` instantiated service classes and never issued an HTTP request. Zero endpoints had ever been tested — which is exactly how DEF-007 and DEF-008 survived CI | review §21 | ✅ Fixed | `tests/test_http.py` (49 tests) drives the real ASGI app over HTTP and a real WebSocket. Suite **95 → 191** |

### Documentation — R9 class (docs must not outrun the code)

| ID | Sev | Defect | Evidence | Status | Verification |
|---|---|---|---|---|---|
| DEF-018 | 🟠 High | README claimed "Phases 1–7 ✅ Complete" while 5 routers were unmounted, the WebSocket did not exist, and nothing persisted. Reality was ≈ Phase 2 | review R17 | ✅ Fixed | README carries a pre-production warning, a Done-definition, and a roadmap table with explicit ⬜ Not built rows for persistence, tenancy, object storage |
| DEF-019 | 🟠 High | `implementation_plan.md` (4,543 lines, 72 sections) read as a work queue; §51–§72 (~2,400 lines) have zero implementation and describe infrastructure for a company ~100× this size | review §21, R7 | ✅ Fixed | Marked **non-binding long-term vision** at the top, pointing to MASTER_BLUEPRINT for reality |
| DEF-020 | 🟡 Medium | `EXECUTION_RULES.md` links to `EXECUTION_TRACKER.md`, which **did not exist**. R4 was therefore unenforceable | found this run (R5) | ✅ Fixed | This file |

---

## Open

| ID | Sev | Defect | Why it is still open | Owner |
|---|---|---|---|---|
| DEF-022 | 🔴 Critical | **Dead-letter queue is in-memory** — a process restart loses every pending retry and every dead letter. DEF-013 reduced the blast radius; it did not make delivery durable | Requires the `events` / `event_actions` tables. Blocked on DEF-025 | Platform |
| DEF-023 | 🟠 High | **Dead letters are not inspectable or replayable via the API** — an operator cannot see that alerts were dropped | The API process owns no `EventEngine` instance; the edge process that does has no persistence to read back from. Needs the transport decision in DEF-025 | Platform |
| DEF-025 | 🔴 Critical | **No persistence and no multi-tenancy** — no schema, no models, no migrations, no `org_id` anywhere. Nothing survives a restart | The 9-table schema + Alembic + RLS is the next unit of work (review §4.2, MASTER_BLUEPRINT Phase 1). Retrofitting tenancy later is a 6–10 week refactor | Platform |
| DEF-026 | 🟡 Medium | Access token stored in `localStorage` → XSS-exfiltratable; no documented CSRF position | review S8 · `client/src/utils/api.ts:27` | Frontend |
| DEF-027 | 🟢 Low | CSP allows `'unsafe-inline'` for `script-src` | review S10 · `docker/nginx.conf:18` | Frontend |
| DEF-028 | 🟠 High | Camera credentials unencrypted — RTSP URLs embed `user:password@`, no encryption-at-rest design | review S6 · `edge/core/camera.py` | Platform |
| DEF-029 | 🟡 Medium | Audit / governance logs are in-memory lists that vanish on restart | review S9 · `governance.py:69` | Platform |
| DEF-024 | 🟡 Medium | Rate limiter and abuse detector are per-process in-memory — ineffective above one replica. Also: no test covers the nginx routing fixed in DEF-009 (needs a container test) | review S7, R15 | Platform |
| DEF-030 | 🔴 Critical | **Ultralytics YOLOv8 is AGPL-3.0** while the repo ships MIT. Unresolved commercial-distribution conflict | Legal/founder decision: buy the commercial licence or migrate to a permissive detector. Not an engineering fix | Founder + Counsel |
| DEF-031 | 🟢 Low | 6.5 MB `yolov8n.pt` committed to git | Should be a release artifact or object-storage download | Platform |
| DEF-032 | 🟠 High | **No detection-quality measurement** — no mAP/precision/recall harness, no labeled validation set, no false-positive feedback. False positives are the #1 churn cause in this category and cannot currently be measured | review §6.1 | Product + ML |

## Deferred

| ID | Defect | Reason |
|---|---|---|
| DEF-033 | 47 features for ≤3 engineers; review recommends deleting 13 (3D characters, face recognition, cross-camera re-ID, behavior/pose/segmentation/speed, Pinecone, model hot-swap, help centre, crash reporting, admin takeover, IoT/hardware/alarm actions) | 🔵 Deferred — deletion is a **product scope decision**, not an engineering one, and depends on the unanswered M1/M3/M6/M8 questions in ENGINEERING_REVIEW §0. Logged so it is not forgotten; not actioned unilaterally |

---

## Run log

### Run 1 — 2026-08-02 · Security, reachability, and honesty pass

| | |
|---|---|
| **Scope** | ENGINEERING_REVIEW findings S1–S3, S5, A10; unmounted routers; missing WebSocket transport; silent action loss; doc/reality gap |
| **Closed** | DEF-001 … DEF-012, DEF-014 … DEF-021 (19 rows). DEF-013 partial |
| **Opened** | DEF-022 … DEF-033 (12 rows) |
| **Tests** | 95 → **191** (`+49` HTTP/WebSocket, `+` governance, security, retry/DLQ) |
| **Gates (R3)** | ✅ `pytest -q` 191 passed · ✅ `ruff check . --select E,W,F --ignore E501` · ✅ `npx tsc --noEmit` · ✅ `npm run build` — all four executed on Windows, all green |
| **Not verified** | The nginx fix (DEF-009) was reasoned from the nginx `proxy_pass` prefix-replacement rule and reviewed by inspection — **it was not exercised against a running container.** Logged as part of DEF-024 |
| **Outcome** | The three critical security findings are closed and the product's core UX (live feed) functions for the first time. **The platform layer is untouched** — the project remains pre-production and non-durable. Reality score movement is in security and reachability only |

---

## Change log for this file

| Date | Change |
|---|---|
| 2026-08-02 | Created (DEF-020). Run 1 recorded retroactively; R4 applies prospectively from Run 2 |
