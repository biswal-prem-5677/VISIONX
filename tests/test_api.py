"""
VisionX — Platform API Tests
================================
Unit tests for auth, RBAC, billing, rate limiting, and platform services.
"""


import pytest

from server.auth.jwt_handler import JWTHandler
from server.auth.rbac import RBACChecker, Permission
from server.auth.device_auth import DeviceAuthManager
from server.auth.admin_takeover import AdminTakeover
from server.billing.feature_gates import FeatureGate
from server.api.middleware.rate_limiter import RateLimiter
from server.api.middleware.abuse_detector import AbuseDetector
from server.crash_reporting.crash_collector import CrashCollector, CrashEntry
from server.usage_tracking.tracker import UsageTracker, UsageRecord
from server.help.help_system import HelpSystem, SupportTicket


# ============================================
# JWT Handler Tests
# ============================================

class TestJWTHandler:

    def test_create_token_pair(self):
        handler = JWTHandler(secret_key="visionx-test-secret-key-minimum-32-bytes-long")
        pair = handler.create_token_pair("user-123", "user")
        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"

    def test_verify_valid_token(self):
        handler = JWTHandler(secret_key="visionx-test-secret-key-minimum-32-bytes-long")
        token = handler.create_access_token("user-123", "admin")
        payload = handler.verify_token(token)
        assert payload is not None
        assert payload.sub == "user-123"
        assert payload.role == "admin"

    def test_verify_invalid_token(self):
        handler = JWTHandler(secret_key="visionx-test-secret-key-minimum-32-bytes-long")
        payload = handler.verify_token("invalid.token.here")
        assert payload is None

    def test_revoke_token(self):
        handler = JWTHandler(secret_key="visionx-test-secret-key-minimum-32-bytes-long")
        token = handler.create_access_token("user-123")
        payload = handler.verify_token(token)
        assert payload is not None

        handler.revoke_token(payload.jti)
        payload2 = handler.verify_token(token)
        assert payload2 is None


# ============================================
# RBAC Tests
# ============================================

class TestRBAC:

    def test_viewer_permissions(self):
        assert RBACChecker.has_permission("viewer", Permission.VIEW_FEED)
        assert not RBACChecker.has_permission("viewer", Permission.MANAGE_USERS)

    def test_user_permissions(self):
        assert RBACChecker.has_permission("user", Permission.VIEW_FEED)
        assert RBACChecker.has_permission("user", Permission.VIEW_ANALYTICS)
        assert not RBACChecker.has_permission("user", Permission.MANAGE_DEVICES)

    def test_admin_permissions(self):
        assert RBACChecker.has_permission("admin", Permission.MANAGE_USERS)
        assert RBACChecker.has_permission("admin", Permission.ADMIN_DASHBOARD)
        assert not RBACChecker.has_permission("admin", Permission.ADMIN_TAKEOVER)

    def test_super_admin_all_permissions(self):
        for perm in Permission:
            assert RBACChecker.has_permission("super_admin", perm)

    def test_invalid_role(self):
        assert not RBACChecker.has_permission("hacker", Permission.VIEW_FEED)

    def test_require_permission_raises(self):
        with pytest.raises(PermissionError):
            RBACChecker.require_permission("viewer", Permission.MANAGE_USERS)


# ============================================
# Device Auth Tests
# ============================================

class TestDeviceAuth:

    def test_register_and_validate(self):
        mgr = DeviceAuthManager()
        device = mgr.register_device("cam-001", "Front Camera")
        assert mgr.validate_token("cam-001", device.token)

    def test_invalid_token(self):
        mgr = DeviceAuthManager()
        mgr.register_device("cam-001")
        assert not mgr.validate_token("cam-001", "wrong-token")

    def test_revoke_device(self):
        mgr = DeviceAuthManager()
        device = mgr.register_device("cam-001")
        mgr.revoke_device("cam-001")
        assert not mgr.validate_token("cam-001", device.token)

    def test_active_devices(self):
        mgr = DeviceAuthManager()
        mgr.register_device("cam-001")
        mgr.register_device("cam-002")
        mgr.revoke_device("cam-001")
        assert len(mgr.get_active_devices()) == 1


# ============================================
# Admin Takeover Tests
# ============================================

class TestAdminTakeover:

    def test_start_session(self):
        takeover = AdminTakeover()
        session = takeover.start_session("admin-1", "user-1", "super_admin", "Debug")
        assert session is not None
        assert takeover.is_impersonating("admin-1") == "user-1"

    def test_non_super_admin_denied(self):
        takeover = AdminTakeover()
        session = takeover.start_session("admin-1", "user-1", "admin", "Debug")
        assert session is None

    def test_end_session(self):
        takeover = AdminTakeover()
        takeover.start_session("admin-1", "user-1", "super_admin")
        takeover.end_session("admin-1")
        assert takeover.is_impersonating("admin-1") is None

    def test_audit_log(self):
        takeover = AdminTakeover()
        takeover.start_session("admin-1", "user-1", "super_admin")
        takeover.log_action("admin-1", "viewed_dashboard")
        takeover.end_session("admin-1")

        log = takeover.get_audit_log()
        assert len(log) == 1
        assert len(log[0].actions_log) == 1


