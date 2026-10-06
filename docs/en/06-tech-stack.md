# SoftForge Official Tech Stack

> **The modern, contract-driven foundation engineered for AI Agents and human developers.**

---

## 1. Stack Architecture Overview

SoftForge was built on a single architectural principle: **every technology must be strictly typed, deterministic, and maintain an optimal context window footprint for autonomous AI Agents (LLMs).**

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (apps/web)                             │
│      React + TypeScript + Vite + Tailwind CSS + shadcn/ui             │
│      TanStack Query (React Query v5) + Lucide Icons                    │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │
                       OpenAPI 3.1 Contract & DTOs
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                         BACKEND (apps/api)                             │
│     Python 3.12+ + FastAPI + Pydantic v2 + SQLAlchemy 2.0 Async        │
│     Loguru (Structured Logs) + JWT/HttpOnly Cookies + Ruff Linter      │
└───────────────────▲────────────────────────────────▲───────────────────┘
                    │                                │
      (Test Environment / CI)              (Production / Docker)
                    │                                │
┌───────────────────▼──────────────┐ ┌───────────────▼───────────────────┐
│     SQLite In-Memory             │ │      PostgreSQL 16+               │
│     (Executes in ~2 seconds)     │ │      (ACID & High Concurrency)    │
└──────────────────────────────────┘ └───────────────────────────────────┘
```

---

## 2. Backend Core (`apps/api`)

| Technology | Version | Role in SoftForge | Rationale & Trade-offs |
| :--- | :--- | :--- | :--- |
| **Python** | `3.12+` | Core API Runtime | Modern typing syntax, high readability for LLMs, extensive ecosystem. |
| **FastAPI** | `0.115+` | HTTP Framework & Routing | Native OpenAPI 3.1 spec generation, built-in dependency injection, and asynchronous throughput. |
| **Pydantic** | `v2.10+` | Validation & DTOs | Rust core (blazing fast), strict data validation, and clean two-way serialization. |
| **SQLAlchemy** | `2.0+ (Async)` | ORM & Query Builder | Industry standard; strictly typed models with `Mapped[...]` and native `AsyncSession`. |
| **Alembic** | `1.13+ (Async)` | Database Migrations | Deterministic schema versioning with async migrations for PostgreSQL and naming conventions. |
| **Loguru** | `0.7+` | Observability & Logging | Structured JSON or colorized console logs with automated `X-Request-ID` correlation. |
| **PyJWT & Passlib** | Latest | Security & Authentication | Password hashing (Argon2 / bcrypt) and dual JWT support (HttpOnly cookies + Bearer headers). |
| **Ruff** | `0.9+` | Linter & Formatter | Rust-based (<100ms execution) replacing Black, Flake8, and isort for spotless code hygiene. |
| **Pytest & pytest-asyncio** | `8.0+` | Test Suite | Async isolated execution with fixtures for database sessions and HTTP client (`httpx`). |

---

## 3. Frontend Core (`apps/web`)

| Technology | Version | Role in SoftForge | Rationale & Trade-offs |
| :--- | :--- | :--- | :--- |
| **React** | `18+ / 19` | UI Library | Universal SPA standard; wide component ecosystem and predictable agent editing. |
| **TypeScript** | `5.0+` | Static Typing | Guarantees that OpenAPI DTOs are strictly honored during development and compile-time. |
| **Vite** | `6.0+` | Bundler & Dev Server | Instant Hot Module Replacement (HMR) powered by esbuild and Rollup. |
| **Tailwind CSS** | `3.4+` | Utility CSS | Design system consistency, zero CSS file overhead, and collision-free styling. |
| **shadcn/ui & Radix** | Standard | Component Library | Accessible (WAI-ARIA compliant), unstyled primitives with code living directly inside repo. |
| **TanStack Query** | `v5` | Server State Management | Invalidation, caching, optimistic updates, and background re-fetching. |
| **Lucide Icons** | Latest | Icon Set | Lightweight, tree-shakeable SVG icons. |

---

## 4. AI Agent Tooling (`tools/scripts/`)

1. **`tools/scripts/slice_scaffold.py`:** Deterministically creates full vertical slices (`schemas.py`, `models.py`, `service.py`, `router.py`, `tests/`).
2. **`tools/scripts/export_openapi.py`:** Generates OpenAPI 3.1 schema definitions.
3. **`tools/scripts/migrate.py`:** Unified Alembic migration runner (`makemigrations`, `upgrade`, `downgrade`, `sql`) with auto-discovery of slice models.
4. **`tools/scripts/verify.py`:** Quality gatekeeper running linters, migration validations, and tests before any task completion.

---

## 5. CI/CD & GitHub Actions Automation

| Component | Configuration | Purpose |
| :--- | :--- | :--- |
| **Quality Gate Workflow** | `.github/workflows/ci.yml` | Triggered on every `push` and `pull_request` targeting `main`. Executes `tools/scripts/verify.py` covering tests, linters, migration validations, and frontend typechecking. |
| **Automated Docs Deployment** | Job `deploy-docs` | Builds VitePress and automatically deploys the static documentation to **GitHub Pages** under the custom domain `softforge.redepronta.com`. |
