# FAQ & Troubleshooting Guide

> **Frequently Asked Questions, Debugging Tips, and Common Fixes**

---

## 1. Frequently Asked Questions (FAQ)

### Can I run SoftForge without Docker?
**Yes.** During development and prototyping, you can run the API using the Python virtual environment (`.venv`) and the frontend with `npm run dev`. Automated integration tests utilize SQLite in-memory, requiring no external databases.

### How does dual authentication work (Cookie + Bearer)?
SoftForge accepts JWT tokens either via the `Authorization: Bearer <token>` header or through a secure `HttpOnly` cookie named `access_token`. This guarantees maximum browser security against XSS attacks while remaining fully compatible with external clients, mobile apps, and tools like Postman or cURL.

### Golden Rule: Why must every feature be rigorously documented?
SoftForge is designed to be operated and expanded by both human engineers and **Autonomous AI Agents** (Cursor, Antigravity, Claude Code, GitHub Copilot).
LLMs rely strictly on code and active documentation in their context windows. **If a feature or architectural decision is undocumented, it does not exist to the AI.** Undocumented changes lead to hallucinations, broken contracts, and redundant code. In SoftForge, documentation evolves continuously alongside implementation in the same pull request or task.

---

## 2. Common Troubleshooting

### Why does opening `docs/dist/index.html` via `file:///` look unstyled?
- **Cause:** VitePress (and modern static site generators) compiles CSS and JS with absolute root paths (e.g. `/assets/style.css`). When opened via local `file:///` paths in Windows Explorer:
  1. The leading slash `/` resolves to your drive root (`V:\assets\...`), triggering 404s for stylesheets and scripts.
  2. Modern web browsers block ES modules (`<script type="module">`) over `file://` due to local file CORS security policies.
- **Solution:**
  1. **Full VitePress Experience (Recommended):** Double-click `docs.bat` in the repository root (or run `.\docs.ps1` in PowerShell). This launches a local static preview server at `http://localhost:5174` with offline search and theme support.
  2. **Zero-Server Standalone Manual:** Open `docs/manual-offline.html` directly with a double-click. It is 100% self-contained with inlined CSS and requires no local server.

### Error: `ModuleNotFoundError: No module named 'greenlet'`
- **Cause:** SQLAlchemy 2.0 Async requires `greenlet` for coroutine dispatch.
- **Solution:** Run `pip install "greenlet>=3.0.0"` in your virtual environment.

### Error: `Port 8000 or 5173 already in use`
- **Cause:** Another process is currently listening on the default API or Vite port.
- **Solution:** Adjust `API_PORT=8001` in your `.env` or terminate the conflicting process.
