"""
VisionX — Governance Validator Tests
========================================
Covers the ethics/privacy gate between the Decision Engine and Event Engine.

Central regression: the built-in ``privacy_zones`` policy declares both
``blocked_zones`` and ``blocked_actions``. The action check previously ran first
and returned unconditionally, so biometric actions were blocked in *every* zone
rather than only in the restricted ones — and the ``biometric_consent`` policy
became unreachable. See ENGINEERING_REVIEW.md §8 finding S5.
"""

from __future__ import annotations

from decision.governance import (
    GovernancePolicy,
    GovernanceValidator,
    GovernanceVerdict,
)
from decision.rules import RuleResult, RuleSeverity


def _result(actions: list[str], severity: RuleSeverity = RuleSeverity.WARNING) -> RuleResult:
    return RuleResult(
        rule_id="rule-1",
        rule_name="Test Rule",
        triggered=True,
        severity=severity,
        actions=actions,
        matched_conditions=["person_count > 5"],
    )


def _bare_validator() -> GovernanceValidator:
    """Validator with the built-in defaults removed, for isolated policy tests."""
    v = GovernanceValidator()
    v._policies.clear()
    return v


# ============================================
# S5 — zone scoping regression
# ============================================

class TestZoneScoping:

    def test_biometric_action_allowed_outside_private_zone(self):
        """
        The regression: face_recognition in the lobby must be APPROVED. The
        privacy_zones policy is scoped to bathroom/changing_room/private_office.
        """
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["face_recognition"])],
            context={"zone": "lobby", "user_consent": True, "max_confidence": 0.9},
        )
        assert len(approved) == 1
        assert approved[0].actions == ["face_recognition"]

    def test_biometric_action_blocked_inside_private_zone(self):
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["face_recognition"])],
            context={"zone": "bathroom", "user_consent": True, "max_confidence": 0.9},
        )
        assert approved == []

    def test_record_video_blocked_only_in_private_zone(self):
        v = GovernanceValidator()

        in_private = v.validate(
            [_result(["record_video"])],
            context={"zone": "changing_room", "user_consent": True, "max_confidence": 0.9},
        )
        assert in_private == []

        in_public = v.validate(
            [_result(["record_video"])],
            context={"zone": "warehouse_floor", "user_consent": True, "max_confidence": 0.9},
        )
        assert len(in_public) == 1

    def test_partial_block_in_private_zone_is_modified(self):
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["face_recognition", "send_email"])],
            context={"zone": "private_office", "user_consent": True, "max_confidence": 0.9},
        )
        assert len(approved) == 1
        assert approved[0].actions == ["send_email"]

    def test_zone_only_policy_blocks_everything_in_scope(self):
        v = _bare_validator()
        v.add_policy(GovernancePolicy(
            id="no_alerts_in_vault",
            name="Vault Silence",
            blocked_zones=["vault"],
        ))

        assert v.validate([_result(["send_email"])], context={"zone": "vault"}) == []
        assert len(v.validate([_result(["send_email"])], context={"zone": "lobby"})) == 1

    def test_global_policy_applies_everywhere(self):
        """A policy with no blocked_zones is unscoped and applies in all zones."""
        v = _bare_validator()
        v.add_policy(GovernancePolicy(
            id="no_sms_ever",
            name="No SMS",
            blocked_actions=["send_sms"],
        ))

        for zone in ("lobby", "bathroom", ""):
            assert v.validate([_result(["send_sms"])], context={"zone": zone}) == []


# ============================================
# Consent policy reachability
# ============================================

class TestConsentPolicy:

    def test_consent_policy_is_reachable(self):
        """
        Previously dead code: privacy_zones matched the same biometric actions
        first and always returned, so biometric_consent never ran.
        """
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["face_recognition"])],
            context={"zone": "lobby", "user_consent": False, "max_confidence": 0.9},
        )
        assert approved == []

    def test_consent_granted_allows_biometrics(self):
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["face_recognition"])],
            context={"zone": "lobby", "user_consent": True, "max_confidence": 0.9},
        )
        assert len(approved) == 1

    def test_consent_partial_removes_only_biometric_actions(self):
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["face_recognition", "log_event"])],
            context={"zone": "lobby", "user_consent": False, "max_confidence": 0.9},
        )
        assert len(approved) == 1
        assert approved[0].actions == ["log_event"]

    def test_non_biometric_action_unaffected_by_consent(self):
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["send_email"])],
            context={"zone": "lobby", "user_consent": False, "max_confidence": 0.9},
        )
        assert len(approved) == 1


# ============================================
# Confidence gate
# ============================================

class TestConfidenceGate:

    def test_low_confidence_blocked(self):
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["send_email"])],
            context={"zone": "lobby", "user_consent": True, "max_confidence": 0.2},
        )
        assert approved == []

    def test_high_confidence_approved(self):
        v = GovernanceValidator()
        approved = v.validate(
            [_result(["send_email"])],
            context={"zone": "lobby", "user_consent": True, "max_confidence": 0.95},
        )
        assert len(approved) == 1


# ============================================
# Severity cap
# ============================================

class TestSeverityCap:

    def test_severity_above_cap_blocked(self):
        v = _bare_validator()
        v.add_policy(GovernancePolicy(
            id="cap", name="Severity Cap", max_severity=RuleSeverity.WARNING,
        ))
        assert v.validate([_result(["send_email"], RuleSeverity.EMERGENCY)], context={}) == []

    def test_severity_at_cap_approved(self):
        v = _bare_validator()
        v.add_policy(GovernancePolicy(
            id="cap", name="Severity Cap", max_severity=RuleSeverity.WARNING,
        ))
        assert len(v.validate([_result(["send_email"], RuleSeverity.WARNING)], context={})) == 1


# ============================================
# Audit trail & bookkeeping
# ============================================

class TestAuditAndStats:

    def test_disabled_policy_ignored(self):
        v = _bare_validator()
        v.add_policy(GovernancePolicy(
            id="off", name="Disabled", enabled=False, blocked_actions=["send_email"],
        ))
        assert len(v.validate([_result(["send_email"])], context={})) == 1

    def test_untriggered_result_passes_through(self):
        v = GovernanceValidator()
        untriggered = RuleResult(
            rule_id="r", rule_name="R", triggered=False,
            severity=RuleSeverity.INFO, actions=[],
        )
        assert len(v.validate([untriggered], context={})) == 1

    def test_audit_log_records_verdicts(self):
        v = GovernanceValidator()
        v.validate(
            [_result(["face_recognition"])],
            context={"zone": "bathroom", "user_consent": True, "max_confidence": 0.9},
        )
        log = v.get_audit_log()
        assert log and log[-1].verdict == GovernanceVerdict.BLOCKED
        assert log[-1].policy_id == "privacy_zones"

    def test_stats_counts_outcomes(self):
        v = GovernanceValidator()
        ctx = {"zone": "lobby", "user_consent": True, "max_confidence": 0.9}
        v.validate([_result(["send_email"])], context=ctx)
        v.validate(
            [_result(["face_recognition"])],
            context={**ctx, "zone": "bathroom"},
        )

        stats = v.get_stats()
        assert stats["total_approved"] >= 1
        assert stats["total_blocked"] >= 1
        assert 0 <= stats["block_rate"] <= 100

    def test_empty_input_returns_empty(self):
        assert GovernanceValidator().validate([], context={}) == []
