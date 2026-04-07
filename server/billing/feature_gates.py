"""
VisionX — Feature Gates
===========================
Controls feature access based on subscription plan.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from server.billing.stripe_service import PLANS, SubscriptionPlan


class FeatureGate:
    """
    Feature gating based on subscription plan.

    Controls which features are available to users
    based on their subscription tier.
    """

    def __init__(self):
        self._user_plans: dict[str, str] = {}  # user_id -> plan_id

        logger.info("Feature Gate initialized")

    def set_user_plan(self, user_id: str, plan_id: str) -> None:
        """Set a user's subscription plan."""
        self._user_plans[user_id] = plan_id

    def get_user_plan(self, user_id: str) -> SubscriptionPlan:
        """Get a user's plan (defaults to free)."""
        plan_id = self._user_plans.get(user_id, "free")
        return PLANS.get(plan_id, PLANS["free"])

    def check_device_limit(self, user_id: str, current_count: int) -> bool:
        """Check if user can add more devices."""
        plan = self.get_user_plan(user_id)
        return current_count < plan.max_devices

    def check_rule_limit(self, user_id: str, current_count: int) -> bool:
        """Check if user can add more rules."""
        plan = self.get_user_plan(user_id)
        return current_count < plan.max_rules

    def has_cloud_modules(self, user_id: str) -> bool:
        """Check if user has access to cloud AI modules."""
        return self.get_user_plan(user_id).cloud_modules

    def has_api_access(self, user_id: str) -> bool:
        """Check if user has API access."""
        return self.get_user_plan(user_id).api_access

    def has_priority_support(self, user_id: str) -> bool:
        """Check if user has priority support."""
        return self.get_user_plan(user_id).priority_support

    def require_feature(self, user_id: str, feature: str) -> None:
        """Raise error if user doesn't have access to feature."""
        plan = self.get_user_plan(user_id)
        checks = {
            "cloud_modules": plan.cloud_modules,
            "api_access": plan.api_access,
            "priority_support": plan.priority_support,
        }

        if feature in checks and not checks[feature]:
            raise PermissionError(
                f"Feature '{feature}' requires plan upgrade. "
                f"Current plan: {plan.name}"
            )
