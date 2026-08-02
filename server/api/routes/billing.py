"""
VisionX — Billing API Routes
================================
Stripe subscription, plan management, and invoice endpoints.

Authorization
-------------
``GET /plans`` is **deliberately public** — a pricing page must render before
signup. Everything else requires ``Permission.MANAGE_BILLING``.

``POST /webhook`` cannot use bearer auth (Stripe calls it), so it authenticates
by HMAC signature instead. It previously accepted any unsigned request and
returned 200, which is an unauthenticated write path into billing state the
moment this stub is implemented. It now **fails closed**: no configured secret,
no missing/!invalid signature, no processing.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from loguru import logger
from pydantic import BaseModel

from server.api.dependencies import require_permission
from server.auth.rbac import Permission

router = APIRouter(prefix="/billing", tags=["billing"])

_manage_billing = require_permission(Permission.MANAGE_BILLING)

#: Stripe rejects signatures older than this by default; mirroring it here
#: prevents captured webhook payloads from being replayed indefinitely.
_WEBHOOK_TOLERANCE_SECONDS = 300


class PlanInfo(BaseModel):
    """Subscription plan details."""
    id: str
    name: str
    price: float
    camera_limit: int
    features: list[str]


class SubscriptionStatus(BaseModel):
    """Current subscription status."""
    plan: str
    status: str  # active, canceled, past_due
    current_period_end: str
    camera_limit: int


PLANS = [
    PlanInfo(
        id="free", name="Free", price=0, camera_limit=1,
        features=["1 Camera", "Basic Detection", "Email Alerts"],
    ),
    PlanInfo(
        id="pro", name="Pro", price=29.99, camera_limit=5,
        features=["5 Cameras", "All AI Modules", "Priority Support", "Analytics"],
    ),
    PlanInfo(
        id="enterprise", name="Enterprise", price=99.99, camera_limit=999,
        features=["Unlimited Cameras", "Custom Models", "Dedicated Support", "SLA"],
    ),
]


@router.get("/plans", response_model=list[PlanInfo])
async def list_plans():
    """List available subscription plans. Public — this is the pricing page."""
    return PLANS


@router.get(
    "/subscription",
    response_model=SubscriptionStatus,
    dependencies=[Depends(_manage_billing)],
)
async def get_subscription():
    """Get current user's subscription status."""
    return SubscriptionStatus(
        plan="pro",
        status="active",
        current_period_end="2026-05-11T00:00:00Z",
        camera_limit=5,
    )


@router.post("/checkout", dependencies=[Depends(_manage_billing)])
async def create_checkout(plan_id: str):
    """Create Stripe checkout session for plan upgrade."""
    plan = next((p for p in PLANS if p.id == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # In production: create Stripe checkout session
    return {
        "checkout_url": f"https://checkout.stripe.com/mock/{plan_id}",
        "plan": plan.name,
    }


def _verify_stripe_signature(secret: str, payload: bytes, header: str) -> bool:
    """
    Verify a ``Stripe-Signature`` header (scheme ``t=<ts>,v1=<hex>``).

    Returns False on any malformed input rather than raising, so a hostile
    header shape cannot turn into a 500.
    """
    try:
        parts = dict(
            item.split("=", 1) for item in header.split(",") if "=" in item
        )
        timestamp = parts["t"]
        provided = parts["v1"]
    except (ValueError, KeyError):
        return False

    try:
        age = abs(time.time() - int(timestamp))
    except ValueError:
        return False
    if age > _WEBHOOK_TOLERANCE_SECONDS:
        logger.warning("Stripe webhook rejected: signature timestamp outside tolerance")
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        f"{timestamp}.".encode("utf-8") + payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, provided)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header("", alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.

    Authenticated by HMAC signature, not by bearer token — Stripe cannot present
    one. Fails closed when ``STRIPE_WEBHOOK_SECRET`` is not configured.
    """
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        logger.error("Stripe webhook received but STRIPE_WEBHOOK_SECRET is not set")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing webhooks are not configured",
        )

    body = await request.body()
    if not stripe_signature or not _verify_stripe_signature(
        secret, body, stripe_signature
    ):
        logger.warning("Stripe webhook rejected: invalid signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # In production: parse the event and update subscription state.
    return {"status": "received"}


@router.get("/invoices", dependencies=[Depends(_manage_billing)])
async def list_invoices():
    """List billing invoices."""
    return [
        {"id": "inv_001", "amount": 29.99, "status": "paid", "date": "2026-04-01"},
        {"id": "inv_002", "amount": 29.99, "status": "paid", "date": "2026-03-01"},
    ]
