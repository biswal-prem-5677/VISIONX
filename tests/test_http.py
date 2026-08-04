"""
VisionX — HTTP / WebSocket Integration Tests
================================================
Exercises the FastAPI application over real HTTP and WebSocket transport.

Why this file exists
--------------------
Before it, the suite had 95 passing tests and **zero** that issued a request.
``test_api.py`` instantiates service classes directly, so an unmounted router,
a broken dependency, or a missing WebSocket route passed CI unnoticed — which
is exactly how five routers and the entire live feed ended up unreachable.

These tests assert *reachability and contract*, not business depth.
"""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

# The app must import with a deterministic bootstrap admin.
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "test-admin-password-123")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "admin@visionx.ai")
os.environ.setdefault("VISIONX_ENV", "development")

# DATABASE_URL is deliberately *not* set here. It has to be exported before
# ``server.db.session`` is first imported by any module, which is earlier than
# this file — see the note at the top of ``tests/conftest.py``.

fastapi_testclient = pytest.importorskip(
    "fastapi.testclient", reason="fastapi/httpx required for HTTP tests"
)

from fastapi.testclient import TestClient  # noqa: E402

from server.api.main import app  # noqa: E402

ADMIN_EMAIL = "admin@visionx.ai"
ADMIN_PASSWORD = "test-admin-password-123"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_token(client) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ============================================
# System endpoints
# ============================================

