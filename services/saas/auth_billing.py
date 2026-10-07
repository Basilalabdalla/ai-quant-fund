from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

# --- إعدادات السجلات ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("SaaSGateway")


# --- النماذج والثوابت ---
class SubscriptionTier:
    BASIC = "BASIC"  # Max $10k portfolio cap
    PRO = "PRO"  # Max $100k portfolio cap
    ENTERPRISE = "ENTERPRISE"  # Unlimited portfolio cap


CAPITAL_CAPS = {
    SubscriptionTier.BASIC: 10_000.0,
    SubscriptionTier.PRO: 100_000.0,
    SubscriptionTier.ENTERPRISE: 1_000_000.0,
}


class TenantProfile(BaseModel):
    tenant_id: str
    owner_email: str
    tier: str = SubscriptionTier.BASIC
    max_capital_cap: float = 10_000.0
    exchange_api_keys: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = True
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class RegisterTenantRequest(BaseModel):
    tenant_id: str
    email: str
    tier: str = SubscriptionTier.BASIC


class ValidateOrderRequest(BaseModel):
    tenant_id: str
    proposed_trade_amount: float


class StripeWebhookPayload(BaseModel):
    event_type: str
    payload: Dict[str, Any]


# --- مدير المستأجرين (SaaS Manager) ---
class SaaSMultiTenantManager:

    def __init__(self):
        self._tenants_db: Dict[str, TenantProfile] = {}

    def register_tenant(
        self, tenant_id: str, email: str, tier: str = SubscriptionTier.BASIC
    ) -> TenantProfile:
        profile = TenantProfile(
            tenant_id=tenant_id,
            owner_email=email,
            tier=tier,
            max_capital_cap=CAPITAL_CAPS.get(tier, 10_000.0),
        )
        self._tenants_db[tenant_id] = profile
        logger.info(
            f"👤 [Tenant Registered] ID: {tenant_id} | Email: {email} | Tier: {tier} | Capital Cap: ${profile.max_capital_cap:,.2f}"
        )
        return profile

    def handle_stripe_webhook_event(
        self, event_type: str, payload: Dict[str, Any]
    ):
        logger.info(f"💳 [Stripe Webhook Event Received] Type: {event_type}")

        if event_type == "customer.subscription.updated":
            tenant_id = payload.get("client_reference_id")
            new_tier = payload.get("new_tier")

            if tenant_id in self._tenants_db:
                tenant = self._tenants_db[tenant_id]
                tenant.tier = new_tier
                tenant.max_capital_cap = CAPITAL_CAPS.get(new_tier, 10_000.0)
                logger.info(
                    f"🚀 [Tier Updated] Tenant '{tenant_id}' set to '{new_tier}'. New Cap: ${tenant.max_capital_cap:,.2f}"
                )

    def validate_tenant_order_allowance(
        self, tenant_id: str, proposed_trade_amount: float
    ) -> Tuple[bool, str]:
        tenant = self._tenants_db.get(tenant_id)
        if not tenant:
            return False, "Tenant not found or unauthorized."

        if not tenant.is_active:
            return False, "Tenant subscription is inactive."

        if proposed_trade_amount > tenant.max_capital_cap:
            return (
                False,
                f"Trade amount (${proposed_trade_amount:,.2f}) exceeds subscription cap (${tenant.max_capital_cap:,.2f}). Upgrade to PRO or ENTERPRISE.",
            )

        return True, "Order allowed under current SaaS subscription."


# --- إنشاء تطبيق FastAPI والربط ---
app = FastAPI(title="SaaS Multi-Tenant Gateway & Billing", version="1.0")
saas_manager = SaaSMultiTenantManager()


@app.get("/")
def read_root():
    return {"status": "online", "service": "SaaS Multi-Tenant Gateway"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/tenants/register", response_model=TenantProfile)
def register_tenant(req: RegisterTenantRequest):
    return saas_manager.register_tenant(req.tenant_id, req.email, req.tier)


@app.post("/tenants/validate-order")
def validate_order(req: ValidateOrderRequest):
    allowed, message = saas_manager.validate_tenant_order_allowance(
        req.tenant_id, req.proposed_trade_amount
    )
    return {"allowed": allowed, "message": message}


@app.post("/webhooks/stripe")
def stripe_webhook(data: StripeWebhookPayload):
    saas_manager.handle_stripe_webhook_event(data.event_type, data.payload)
    return {"status": "success"}


# --- نقطة التشغيل الرئيسية ---
if __name__ == "__main__":
    logger.info("🚀 Starting SaaS Gateway HTTP Server on port 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)