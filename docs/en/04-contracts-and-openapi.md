# Contracts & OpenAPI 3.1

> **End-to-End Type Safety and Code Generation**  
> *FastAPI, Pydantic v2, Orval, and TanStack Query.*

---

## 1. Universal Source of Truth

In SoftForge, the frontend never writes loose types or hardcoded URLs.
All network contracts derive directly from the **OpenAPI 3.1.0** specification exported from backend Pydantic models.

---

## 2. Cold Static Extraction (`export_openapi.py`)

No running database or live web server is needed to inspect or export API contracts.
The script `tools/scripts/export_openapi.py` statically instantiates the FastAPI app with an in-memory test engine:
```bash
python tools/scripts/export_openapi.py
```
This updates `apps/api/openapi.json` in milliseconds.

---

## 3. Automated Frontend CodeGen (`Orval`)

SoftForge integrates **Orval** directly into the frontend build and development lifecycle.

### Automatic Execution on `dev` and `build`
Whenever you run either script in `apps/web/`, Orval is automatically triggered before Vite or TypeScript compilation:
```bash
# In development (runs codegen and launches Vite HMR)
npm run dev

# In production build (runs codegen, runs tsc typecheck, and bundles)
npm run build

# Or on-demand:
npm run codegen
```

Orval produces:
- **Strictly Typed TypeScript Models** in `apps/web/src/api/generated/models/`.
- **TanStack Query Hooks** (`useQuery`, `useMutation`) for each backend operation with built-in caching and reactive loading/error states.
- **Configured Axios Client** (`apps/web/src/lib/api-client.ts`) with `withCredentials: true` for HttpOnly cookies and authorization interceptors.

---

## 4. Git Policy & Quality Assurance

- **Ignored in Version Control:** The directory `apps/web/src/api/generated/` is included in `.gitignore` to keep the Git history clean of machine-generated code.
- **Gatekeeper Validation (`verify.py`):** The script `tools/scripts/verify.py` runs `npm run typecheck`, immediately catching any schema discrepancies between backend and frontend before code is merged.
