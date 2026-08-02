"""
VisionX — Security Unit Tests
=================================
Covers password hashing, JWT secret resolution, and RBAC dependency behaviour.

Each test here maps to a finding in ENGINEERING_REVIEW.md §8 and exists to keep
that finding fixed.
"""

from __future__ import annotations

import pytest

from server.auth.password import (
    PREFERRED_SCHEME,
    generate_password,
    hash_password,
    needs_rehash,
    verify_password,
)


# ============================================
# S1 — password hashing
# ============================================

class TestPasswordHashing:

    def test_hash_is_not_plaintext(self):
        h = hash_password("correct-horse-battery-staple")
        assert "correct-horse-battery-staple" not in h

    def test_hash_is_self_describing(self):
        assert hash_password("x" * 12).startswith(f"${PREFERRED_SCHEME}$")

    def test_verify_correct_password(self):
        h = hash_password("s3cret-passphrase")
        assert verify_password("s3cret-passphrase", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("s3cret-passphrase")
        assert verify_password("wrong-passphrase", h) is False

    def test_salted_hashes_differ(self):
        a = hash_password("same-password")
        b = hash_password("same-password")
        assert a != b
        assert verify_password("same-password", a)
        assert verify_password("same-password", b)

    def test_empty_password_rejected(self):
        with pytest.raises(ValueError):
            hash_password("")

    def test_verify_empty_inputs_false(self):
        assert verify_password("", hash_password("abc12345")) is False
        assert verify_password("abc12345", "") is False

    def test_verify_malformed_hash_returns_false(self):
        """A corrupted row must not turn into a 500 on the login path."""
        for bad in ("garbage", "$unknown$abc", "$scrypt$broken", "$bcrypt$"):
            assert verify_password("anything", bad) is False

    def test_long_password_not_silently_truncated(self):
        """
        bcrypt truncates at 72 bytes. Without SHA-256 pre-hashing, two distinct
        long passphrases sharing a 72-byte prefix would both authenticate.
        """
        base = "A" * 72
        h = hash_password(base + "-first-suffix")
        assert verify_password(base + "-first-suffix", h) is True
        assert verify_password(base + "-second-suffix", h) is False

    def test_unicode_password(self):
        pw = "パスワード-Ω-🔐"
        assert verify_password(pw, hash_password(pw)) is True

    def test_needs_rehash_on_foreign_scheme(self):
        assert needs_rehash("$md5$deadbeef") is True
        assert needs_rehash("") is True

    def test_needs_rehash_false_for_current(self):
        assert needs_rehash(hash_password("current-password")) is False

    def test_generate_password_length_and_uniqueness(self):
        a, b = generate_password(20), generate_password(20)
        assert len(a) == 20 and a != b


# ============================================
# S2 — JWT secret resolution
# ============================================

class TestJWTSecretResolution:

    def test_dev_allows_missing_secret(self, monkeypatch):
        monkeypatch.setenv("VISIONX_ENV", "development")
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

        from server.auth.jwt_handler import JWTHandler
        assert JWTHandler().secret_key  # falls back, with a warning

    def test_production_without_secret_raises(self, monkeypatch):
        monkeypatch.setenv("VISIONX_ENV", "production")
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

        from server.auth.jwt_handler import JWTHandler
        with pytest.raises(RuntimeError, match="required in production"):
            JWTHandler()

    def test_production_rejects_dev_fallback_secret(self, monkeypatch):
        from server.auth.jwt_handler import _DEV_FALLBACK_SECRET, JWTHandler

        monkeypatch.setenv("VISIONX_ENV", "production")
        monkeypatch.setenv("JWT_SECRET_KEY", _DEV_FALLBACK_SECRET)

        with pytest.raises(RuntimeError, match="development fallback"):
            JWTHandler()

    def test_production_rejects_short_secret(self, monkeypatch):
        monkeypatch.setenv("VISIONX_ENV", "production")
        monkeypatch.setenv("JWT_SECRET_KEY", "too-short")

        from server.auth.jwt_handler import JWTHandler
        with pytest.raises(RuntimeError, match="at least"):
            JWTHandler()

    def test_production_accepts_strong_secret(self, monkeypatch):
        monkeypatch.setenv("VISIONX_ENV", "production")
        monkeypatch.setenv("JWT_SECRET_KEY", "k" * 48)

        from server.auth.jwt_handler import JWTHandler
        assert JWTHandler().secret_key == "k" * 48

    def test_staging_is_treated_as_production(self, monkeypatch):
        monkeypatch.setenv("VISIONX_ENV", "staging")
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

        from server.auth.jwt_handler import JWTHandler
        with pytest.raises(RuntimeError):
            JWTHandler()


# ============================================
# Token type confusion
# ============================================

class TestTokenTypeEnforcement:

    SECRET = "test-secret-key-of-sufficient-length-for-tests"

    def test_access_token_accepted_as_access(self):
        from server.auth.jwt_handler import JWTHandler

        h = JWTHandler(secret_key=self.SECRET)
        token = h.create_access_token("user-1", "admin")
        assert h.verify_token(token, expected_type="access") is not None

    def test_refresh_token_rejected_as_access(self):
        from server.auth.jwt_handler import JWTHandler

        h = JWTHandler(secret_key=self.SECRET)
        token = h.create_refresh_token("user-1")
        assert h.verify_token(token, expected_type="access") is None

    def test_access_token_rejected_as_refresh(self):
        from server.auth.jwt_handler import JWTHandler

        h = JWTHandler(secret_key=self.SECRET)
        token = h.create_access_token("user-1")
        assert h.verify_token(token, expected_type="refresh") is None

    def test_no_expected_type_preserves_legacy_behaviour(self):
        from server.auth.jwt_handler import JWTHandler

        h = JWTHandler(secret_key=self.SECRET)
        assert h.verify_token(h.create_refresh_token("user-1")) is not None


# ============================================
# S3 — RBAC dependency
# ============================================

class TestRBACDependency:

    def test_bearer_parsing_is_case_insensitive(self):
        from server.api.dependencies import _extract_bearer

        assert _extract_bearer("Bearer abc123") == "abc123"
        assert _extract_bearer("bearer abc123") == "abc123"
        assert _extract_bearer("BEARER abc123") == "abc123"

    def test_bearer_parsing_rejects_malformed(self):
        from server.api.dependencies import _extract_bearer

        for bad in ("", "abc123", "Basic abc123", "Bearer", "Bearer   "):
            assert _extract_bearer(bad) is None

    def test_current_user_permission_check(self):
        from server.api.dependencies import CurrentUser
        from server.auth.rbac import Permission

        viewer = CurrentUser(user_id="u1", role="viewer")
        admin = CurrentUser(user_id="u2", role="super_admin")

        assert viewer.has(Permission.VIEW_FEED) is True
        assert viewer.has(Permission.MANAGE_USERS) is False
        assert admin.has(Permission.MANAGE_USERS) is True

    def test_unknown_role_has_no_permissions(self):
        from server.api.dependencies import CurrentUser
        from server.auth.rbac import Permission

        assert CurrentUser(user_id="u", role="wizard").has(Permission.VIEW_FEED) is False
