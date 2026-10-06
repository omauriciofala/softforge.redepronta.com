# Stack Tecnológica Oficial do SoftForge

> **A fundação tecnológica moderna, orientada a contratos e otimizada para operação por Agentes de IA.**

---

## 1. Visão Geral da Stack

O SoftForge foi desenhado com base em um critério rigoroso: **cada tecnologia da stack deve ser determinística, fortemente tipada e com superfície de contexto ideal para Agentes de IA (LLMs) e desenvolvedores humanos.**

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (apps/web)                             │
│      React + TypeScript + Vite + Tailwind CSS + shadcn/ui             │
│      TanStack Query (React Query v5) + Lucide Icons                    │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │
                       Contrato OpenAPI 3.1 & DTOs
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                         BACKEND (apps/api)                             │
│     Python 3.12+ + FastAPI + Pydantic v2 + SQLAlchemy 2.0 Async        │
│     Loguru (Logs Estruturados) + JWT/HttpOnly Cookies + Ruff Linter    │
└───────────────────▲────────────────────────────────▲───────────────────┘
                    │                                │
    (Ambiente de Testes / CI)             (Produção / Local Docker)
                    │                                │
┌───────────────────▼──────────────┐ ┌───────────────▼───────────────────┐
│     SQLite In-Memory             │ │      PostgreSQL 16+               │
│     (Execução em ~2 segundos)    │ │      (Persistência e Concorrência)│
└──────────────────────────────────┘ └───────────────────────────────────┘
```

---

## 2. Backend Core (`apps/api`)

| Tecnologia | Versão | Papel no SoftForge | Por que foi escolhida? |
| :--- | :--- | :--- | :--- |
| **Python** | `3.12+` | Linguagem base da API | Suporte a generics modernos de tipo (`type`, `TypeVar`), alta legibilidade para modelos de IA e ecossistema robusto. |
| **FastAPI** | `0.115+` | Framework HTTP & Roteamento | Geração automática de OpenAPI 3.1, injeção de dependências nativa e alta performance assíncrona com `asyncio`. |
| **Pydantic** | `v2.10+` | Validação de Dados & DTOs | Núcleo escrito em Rust (ultra-rápido), validação rigorosa de esquemas e conversão bidirecional com tipagem estrita. |
| **SQLAlchemy** | `2.0+ (Async)` | ORM & Query Builder | Padrão da indústria para Python; sintaxe tipada com `Mapped[...]`, suporte assíncrono nativo com `AsyncSession`. |
| **Loguru** | `0.7+` | Observabilidade & Logs | Logs estruturados em JSON ou coloridos no terminal, com injeção automática de `X-Request-ID` para rastreabilidade. |
| **PyJWT & Passlib** | Recente | Segurança & Autenticação | Hashing seguro de senhas (Argon2 / bcrypt) e emissão de tokens JWT com dupla camada (HttpOnly cookie + Bearer header). |
| **Ruff** | `0.9+` | Linter e Formatador | Escrito em Rust; substitui Flake8, Black e isort com velocidade instantânea (<100ms), mantendo o código impecável. |
| **Pytest & pytest-asyncio** | `8.0+` | Suíte de Testes | Execução assíncrona isolada com fixtures para sessões de banco e cliente HTTP de teste (`httpx`). |

---

## 3. Frontend Core (`apps/web`)

| Tecnologia | Versão | Papel no SoftForge | Por que foi escolhida? |
| :--- | :--- | :--- | :--- |
| **React** | `18+ / 19` | Biblioteca de UI | Padrão universal para SPAs; ampla compatibilidade e facilidade de manipulação por agentes de código. |
| **TypeScript** | `5.0+` | Superset tipado | Garante que os modelos e DTOs gerados a partir do OpenAPI 3.1 sejam respeitados em tempo de compilação. |
| **Vite** | `6.0+` | Build Tool & Bundler | HMR (Hot Module Replacement) instantâneo, compilação via esbuild/Rollup e inicialização ultrarrápida. |
| **Tailwind CSS** | `3.4+` | Estilização Utilitária | Design system consistente, zero overhead de arquivos CSS separados e sem colisões de classes globais. |
| **shadcn/ui & Radix** | Padrão | Biblioteca de Componentes | Acessibilidade (WAI-ARIA) por padrão, componentes não-opacados (código vive no repo) e customização total. |
| **TanStack Query** | `v5` | Gerenciamento de Estado Server | Cache inteligente, revalidação em segundo plano, mutações assíncronas e controle de loading/error sem boilerplate. |
| **Lucide Icons** | Recente | Conjunto de Ícones | Ícones vetoriais leves, consistentes e fáceis de importar dinamicamente. |

---

## 4. Persistência de Dados & Ambientes

O SoftForge adota uma estratégia **híbrida e inteligente** de banco de dados:

1. **Testes & Protótipos Locais (SQLite In-Memory):**
   - Os testes de integração em `apps/api/src/slices/*/tests/` usam `sqlite+aiosqlite:///:memory:`.
   - **Vantagem:** Toda a suíte de testes do monorepo roda em **menos de 3 segundos** sem necessitar de containers Docker ligados ou portas de rede abertas.
2. **Produção e Staging (PostgreSQL 16+):**
   - Utilizado em ambientes de produção e via `docker compose up` local.
   - Suporte nativo a tipos UUID, índices concorrentes e isolamento transacional ACID.

---

## 5. Ferramental de Agentes de IA (`tools/scripts/`)

Ferramentas nativas do repositório para garantir que qualquer IA (Cursor, Antigravity, Claude Code, Copilot) opere sem degradar a base:

1. **`tools/scripts/slice_scaffold.py`:**
   - Cria o esqueleto completo de uma nova fatia vertical (`schemas.py`, `models.py`, `service.py`, `router.py`, `tests/`) já com tipagem estrita e convenções prontas.
2. **`tools/scripts/export_openapi.py`:**
   - Extrai a especificação OpenAPI 3.1 oficial para `docs/openapi.json` e `contracts/openapi.json`.
3. **`tools/scripts/verify.py`:**
   - Gatekeeper de qualidade: roda o Ruff linter, verifica sintaxe e executa 100% dos testes Pytest antes de qualquer commit ou aprovação de tarefa.

---

## 6. Documentação & Visualização Offline

| Ferramenta | Localização | Função |
| :--- | :--- | :--- |
| **VitePress** | `docs/` | Gerador de documentação estática bilíngue com suporte a tema escuro/claro e motor de busca local (*minisearch*). |
| **`docs.bat` / `docs.ps1`** | Raiz (`/`) | Scripts de inicialização rápida que servem os arquivos estáticos pré-compilados em `http://localhost:5174`. |
| **`manual-offline.html`** | `docs/` | Manual zero-dependências com CSS 100% inlined. Funciona diretamente com duplo clique via `file:///`. |
