# SoftForge Framework Manual

> **Architecture, Design Patterns, and Internal Conventions**  
> *Complete technical guide to the SoftForge ecosystem.*

---

## 1. Philosophy: Why Vertical Slice Architecture?

In traditional layered architecture (Controllers, Services, Repositories), features are scattered across distinct horizontal folders. When an AI agent attempts to create or edit a feature, it must juggle dozens of disparate files inside its context window, drastically increasing the chance of hallucination and unintended regressions.

In **SoftForge**, each business feature is completely self-contained in a vertical slice:
```text
apps/api/src/slices/<feature>/
├── schemas.py       # OpenAPI contracts & DTOs (Pydantic v2)
├── models.py        # ORM entities (SQLAlchemy 2.0 Async)
├── service.py       # Pure business logic
├── router.py        # HTTP routes & dependencies
└── tests/           # Isolated integration tests
```

---

## 2. Anatomy of a Vertical Slice

### 2.1 `schemas.py` (Data Contracts)
Defines strict inputs and outputs:
- `CreateRequest` and `UpdateRequest` using Pydantic `Field(...)` validations.
- `Response` with `model_config = ConfigDict(from_attributes=True)` for direct ORM serialization.

### 2.2 `models.py` (Database Entities)
Inherits from `src.core.database.Base`:
- Automatically inherits `id` (cross-database UUID), `created_at`, and `updated_at`.
- Strictly typed using `Mapped[...]` and `mapped_column(...)`.

### 2.3 `service.py` (Business Logic)
Pure async functions taking `session: AsyncSession`:
- Completely decoupled from HTTP concerns (no `Request` or `Response`).
- Raises standardized exceptions (`NotFoundException`, `ForbiddenException`, `AppException`).

### 2.4 `router.py` (HTTP Layer)
Bridges logic to FastAPI:
- Applies security and RBAC guards (`require_workspace_role`).
- Documents `response_model`, status codes, and Swagger tags.

---

## 3. Multi-Tenancy and Role-Based Access Control (RBAC)

SoftForge is built for B2B SaaS products with multi-workspace support:
- **Role Hierarchy:**
  1. `Owner` (Level 4) — Full control over organization and billing.
  2. `Admin` (Level 3) — Manages members and project configurations.
  3. `Member` (Level 2) — Creates and edits projects and tasks.
  4. `Viewer` (Level 1) — Read-only access to resources.

---

## 4. Observability & Structured Logging

Powered by **Loguru** with automatic **Correlation ID (`X-Request-ID`)** propagation:
- **Development:** Color-coded, highly readable logs showing file, function, and line.
- **Production:** Structured JSON logs ready for Datadog, Loki, or CloudWatch ingestion.
- Every HTTP response includes `X-Request-ID` and `X-Process-Time`.
