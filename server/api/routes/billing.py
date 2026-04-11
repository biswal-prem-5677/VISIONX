"""
VisionX — Billing API Routes
================================
Stripe subscription, plan management, and invoice endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/billing", tags=["billing"])


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
    """List available subscription plans."""
    return PLANS


@router.get("/subscription", response_model=SubscriptionStatus)
async def get_subscription():
    """Get current user's subscription status."""
    return SubscriptionStatus(
        plan="pro",
        status="active",
        current_period_end="2026-05-11T00:00:00Z",
        camera_limit=5,
    )


@router.post("/checkout")
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


@router.post("/webhook")
async def stripe_webhook():
    """Handle Stripe webhook events."""
    # In production: verify signature and process events
    return {"status": "received"}


@router.get("/invoices")
async def list_invoices():
    """List billing invoices."""
    return [
        {"id": "inv_001", "amount": 29.99, "status": "paid", "date": "2026-04-01"},
        {"id": "inv_002", "amount": 29.99, "status": "paid", "date": "2026-03-01"},
    ]
