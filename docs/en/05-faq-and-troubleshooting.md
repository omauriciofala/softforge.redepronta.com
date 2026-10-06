# FAQ & Troubleshooting

> **Frequently Asked Questions, Debugging Tips, and Solutions**

---

## 1. Frequently Asked Questions (FAQ)

### Can I run SoftForge without Docker?
**Yes.** For prototyping and local development, run the FastAPI backend inside the Python virtual environment (`.venv`) and the frontend with `npm run dev`. Automated tests use an in-memory SQLite database, requiring no external services.

### How does dual-mode authentication work?
SoftForge accepts JWT tokens either via the `Authorization: Bearer <token>` header or via the `access_token` HttpOnly cookie. This provides security against XSS in web browsers while maintaining compatibility with curl, mobile apps, and external API clients.

### How do vertical slices share data?
Vertical slices should not import private models or services from other slices. Instead, they reference foreign entities via primitive UUIDs (`workspace_id`, `user_id`). Shared infrastructure logic belongs in `src/core/`.

---

## 2. Troubleshooting Common Issues

### Issue: `ModuleNotFoundError: No module named 'greenlet'`
- **Cause:** Async SQLAlchemy 2.0 requires `greenlet`.
- **Fix:** Run `pip install "greenlet>=3.0.0"` in your virtual environment.

### Issue: `Port 8000 or 5173 already in use`
- **Cause:** A lingering process is holding the default ports.
- **Fix:** Change ports in `.env` (`API_PORT=8001`) or terminate the conflicting process.

### How to reset the local Docker database?
Run:
```bash
docker compose down -v
docker compose up -d
```
This flushes the `pgdata` volume and re-initializes Postgres with fresh tables.
