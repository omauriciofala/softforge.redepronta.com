# Vertical Slice: Billing & Subscriptions (Mercado Pago)

> **Hybrid Subscription Engine, Transparent Pix, Invoices, Plan Management, and Quota Enforcement for SaaS.**

---

## 1. Slice Architecture Overview

The `billing` slice (`apps/api/src/slices/billing/`) manages the full subscription and payment lifecycle:

- **Hybrid Tenancy Model:** Native support for both organization-level subscriptions by **Workspace** (standard B2B SaaS) and personal subscriptions by **User** (B2C).
- **Mercado Pago Integration:** Full support for Brazilian payment methods: **Transparent Pix (QR Code and Copy-Paste)**, Boletos, and Credit Cards.
- **Offline Mock Provider:** A deterministic mock gateway that enables 100% offline integration tests without requiring live API credentials.
- **Declarative Quota Guards:** Reusable FastAPI dependencies (`check_quota("projects")`, `check_quota("members")`) that guard resource creation against plan thresholds.
- **Webhook Reconciliation:** Secure callback endpoints that process payment events and automatically extend subscription periods.

---

## 2. Official Plan Tiers

| Tier | Monthly Price | Project Quota | Member Quota | Features |
| :--- | :--- | :--- | :--- | :--- |
| **Starter (Free)** | Free ($0 / R$ 0) | 3 projects | 2 members | JWT Auth, basic CRUD, SQLite in-memory |
| **Professional (Pro)** | R$ 49.00 / mo | 25 projects | 10 members | OpenAPI export, Webhooks, priority support |
| **Enterprise** | R$ 199.00 / mo | Unlimited (`-1`) | Unlimited (`-1`) | Multiple admins, audit logging, 99.9% SLA |

---

## 3. How to Guard Resources with Quota Dependencies

Attach the `check_quota` dependency directly to any endpoint to enforce subscription limits:

```python
from fastapi import APIRouter, Depends
from src.slices.billing.dependencies import check_quota

router = APIRouter(prefix="/workspaces/{workspace_id}/projects")

@router.post(
    "",
    dependencies=[Depends(check_quota("projects"))],
)
async def create_project(...):
    # Only executes if project count < max_projects of active plan!
    ...
```

When quota limits are reached, SoftForge returns `HTTP 403 Forbidden`:
```json
{
  "error": "FORBIDDEN",
  "message": "Limite de projetos atingido (3/3). Faça upgrade para o Plano Pro em /billing para criar mais projetos.",
  "details": null,
  "request_id": "..."
}
```
