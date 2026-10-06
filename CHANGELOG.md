# Changelog — SoftForge

Todas as mudanças notáveis neste projeto são documentadas aqui seguindo o padrão [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [v1.0.0] - 2026-10-06

**General Availability (GA) — O Framework Fullstack AI-Native definitivo.**

Esta versão marca a primeira edição estável do **SoftForge**, consolidando as 10 fases da fundação da arquitetura, 42 testes de integração assíncronos no backend com SQLite em memória, 11 migrações Alembic validadas, suporte a múltiplos motores de frontend e temas, e as diretrizes universais de IA baseadas na filosofia de Andrej Karpathy.

### ✨ Novas Funcionalidades

#### 1. Arquitetura e Núcleo do Sistema
- **Vertical Slice Architecture:** Fatias verticais autossuficientes em `apps/api/src/slices/` com separação estrita entre contratos OpenAPI Pydantic v2 e tabelas SQLAlchemy 2.0 Async.
- **Spec-First Determinístico:** Contratos OpenAPI 3.1 exportados a frio (<1s) via `tools/scripts/export_openapi.py`.
- **Pipeline Unificado de Guardrails:** Script mestre `tools/scripts/verify.py` executando 5 verificações automáticas (OpenAPI, Pytest, Alembic SQL, Ruff, TypeScript Typecheck).
- **Ambiente Conteinerizado:** Docker Compose e DevContainer com PostgreSQL 16, Redis 7, Backend FastAPI, Workers Arq e Frontend Vite.

#### 2. Fatias de Negócio e Segurança
- **Autenticação & Sessões:** JWT assimétrico com claims de tenant, hash bcrypt/argon2 e rota `/api/v1/auth`.
- **Social OAuth2:** Fluxo Authorization Code e auto-linking por e-mail para **Google** e **GitHub** (`apps/api/src/slices/oauth/`).
- **Multi-Tenancy & RBAC:** Isolamento estrito por `workspace_id` e controle de acesso hierárquico (Owner, Admin, Member, Viewer).
- **Convites de Equipe:** Geração de convites com tokens assinados criptograficamente válidos por 7 dias (`apps/api/src/slices/invites/`).
- **Billing & Mercado Pago:** Suporte nativo a Pix Transparente com QR Code dinâmico e chave copia-e-cola, cartões, planos e cotas declarativas (`apps/api/src/slices/billing/`).
- **Chaves de API / PAT (M2M):** Autenticação Machine-to-Machine com prefixos mascarados e hash SHA-256 (`apps/api/src/slices/api_keys/`).
- **Trilha de Auditoria:** Registros de compliance imutáveis com despacho assíncrono de latência zero (`apps/api/src/slices/audit/`).
- **Notificações In-App & WebSockets:** Canal persistente bidirecional (`/notifications/ws`), broadcast multitela e contadores de badge (`apps/api/src/slices/notifications/`).
- **Webhooks Outbound:** Despacho assíncrono via Arq Worker com assinatura HMAC-SHA256 e timestamp anti-replay (`X-SoftForge-Signature`).
- **Storage & Uploads:** Persistência híbrida unificada (disco local em dev/testes e compatibilidade com AWS S3/MinIO em prod).
- **Rate Limiting:** Algoritmo de janela deslizante com Redis ZSET em prod e fallback em memória para testes offline (`apps/api/src/core/ratelimit.py`).
- **Feature Flags & Toggles:** Catálogo de flags globais com overrides por Workspace (`apps/api/src/slices/feature_flags/`).
- **Internacionalização (i18n):** Negociação de conteúdo RFC 7231 (`Accept-Language`), exceções traduzidas dinamicamente e suporte nativo a `pt-BR` e `en-US`.

#### 3. Temas Plugáveis & Frontend
- **Sistema Universal de Temas:** Especificação de manifesto `softforge-theme.json` e tokens CSS universais (`--sf-*`).
- **Catálogo de Temas:** Starters de referência para **React 18 + Tailwind** (`themes/default-react`) e **HTML5 + Bootstrap 5.3 + Vanilla JS** (`themes/bootstrap-starter`).
- **Dashboard Unificado (`apps/web`):** Interface completa em React com visualizadores dedicados para todas as fatias do framework, sino de notificações em tempo real e seletor de temas e idiomas.

#### 4. Engenharia de IA & Scaffolding
- **Diretrizes Karpathy:** Skill canônica `.agents/skills/karpathy-guidelines/SKILL.md` com os 4 princípios fundamentais (*Think Before Coding*, *Simplicity First*, *Surgical Changes*, *Goal-Driven Execution*).
- **Suporte Multi-IA Nativo:** Pontes de descoberta para Google Antigravity, Claude Code (`CLAUDE.md`), Cursor (`AGENTS.md`), Windsurf e GitHub Copilot (`.github/copilot-instructions.md`).
- **Scaffolder Integrado:** `tools/scripts/slice_scaffold.py` e `tools/scripts/init_project_ai.py` para geração de código com IA e inicialização de novos projetos.
- **Automação de Release:** `tools/scripts/release.py` para gestão SemVer, guardrails pré-release e sincronização de manifestos.
