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

Running Orval inside `apps/web`:
```bash
cd apps/web
npm run codegen
```
Produces:
- TypeScript models in `src/api/generated/models/`.
- TanStack Query hooks (`useQuery`, `useMutation`) for each backend operation.
- Axios client integration with automatic HttpOnly cookie credentials.
