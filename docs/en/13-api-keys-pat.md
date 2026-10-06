# Vertical Slice: API Keys & PAT (Machine-to-Machine)

> **Machine-to-Machine (M2M) Authentication for Autonomous AI Agents, CLI tools, and CI/CD pipelines with SHA-256 hashing and multi-tenant isolation.**

---

## 1. Slice Overview

The `apikeys` slice (`apps/api/src/slices/apikeys/`) provides SoftForge's official channel for programmatic and autonomous agent authentication:

- **First-Class M2M Authentication:** Empowers external AI agents (e.g., Cursor, Claude Dev, AutoPR, GitHub Actions, Python/Go scripts) to perform operations on the API without relying on web browser sessions or short-lived JWT tokens.
- **SHA-256 Cryptographic Hashing:** The plaintext secret (`sf_live_...`) is generated with high cryptographic entropy (`secrets.token_urlsafe(32)`) and revealed **only once** upon creation. The database exclusively persists the SHA-256 hexadecimal digest (`hashed_key`).
- **Visual Key Identification via Masked Prefix:** Listing endpoints return a masked prefix (`key_prefix`, e.g., `sf_live_a1b2...9xyz`), allowing administrators to identify keys without exposing credentials.
- **Configurable Expiration:** Keys can be configured with an optional lifetime in days (`expires_in_days`) or set to never expire. Expired keys are rejected with HTTP 401 Unauthorized.
- **Instant Revocation:** Workspace administrators can immediately revoke compromised or obsolete keys, terminating API access instantly.
- **Strict Multi-Tenant Isolation:** Each API key belongs strictly to its originating workspace. Any attempt to access resources in another workspace is rejected with HTTP 403 Forbidden.
- **Integrated Audit Trail & Outbound Webhooks:** Key creation (`api_key.created`) and revocation (`api_key.revoked`) events automatically trigger immutable audit logs and outbound webhooks.

---

## 2. M2M Authentication Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Agent as Autonomous AI Agent / CI Script
    participant API as SoftForge API (FastAPI)
    participant Auth as Auth Dependency (get_current_user)
    participant Service as ApiKey Service
    participant DB as PostgreSQL Database (api_keys)
    participant Resource as Endpoint (/projects)

    Agent->>API: GET /api/v1/workspaces/{id}/projects
    Note over Agent,API: Header "X-API-Key: sf_live_..." or "Authorization: Bearer sf_live_..."
    API->>Auth: Inject get_current_user dependency
    Auth->>Service: authenticate_api_key(session, raw_key)
    Service->>Service: Calculate SHA-256 hash of incoming key
    Service->>DB: Query active key where hashed_key = digest
    DB-->>Service: Return ApiKey + Creator User
    Service->>Service: Verify is_revoked=False and expires_at > now()
    Service->>DB: Update last_used_at = now()
    Service-->>Auth: Return creator User
    Auth->>Resource: Proceed with authenticated user and workspace security check
    Resource-->>Agent: HTTP 200 OK (Projects data)
```

---

## 3. How to Use API Keys

SoftForge supports two standard HTTP request headers:

### Option A: `X-API-Key` Header (Recommended for Scripts and AI Agents)

```bash
curl -X GET "https://api.softforge.redepronta.com/api/v1/workspaces/{workspace_id}/projects" \
  -H "X-API-Key: sf_live_YOUR_SECRET_KEY_HERE"
```

### Option B: `Authorization: Bearer` Header (RFC 6750 Standard)

```bash
curl -X GET "https://api.softforge.redepronta.com/api/v1/auth/me" \
  -H "Authorization: Bearer sf_live_YOUR_SECRET_KEY_HERE"
```

---

## 4. Slice Endpoints

| Method | Route | Description | Minimum Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/workspaces/{workspace_id}/api-keys` | Generates a new API key and returns the raw secret | `Admin` |
| `GET` | `/api/v1/workspaces/{workspace_id}/api-keys` | Lists registered API keys with masked prefixes | `Admin` |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/api-keys/{key_id}` | Immediately revokes an API key | `Admin` |

---

## 5. Automated Verification & Testing

The slice is covered with 100% deterministic Pytest test cases (`test_apikeys_slice.py`):
1. **Generation and Hashing:** Validates key structure, prefix formatting, and SHA-256 consistency.
2. **CRUD Lifecycle:** Creation, masked listing, and revocation.
3. **Real-world Authentication & Tenant Isolation:** Verifies requests authenticated via `X-API-Key` and `Authorization: Bearer`, ensuring cross-workspace access attempts receive HTTP 403 Forbidden.
4. **Invalid Key Protection:** Returns HTTP 401 Unauthorized for forged, revoked, or expired keys.