# ============================================
# Feature Gate Tests
# ============================================

class TestFeatureGate:

    def test_free_plan_limits(self):
        gate = FeatureGate()
        gate.set_user_plan("user-1", "free")
        assert gate.check_device_limit("user-1", 0)
        assert not gate.check_device_limit("user-1", 1)
        assert not gate.has_cloud_modules("user-1")

    def test_pro_plan_features(self):
        gate = FeatureGate()
        gate.set_user_plan("user-1", "pro")
        assert gate.has_cloud_modules("user-1")
        assert gate.has_api_access("user-1")
        assert gate.check_device_limit("user-1", 4)

    def test_default_free(self):
        gate = FeatureGate()
        plan = gate.get_user_plan("unknown-user")
        assert plan.id == "free"


# ============================================
# Rate Limiter Tests
# ============================================

class TestRateLimiter:

    def test_allows_within_limit(self):
        limiter = RateLimiter(requests_per_minute=10)
        allowed, _ = limiter.check("user-1")
        assert allowed

    def test_blocks_over_limit(self):
        limiter = RateLimiter(requests_per_minute=3, requests_per_hour=100)
        for _ in range(3):
            limiter.check("user-1")

        allowed, headers = limiter.check("user-1")
        assert not allowed
        assert headers["X-RateLimit-Remaining-Minute"] == 0

    def test_different_keys_independent(self):
        limiter = RateLimiter(requests_per_minute=2)
        limiter.check("user-1")
        limiter.check("user-1")
        limiter.check("user-1")  # blocked

        allowed, _ = limiter.check("user-2")
        assert allowed


# ============================================
# Abuse Detector Tests
# ============================================

class TestAbuseDetector:

    def test_not_blocked_initially(self):
        detector = AbuseDetector()
        assert not detector.is_blocked("user-1")

    def test_blocks_after_failures(self):
        detector = AbuseDetector(max_auth_failures=3)
        detector.record_auth_failure("user-1")
        detector.record_auth_failure("user-1")
        blocked = detector.record_auth_failure("user-1")
        assert blocked
        assert detector.is_blocked("user-1")

    def test_unblock(self):
        detector = AbuseDetector(max_auth_failures=1)
        detector.record_auth_failure("user-1")
        assert detector.is_blocked("user-1")
        detector.unblock("user-1")
        assert not detector.is_blocked("user-1")


# ============================================
# Crash Collector Tests
# ============================================

class TestCrashCollector:

    def test_submit_crash(self):
        collector = CrashCollector()
        crash = CrashEntry(
            crash_id="crash-1",
            error_message="NullPointerException",
            user_id="user-1",
        )
        collector.submit(crash)
        assert collector.get_stats()["total_reports"] == 1

    def test_top_crashes(self):
        collector = CrashCollector()
        for i in range(5):
            collector.submit(CrashEntry(
                crash_id=f"crash-{i}",
                error_message="Same error",
                user_id=f"user-{i}",
            ))
        tops = collector.get_top_crashes(limit=1)
        assert tops[0]["count"] == 5
        assert tops[0]["affected_users"] == 5


# ============================================
# Usage Tracker Tests
# ============================================

class TestUsageTracker:

    def test_track_feature(self):
        tracker = UsageTracker()
        tracker.track(UsageRecord(
            user_id="user-1",
            feature="detection",
            action="toggle",
        ))
        assert tracker.get_stats()["total_records"] == 1

    def test_top_features(self):
        tracker = UsageTracker()
        for _ in range(3):
            tracker.track(UsageRecord(
                user_id="user-1", feature="detection", action="view"
            ))
        tracker.track(UsageRecord(
            user_id="user-1", feature="analytics", action="view"
        ))

        tops = tracker.get_top_features(limit=1)
        assert tops[0]["feature"] == "detection"
        assert tops[0]["count"] == 3


# ============================================
# Help System Tests
# ============================================

class TestHelpSystem:

    def test_search_articles(self):
        help_sys = HelpSystem()
        results = help_sys.search_articles("camera")
        assert len(results) > 0

    def test_create_ticket(self):
        help_sys = HelpSystem()
        ticket = help_sys.create_ticket(SupportTicket(
            user_id="user-1",
            subject="Camera not working",
            description="My webcam shows black screen",
        ))
        assert ticket.id.startswith("TICKET-")
        assert ticket.status == "open"

    def test_update_ticket_status(self):
        help_sys = HelpSystem()
        ticket = help_sys.create_ticket(SupportTicket(
            user_id="user-1",
            subject="Test",
            description="Test",
        ))
        help_sys.update_ticket_status(ticket.id, "resolved")
        updated = help_sys.get_user_tickets("user-1")
        assert updated[0].status == "resolved"
