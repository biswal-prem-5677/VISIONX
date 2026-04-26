"""
VisionX — Billing Plans
========================================
Subscription plan definitions: Free, Pro, Enterprise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class PlanLimits:
    """Rate & resource limits per plan tier."""
    max_cameras: int = 2
    max_events_per_hour: int = 100
    max_api_requests_per_min: int = 100
    max_websocket_connections: int = 2
    max_users: int = 1
    max_storage_gb: int = 1
    max_retention_days: int = 7
    video_export: bool = False
    custom_rules: bool = False
    priority_support: bool = False
    webhook_deliveries_per_hour: int = 100
    model_uploads_per_day: int = 1


@dataclass
class Plan:
    """Subscription plan definition."""
    tier: PlanTier
    name: str
    price_monthly_usd: float
    price_yearly_usd: float
    stripe_price_id_monthly: str = ""
    stripe_price_id_yearly: str = ""
    limits: PlanLimits = field(default_factory=PlanLimits)
    features: list[str] = field(default_factory=list)


# ─── Plan Definitions ────────────────────────────────────────────────────────

FREE_PLAN = Plan(
    tier=PlanTier.FREE,
    name="Free",
    price_monthly_usd=0,
    price_yearly_usd=0,
    limits=PlanLimits(
        max_cameras=2,
        max_events_per_hour=100,
        max_api_requests_per_min=100,
        max_websocket_connections=2,
        max_users=1,
        max_storage_gb=1,
        max_retention_days=7,
        video_export=False,
        custom_rules=False,
        priority_support=False,
        webhook_deliveries_per_hour=100,
        model_uploads_per_day=1,
    ),
    features=[
        "2 Cameras",
        "Basic Detection",
        "7-day retention",
        "Community support",
    ],
)

PRO_PLAN = Plan(
    tier=PlanTier.PRO,
    name="Pro",
    price_monthly_usd=29.99,
    price_yearly_usd=299.99,
    limits=PlanLimits(
        max_cameras=20,
        max_events_per_hour=5000,
        max_api_requests_per_min=5000,
        max_websocket_connections=20,
        max_users=10,
        max_storage_gb=50,
        max_retention_days=30,
        video_export=True,
        custom_rules=True,
        priority_support=False,
        webhook_deliveries_per_hour=5000,
        model_uploads_per_day=10,
    ),
    features=[
        "20 Cameras",
        "All AI Modules",
        "30-day retention",
        "Custom rules & automation",
        "Video export",
        "Email support",
    ],
)

ENTERPRISE_PLAN = Plan(
    tier=PlanTier.ENTERPRISE,
    name="Enterprise",
    price_monthly_usd=199.99,
    price_yearly_usd=1999.99,
    limits=PlanLimits(
        max_cameras=1000,
        max_events_per_hour=50000,
        max_api_requests_per_min=50000,
        max_websocket_connections=200,
        max_users=10000,
        max_storage_gb=1000,
        max_retention_days=365,
        video_export=True,
        custom_rules=True,
        priority_support=True,
        webhook_deliveries_per_hour=50000,
        model_uploads_per_day=999,
    ),
    features=[
        "Unlimited Cameras",
        "All AI + Governance",
        "365-day retention",
        "Custom models",
        "Priority support",
        "SLA guarantee",
        "SSO / SAML",
    ],
)

ALL_PLANS = {
    PlanTier.FREE: FREE_PLAN,
    PlanTier.PRO: PRO_PLAN,
    PlanTier.ENTERPRISE: ENTERPRISE_PLAN,
}


def get_plan(tier: PlanTier) -> Plan:
    """Get plan by tier."""
    return ALL_PLANS[tier]


def get_plan_limits(tier: PlanTier) -> PlanLimits:
    """Get limits for a plan tier."""
    return ALL_PLANS[tier].limits
