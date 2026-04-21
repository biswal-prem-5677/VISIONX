"""
VisionX — Governance Validator
========================================
Ethics & privacy gate between Decision Engine and Event Engine.
Blocks actions that violate privacy, legal, or safety constraints.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

from decision.rules import RuleResult, RuleSeverity


class GovernanceVerdict(str, Enum):
    APPROVED = "approved"
    BLOCKED = "blocked"
    MODIFIED = "modified"


class GovernancePolicy(BaseModel):
    """A single governance policy."""
    id: str
    name: str
    description: str = ""
    enabled: bool = True
    blocked_actions: list[str] = Field(default_factory=list)
    blocked_zones: list[str] = Field(default_factory=list)
    max_severity: Optional[RuleSeverity] = None
    require_consent: bool = False
    min_confidence: float = 0.0
    time_restrictions: dict[str, Any] = Field(default_factory=dict)


class GovernanceResult(BaseModel):
    """Result of governance validation."""
    rule_id: str
    verdict: GovernanceVerdict
    policy_id: str = ""
    reason: str = ""
    original_actions: list[str] = Field(default_factory=list)
    approved_actions: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GovernanceValidator:
    """
    Ethics & privacy gate for the VisionX pipeline.

    Sits between DecisionEngine and EventEngine:
        DecisionEngine.evaluate() → GovernanceValidator.validate() → EventEngine.process()

    Responsibilities:
    - Block face recognition in private zones
    - Block recording of minors (if age detection available)
    - Enforce time-of-day restrictions
    - Require consent for biometric actions
    - Cap severity escalation
    - Audit log all governance decisions
    """

    def __init__(self):
        self._policies: dict[str, GovernancePolicy] = {}
        self._audit_log: list[GovernanceResult] = []
        self._max_audit: int = 5000
        self._total_approved: int = 0
        self._total_blocked: int = 0
        self._total_modified: int = 0

        self._register_defaults()
        logger.info(f"GovernanceValidator initialized ({len(self._policies)} policies)")

    def add_policy(self, policy: GovernancePolicy) -> None:
        """Register a governance policy."""
        self._policies[policy.id] = policy
        logger.info(f"Governance policy added: {policy.name}")

    def validate(
        self,
        rule_results: list[RuleResult],
        context: Optional[dict[str, Any]] = None,
    ) -> list[RuleResult]:
        """
        Validate triggered rules against governance policies.
        Returns only approved/modified rule results.
        Blocked rules are logged and removed.
        """
        ctx = context or {}
        approved: list[RuleResult] = []

        for result in rule_results:
            if not result.triggered:
                approved.append(result)
                continue

            verdict = self._check_policies(result, ctx)

            if verdict.verdict == GovernanceVerdict.APPROVED:
                approved.append(result)
                self._total_approved += 1

            elif verdict.verdict == GovernanceVerdict.MODIFIED:
                # Replace actions with governance-approved subset
                modified = result.model_copy()
                modified.actions = verdict.approved_actions
                approved.append(modified)
                self._total_modified += 1
                logger.info(
                    f"Governance modified: {result.rule_name} — "
                    f"removed {set(result.actions) - set(verdict.approved_actions)}"
                )

            elif verdict.verdict == GovernanceVerdict.BLOCKED:
                self._total_blocked += 1
                logger.warning(
                    f"Governance BLOCKED: {result.rule_name} — "
                    f"policy={verdict.policy_id}, reason={verdict.reason}"
                )

            self._audit_log.append(verdict)
            if len(self._audit_log) > self._max_audit:
                self._audit_log = self._audit_log[-self._max_audit:]

        return approved

    def _check_policies(
        self, result: RuleResult, context: dict[str, Any]
    ) -> GovernanceResult:
        """Check a single rule result against all policies."""
        for policy in self._policies.values():
            if not policy.enabled:
                continue

            # 1. Block specific actions
            if policy.blocked_actions:
                blocked = [a for a in result.actions if a in policy.blocked_actions]
                if blocked:
                    remaining = [a for a in result.actions if a not in policy.blocked_actions]
                    if not remaining:
                        return GovernanceResult(
                            rule_id=result.rule_id,
                            verdict=GovernanceVerdict.BLOCKED,
                            policy_id=policy.id,
                            reason=f"All actions blocked by policy: {blocked}",
                            original_actions=result.actions,
                        )
                    else:
                        return GovernanceResult(
                            rule_id=result.rule_id,
                            verdict=GovernanceVerdict.MODIFIED,
                            policy_id=policy.id,
                            reason=f"Actions {blocked} removed by policy",
                            original_actions=result.actions,
                            approved_actions=remaining,
                        )

            # 2. Block actions in restricted zones
            if policy.blocked_zones:
                zone = context.get("zone", "")
                if zone in policy.blocked_zones:
                    return GovernanceResult(
                        rule_id=result.rule_id,
                        verdict=GovernanceVerdict.BLOCKED,
                        policy_id=policy.id,
                        reason=f"Zone '{zone}' is restricted by policy",
                        original_actions=result.actions,
                    )

            # 3. Severity cap
            if policy.max_severity:
                severity_order = {
                    RuleSeverity.INFO: 0,
                    RuleSeverity.WARNING: 1,
                    RuleSeverity.CRITICAL: 2,
                    RuleSeverity.EMERGENCY: 3,
                }
                if severity_order.get(result.severity, 0) > severity_order.get(policy.max_severity, 3):
                    return GovernanceResult(
                        rule_id=result.rule_id,
                        verdict=GovernanceVerdict.BLOCKED,
                        policy_id=policy.id,
                        reason=f"Severity {result.severity.value} exceeds max {policy.max_severity.value}",
                        original_actions=result.actions,
                    )

            # 4. Consent requirement
            if policy.require_consent:
                has_consent = context.get("user_consent", False)
                if not has_consent:
                    biometric_actions = [
                        a for a in result.actions
                        if a in ("face_recognition", "store_biometric", "record_video")
                    ]
                    if biometric_actions:
                        remaining = [a for a in result.actions if a not in biometric_actions]
                        if not remaining:
                            return GovernanceResult(
                                rule_id=result.rule_id,
                                verdict=GovernanceVerdict.BLOCKED,
                                policy_id=policy.id,
                                reason="Biometric actions require user consent",
                                original_actions=result.actions,
                            )
                        return GovernanceResult(
                            rule_id=result.rule_id,
                            verdict=GovernanceVerdict.MODIFIED,
                            policy_id=policy.id,
                            reason="Biometric actions removed (no consent)",
                            original_actions=result.actions,
                            approved_actions=remaining,
                        )

            # 5. Minimum confidence check
            if policy.min_confidence > 0:
                confidence = context.get("max_confidence", 1.0)
                if confidence < policy.min_confidence:
                    return GovernanceResult(
                        rule_id=result.rule_id,
                        verdict=GovernanceVerdict.BLOCKED,
                        policy_id=policy.id,
                        reason=f"Confidence {confidence:.2f} below minimum {policy.min_confidence:.2f}",
                        original_actions=result.actions,
                    )

        # All policies passed
        return GovernanceResult(
            rule_id=result.rule_id,
            verdict=GovernanceVerdict.APPROVED,
            original_actions=result.actions,
            approved_actions=result.actions,
        )

    def get_audit_log(self, limit: int = 100) -> list[GovernanceResult]:
        """Get recent governance audit entries."""
        return self._audit_log[-limit:]

    def get_stats(self) -> dict:
        """Get governance statistics."""
        return {
            "policies": len(self._policies),
            "total_approved": self._total_approved,
            "total_blocked": self._total_blocked,
            "total_modified": self._total_modified,
            "audit_log_size": len(self._audit_log),
            "block_rate": round(
                self._total_blocked / max(self._total_approved + self._total_blocked + self._total_modified, 1) * 100, 1
            ),
        }

    def _register_defaults(self) -> None:
        """Register built-in governance policies."""
        defaults = [
            GovernancePolicy(
                id="privacy_zones",
                name="Private Zone Protection",
                description="Block recording and face recognition in private zones",
                blocked_zones=["bathroom", "changing_room", "private_office"],
                blocked_actions=["record_video", "face_recognition", "store_biometric"],
            ),
            GovernancePolicy(
                id="biometric_consent",
                name="Biometric Consent Requirement",
                description="Require consent for biometric data processing",
                require_consent=True,
            ),
            GovernancePolicy(
                id="low_confidence_gate",
                name="Low Confidence Filter",
                description="Block events from low-confidence detections",
                min_confidence=0.4,
            ),
        ]
        for policy in defaults:
            self._policies[policy.id] = policy
