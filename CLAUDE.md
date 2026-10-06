# CLAUDE.md — Claude Code Guidelines for SoftForge

> **Universal Coding Instructions for Claude Code & Anthropic Models**  
> Canonical Skill: `.agents/skills/karpathy-guidelines/SKILL.md`  
> Master Architecture Guidelines: `AGENTS.md`

---

## 1. Andrej Karpathy LLM Coding Principles

Every change in SoftForge must adhere to these 4 principles:
1. **Think Before Coding:** Inspect files, models, and schemas before writing code. Surface tradeoffs early. Push back against architectural violations or unneeded dependencies. Ask when confused.
2. **Simplicity First:** Write the minimum viable code. No speculative abstractions, repository wrappers, or premature generalizations.
3. **Surgical Changes:** Modify only what is strictly necessary. Match existing conventions. Preserve existing comments and docs. Clean your own mess.
4. **Goal-Driven Execution:** Define testable criteria upfront. Write integration tests. Run the unified verification pipeline and verify 100% pass before reporting:
   ```bash
   python tools/scripts/verify.py
   ```

---

## 2. Common Commands

- **Run Unified Quality Gate (All-in-one):**
  ```bash
  python tools/scripts/verify.py
  ```
- **Backend Tests (Pytest with in-memory SQLite):**
  ```bash
  cd apps/api && python -m pytest -v
  ```
- **Run a single test file:**
  ```bash
  cd apps/api && python -m pytest src/slices/<feature>/tests/test_<feature>_slice.py -v
  ```
- **Backend Linter (Ruff):**
  ```bash
  cd apps/api && python -m ruff check src
  ```
- **Export OpenAPI 3.1 Spec:**
  ```bash
  python tools/scripts/export_openapi.py
  ```
- **Scaffold New Vertical Slice:**
  ```bash
  python tools/scripts/slice_scaffold.py --name <feature_name>
  ```
- **Database Migrations Check (Offline SQL DDL):**
  ```bash
  python tools/scripts/migrate.py sql
  ```
- **Frontend Typecheck & Build:**
  ```bash
  cd apps/web && npm run typecheck
  cd apps/web && npm run build
  ```
- **Documentation Build:**
  ```bash
  powershell -ExecutionPolicy Bypass -File docs.ps1
  ```

---

## 3. Architecture Invariants

- **Vertical Slice Architecture:** Everything lives in `apps/api/src/slices/<feature>/` (`schemas.py`, `models.py`, `service.py`, `router.py`, `tests/`).
- **OpenAPI 3.1 Contracts:** Pydantic schemas in `schemas.py` dictate the contract. The web frontend strictly consumes these contracts.
- **ORM / DTO Separation:** SQLAlchemy models (`models.py`) inherit from `src.core.database.Base`. Pydantic models (`schemas.py`) handle serialization. Never expose raw ORM models directly without validation.
- **Multi-Tenancy & RBAC:** Every workspace-scoped query and endpoint must be secured by `workspace_id` and `require_workspace_role(...)`.
- **Documentation-First:** Always update documentation in `docs/pt-br/` and `docs/en/` when introducing features, schemas, or architectural patterns.