class TestSystemEndpoints:

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "VisionX Platform API"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert "websocket_connections" in body

    def test_openapi_schema_builds(self, client):
        """A router with a malformed signature breaks schema generation."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        assert "paths" in resp.json()

    def test_request_id_header_present(self, client):
        resp = client.get("/health")
        assert resp.headers.get("X-Request-ID")
        assert resp.headers.get("X-Response-Time-Ms")

    def test_request_id_is_echoed(self, client):
        resp = client.get("/health", headers={"X-Request-ID": "trace-me-123"})
        assert resp.headers["X-Request-ID"] == "trace-me-123"


# ============================================
# Database wiring — DEF-025 reachability
# ============================================

class TestDatabaseIsWiredIntoTheApp:
    """
    The persistence layer must be *reached* by the application, not merely
    present in the tree.

    ``server/db`` was written as a complete unit — schema, migrations, RLS,
    repositories, 81 tests — and imported by nothing outside its own tests. That
    is precisely the failure this repository has already shipped twice: five
    routers that were never mounted and a WebSocket manager referenced from
    nowhere (DEF-007, DEF-008). Code that only tests call is not reachable, and
    under R0 it is not done.

    These tests run over real HTTP against the real lifespan, so a future edit
    that drops ``database.connect()`` from startup fails here rather than in
    production.
    """

    def test_lifespan_connects_the_engine(self, client):
        """``connect()`` runs on startup, not lazily on the first query."""
        from server.db.session import database

        assert database.is_connected

    def test_health_reports_the_database_it_actually_pinged(self, client):
        body = client.get("/health").json()
        assert body["services"]["database"] == "up"
        assert body["status"] == "healthy"

    def test_health_reports_degraded_when_the_database_is_unreachable(
        self, client, monkeypatch
    ):
        """
        The regression this guards: reporting ``healthy`` from the mere presence
        of an engine object. The entry has to come from a query that ran.
        """
        from server.db.session import database

        async def unreachable() -> bool:
            return False

        monkeypatch.setattr(database, "ping", unreachable)

        resp = client.get("/health")
        body = resp.json()

        assert body["services"]["database"] == "down"
        assert body["status"] == "degraded"

        # Still 200: this endpoint is the container healthcheck, and restarting
        # the API does not repair the database. See the docstring on health_check.
        assert resp.status_code == 200

    def test_admin_health_reports_the_real_database_too(self, client, admin_token):
        """The admin view once hardcoded ``not_configured`` for both entries."""
        body = client.get(
            "/api/v1/admin/health",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).json()

        assert body["services"]["database"] == "up"
        # Redis genuinely is not connected by anything — saying so is the honest
        # answer, and inventing "up" is the bug this replaced (DEF-024).
        assert body["services"]["redis"] == "not_configured"

    def test_shutdown_disposes_the_engine(self):
        """
        A pool abandoned to the garbage collector holds server-side connections
        open until they time out. Uses its own client so the module-scoped one
        stays connected for every other test.
        """
        from server.db.session import Database

        import server.api.main as main_module

        with tempfile.TemporaryDirectory() as tmp:
            isolated = Database(f"sqlite+aiosqlite:///{Path(tmp) / 'shutdown.db'}")

            with monkeypatched(main_module, "database", isolated):
                with TestClient(main_module.app):
                    assert isolated.is_connected
                assert not isolated.is_connected


@contextmanager
def monkeypatched(module, name: str, value):
    """
    Swap a module attribute for the duration of a block.

    ``monkeypatch`` is function-scoped and undoes itself at teardown, which is
    after the ``TestClient`` context exits — too late to assert on what shutdown
    did. This unwinds in the order the assertion needs.
    """
    original = getattr(module, name)
    setattr(module, name, value)
    try:
        yield value
    finally:
        setattr(module, name, original)


# ============================================
# Router mounting — regression guard
# ============================================

class TestRouterMounting:
    """
    Guards the defect where billing/config/help/notifications/usage_tracking
    each defined an APIRouter that was never included in the app.
    """

    EXPECTED_PREFIXES = [
        "/api/v1/auth",
        "/api/v1/vision",
        "/api/v1/events",
        "/api/v1/devices",
        "/api/v1/analytics",
        "/api/v1/admin",
        "/api/v1/billing",
        "/api/v1/config",
        "/api/v1/help",
        "/api/v1/notifications",
        "/api/v1/usage",
    ]

    @pytest.mark.parametrize("prefix", EXPECTED_PREFIXES)
    def test_router_is_mounted(self, client, prefix):
        paths = client.get("/openapi.json").json()["paths"]
        assert any(p.startswith(prefix) for p in paths), (
            f"No routes mounted under {prefix} — router is defined but not included"
        )

    def test_websocket_route_registered(self):
        routes = {getattr(r, "path", None) for r in app.routes}
        assert "/ws/vision" in routes


# ============================================
# Authentication
# ============================================

class TestAuthEndpoints:

    def test_login_success(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"] and body["refresh_token"]
        assert body["token_type"] == "bearer"

    def test_login_wrong_password_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrong-password"},
        )
        assert resp.status_code == 401

    def test_legacy_hardcoded_password_no_longer_works(self, client):
        """The removed hardcoded `admin123` credential must stay dead."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": "admin123"},
        )
        assert resp.status_code == 401

    def test_login_unknown_user_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "whatever"},
        )
        assert resp.status_code == 401

    def test_email_is_normalized(self, client):
        """Mixed case and surrounding whitespace must resolve to the same account."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "  ADMIN@VisionX.ai  ", "password": ADMIN_PASSWORD},
        )
        assert resp.status_code == 200

    def test_invalid_email_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "x"},
        )
        assert resp.status_code == 422

    def test_register_then_login(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "a-good-password",
                "name": "New User",
            },
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["role"] == "user"

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "newuser@example.com", "password": "a-good-password"},
        )
        assert login.status_code == 200

    def test_register_duplicate_rejected(self, client):
        payload = {"email": "dupe@example.com", "password": "a-good-password"}
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post("/api/v1/auth/register", json=payload).status_code == 409

    def test_register_short_password_rejected(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "shortpw@example.com", "password": "abc"},
        )
        assert resp.status_code == 422

    def test_me_requires_auth(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_rejects_malformed_header(self, client):
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": "NotBearer abc"}
        )
        assert resp.status_code == 401

    def test_me_rejects_garbage_token(self, client):
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
        )
        assert resp.status_code == 401

    def test_me_with_valid_token(self, client, admin_token):
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == ADMIN_EMAIL
        assert resp.json()["role"] == "super_admin"

    def test_refresh_token_cannot_be_used_as_access_token(self, client):
        """A 30-day refresh token must not authenticate a normal request."""
        tokens = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        ).json()

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        )
        assert resp.status_code == 401

    def test_refresh_rotates_tokens(self, client):
        tokens = client.post(
            "/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        ).json()

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    def test_refresh_rejects_access_token(self, client, admin_token):
        resp = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": admin_token}
        )
        assert resp.status_code == 401

    def test_password_never_returned(self, client, admin_token):
        resp = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"}
        )
        body = resp.text.lower()
        assert "password" not in body
        assert ADMIN_PASSWORD not in resp.text


# ============================================
# Unimplemented endpoints — honesty guard
# ============================================

class TestEventEndpointsAreHonest:
    """
    Guards the defect where `/api/v1/events` returned a hardcoded
    ``{"events": [], "total": 0}`` from no backing store.

    For an alerting product an empty result and a query that never ran must
    never be indistinguishable, so these endpoints answer 501 until the
    persistent `events` table exists (DEF-021).
    """

    PATHS = ["/api/v1/events/", "/api/v1/events/stats"]

    @pytest.mark.parametrize("path", PATHS)
    def test_requires_auth_before_anything_else(self, client, path):
        assert client.get(path).status_code == 401

    @pytest.mark.parametrize("path", PATHS)
    def test_reports_not_implemented(self, client, admin_token, path):
        resp = client.get(
            path, headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 501, resp.text
        detail = resp.json()["detail"]
        assert detail["code"] == "not_implemented"
        assert detail["tracker_id"] == "DEF-021"

    def test_does_not_return_a_fake_empty_result(self, client, admin_token):
        """The specific regression: 200 + `total: 0` from a nonexistent store."""
        resp = client.get(
            "/api/v1/events/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code != 200
        assert "total" not in resp.json()


# ============================================
# WebSocket transport
# ============================================

class TestWebSocket:

    def test_connect_receives_status(self, client):
        with client.websocket_connect("/ws/vision") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "status"
            assert "connection_id" in msg
            assert "events" in msg["subscribed"]

    def test_ping_pong(self, client):
        with client.websocket_connect("/ws/vision") as ws:
            ws.receive_json()  # status
            ws.send_json({"type": "ping"})
            assert ws.receive_json()["type"] == "pong"

    def test_subscribe_acknowledged(self, client):
        with client.websocket_connect("/ws/vision") as ws:
            ws.receive_json()
            ws.send_json({"type": "subscribe", "channel": "live:cam-1"})
            msg = ws.receive_json()
            assert msg["type"] == "subscribed"
            assert msg["channel"] == "live:cam-1"

    def test_unsubscribe_acknowledged(self, client):
        with client.websocket_connect("/ws/vision") as ws:
            ws.receive_json()
            ws.send_json({"type": "subscribe", "channel": "live:cam-2"})
            ws.receive_json()
            ws.send_json({"type": "unsubscribe", "channel": "live:cam-2"})
            assert ws.receive_json()["type"] == "unsubscribed"

    def test_invalid_json_does_not_close_socket(self, client):
        with client.websocket_connect("/ws/vision") as ws:
            ws.receive_json()
            ws.send_text("{not json")
            assert ws.receive_json()["type"] == "error"
            # Socket must still be usable.
            ws.send_json({"type": "ping"})
            assert ws.receive_json()["type"] == "pong"

    def test_unknown_message_type_errors_gracefully(self, client):
        with client.websocket_connect("/ws/vision") as ws:
            ws.receive_json()
            ws.send_json({"type": "nonsense"})
            assert ws.receive_json()["type"] == "error"

    def test_subscribe_without_channel_errors(self, client):
        with client.websocket_connect("/ws/vision") as ws:
            ws.receive_json()
            ws.send_json({"type": "subscribe"})
            assert ws.receive_json()["type"] == "error"

    def test_disconnect_is_cleaned_up(self, client):
        from server.api.websockets.live_feed import ws_manager

        before = ws_manager.connection_count
        with client.websocket_connect("/ws/vision") as ws:
            ws.receive_json()
            assert ws_manager.connection_count == before + 1
        assert ws_manager.connection_count == before


# ============================================
# Error envelope
# ============================================

class TestErrorHandling:

    def test_unknown_route_404(self, client):
        assert client.get("/api/v1/definitely-not-a-route").status_code == 404

    def test_health_is_never_rate_limited(self, client):
        """Probes must not be throttled or an orchestrator will kill a live pod."""
        for _ in range(80):
            assert client.get("/health").status_code == 200
