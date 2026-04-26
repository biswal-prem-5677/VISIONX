"""
VisionX — Stripe Billing Service
====================================
Stripe integration for subscriptions and payments.
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field


class SubscriptionPlan(BaseModel):
    """A subscription plan definition."""
    id: str
    name: str
    price_monthly: float
    price_yearly: float
    features: list[str] = Field(default_factory=list)
    max_devices: int = 1
    max_rules: int = 5
    cloud_modules: bool = False
    api_access: bool = False
    priority_support: bool = False


# Plan definitions
PLANS: dict[str, SubscriptionPlan] = {
    "free": SubscriptionPlan(
        id="free",
        name="Free",
        price_monthly=0,
        price_yearly=0,
        features=["1 camera", "Basic detection", "5 rules"],
        max_devices=1,
        max_rules=5,
    ),
    "pro": SubscriptionPlan(
        id="pro",
        name="Pro",
        price_monthly=29.99,
        price_yearly=299.99,
        features=[
            "5 cameras", "All edge modules", "50 rules",
            "Cloud OCR", "Email alerts", "Analytics",
        ],
        max_devices=5,
        max_rules=50,
        cloud_modules=True,
        api_access=True,
    ),
    "enterprise": SubscriptionPlan(
        id="enterprise",
        name="Enterprise",
        price_monthly=99.99,
        price_yearly=999.99,
        features=[
            "Unlimited cameras", "All modules", "Unlimited rules",
            "Priority support", "Custom integrations", "SLA",
        ],
        max_devices=999,
        max_rules=999,
        cloud_modules=True,
        api_access=True,
        priority_support=True,
    ),
}


class StripeService:
    """
    Stripe billing integration.

    Manages subscriptions, checkout sessions, and webhooks.
    """

    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.getenv("STRIPE_SECRET_KEY", "")
        self._webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        self._stripe = None

        if self._api_key:
            try:
                import stripe
                stripe.api_key = self._api_key
                self._stripe = stripe
                logger.info("Stripe service initialized")
            except ImportError:
                logger.warning("stripe not installed. Install with: pip install stripe")
        else:
            logger.info("Stripe service initialized (no API key — test mode)")

    def get_plans(self) -> list[SubscriptionPlan]:
        """Get all available plans."""
        return list(PLANS.values())

    def get_plan(self, plan_id: str) -> Optional[SubscriptionPlan]:
        """Get a specific plan."""
        return PLANS.get(plan_id)

    async def create_checkout_session(
        self,
        plan_id: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
    ) -> Optional[str]:
        """Create a Stripe checkout session."""
        if not self._stripe:
            logger.warning("Stripe not configured")
            return None

        plan = PLANS.get(plan_id)
        if not plan or plan.price_monthly == 0:
            return None

        try:
            session = self._stripe.checkout.Session.create(
                payment_method_types=["card"],
                customer_email=user_email,
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"VisionX {plan.name}"},
                        "unit_amount": int(plan.price_monthly * 100),
                        "recurring": {"interval": "month"},
                    },
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"plan_id": plan_id},
            )

            return session.url

        except Exception as e:
            logger.error(f"Stripe checkout error: {e}")
            return None

    def verify_webhook(self, payload: bytes, signature: str) -> Optional[dict]:
        """Verify and parse a Stripe webhook event."""
        if not self._stripe or not self._webhook_secret:
            return None

        try:
            event = self._stripe.Webhook.construct_event(
                payload, signature, self._webhook_secret
            )
            return event
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {e}")
            return None
