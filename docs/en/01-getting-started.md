# Getting Started Guide (Quickstart)

> **SoftForge** — AI-Native Fullstack Framework  
> *Go from zero to your first working module in minutes.*

---

## 1. Prerequisites
Before getting started, make sure you have installed on your machine or development container:
- **Python 3.12+** (with `pip` or `uv`)
- **Node.js 20+** (with `npm` or `pnpm`)
- **Docker & Docker Compose** (optional for local SQLite testing, required for full PostgreSQL dev parity)

---

## 2. Step-by-Step Setup

### Step 1: Environment Configuration
In the repository root, copy the template file to create your local `.env`:
```bash
cp .env.example .env
```
Default values are pre-configured for instant local development.

### Step 2: Initialize Backend
Create the virtual environment and install dependencies:
```bash
# In the project root:
python -m venv apps/api/.venv

# Windows:
.\apps\api\.venv\Scripts\python.exe -m pip install -e "apps/api[dev]"

# Linux/macOS:
./apps/api/.venv/bin/python -m pip install -e "apps/api[dev]"
```

### Step 3: Initialize Frontend
```bash
cd apps/web
npm install
npm run dev
```

- Frontend App: **[http://localhost:5173](http://localhost:5173)**  
- Interactive OpenAPI Swagger Docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 3. Running with Docker (Recommended)
If Docker is installed, you can spin up the full stack with a single command:
```bash
make up
# or: docker compose up -d
```
This starts:
- **Database:** PostgreSQL 16 on port `5432`
- **Backend API:** FastAPI on port `8000`
- **Frontend SPA:** React on port `5173`

---

## 4. Creating Your First Slice in 2 Minutes

SoftForge provides an automated slice generator for you and your AI agents:
```bash
python tools/scripts/slice_scaffold.py --name invoices
```

This immediately scaffolds:
- `apps/api/src/slices/invoices/schemas.py` (Pydantic v2 contracts)
- `apps/api/src/slices/invoices/models.py` (SQLAlchemy 2.0 Async tables)
- `apps/api/src/slices/invoices/service.py` (Business logic and CRUD operations)
- `apps/api/src/slices/invoices/router.py` (Documented HTTP routes)
- `apps/api/src/slices/invoices/tests/` (Automated integration tests with in-memory SQLite)

To register the new slice:
1. Open `apps/api/src/main.py`.
2. Add:
```python
from src.slices.invoices.router import router as invoices_router
app.include_router(invoices_router, prefix=settings.API_V1_STR)
```
3. Export the updated OpenAPI spec and verify:
```bash
python tools/scripts/export_openapi.py
python tools/scripts/verify.py
```
Done! Your new module is completely typed, tested, and documented.
