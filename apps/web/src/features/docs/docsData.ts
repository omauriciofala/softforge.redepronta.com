export interface DocArticle {
  id: string;
  title: string;
  category: string;
  summary: string;
  content: string;
}

export interface DocsLocale {
  label: string;
  navTitle: string;
  backToApp: string;
  categories: {
    name: string;
    articles: DocArticle[];
  }[];
}

export const DOCS_DATA: Record<"pt-br" | "en", DocsLocale> = {
  "pt-br": {
    label: "Português",
    navTitle: "Documentação SoftForge",
    backToApp: "Voltar para o App",
    categories: [
      {
        name: "Primeiros Passos",
        articles: [
          {
            id: "inicio-rapido",
            title: "Guia de Início Rápido",
            category: "Primeiros Passos",
            summary: "Pré-requisitos, inicialização dos serviços e sua primeira fatia em 2 minutos.",
            content: `
### Pré-requisitos
Antes de iniciar, certifique-se de ter instalado em sua máquina:
- **Python 3.12+**
- **Node.js 20+**
- **Docker & Docker Compose** (opcional para SQLite, recomendado para Postgres)

### Passo a Passo Inicial

1. **Configurar variáveis de ambiente:**
\`\`\`bash
cp .env.example .env
\`\`\`

2. **Inicializar o Backend com ambiente virtual:**
\`\`\`bash
python -m venv apps/api/.venv
.\\apps\\api\\.venv\\Scripts\\python.exe -m pip install -e "apps/api[dev]"
\`\`\`

3. **Inicializar o Frontend:**
\`\`\`bash
cd apps/web
npm install
npm run dev
\`\`\`

Frontend disponível em: **http://localhost:5173**  
Documentação Swagger em: **http://localhost:8000/docs**

---

### Criando sua Primeira Fatia em 2 Minutos
Execute o gerador inteligente na raiz do projeto:
\`\`\`bash
python tools/scripts/slice_scaffold.py --name invoices
\`\`\`
Isso gerará contratos Pydantic v2, models SQLAlchemy 2.0 Async, service, router e testes automatizados.
            `,
          },
          {
            id: "faq-troubleshooting",
            title: "FAQ & Solução de Problemas",
            category: "Primeiros Passos",
            summary: "Dúvidas frequentes sobre SQLite, Docker, portas e autenticação dupla.",
            content: `
### Posso usar o SoftForge sem Docker?
**Sim.** Durante prototipagem e desenvolvimento local, o backend roda diretamente no venv Python e os testes utilizam SQLite in-memory, eliminando qualquer dependência externa.

### Como funciona a autenticação dupla (Cookie + Bearer)?
O SoftForge aceita tokens JWT tanto via cookie \`HttpOnly\` (proteção máxima contra XSS no navegador) quanto via header \`Authorization: Bearer <token>\` (ideal para mobile e clientes de API).

### Como rodar a verificação de guardrails?
Execute a qualquer momento:
\`\`\`bash
python tools/scripts/verify.py
\`\`\`
O script valida contratos OpenAPI, executa o linter Ruff e roda os testes de integração do Pytest.
            `,
          },
        ],
      },
      {
        name: "Arquitetura & Engenharia",
        articles: [
          {
            id: "manual-do-framework",
            title: "Manual do Framework",
            category: "Arquitetura & Engenharia",
            summary: "Vertical Slice Architecture, SQLAlchemy 2.0 Async e RBAC multi-tenant.",
            content: `
### Vertical Slice Architecture (Fatias Verticais)
Em vez de separar código em camadas horizontais distantes (controllers, services, repos), cada funcionalidade vive isolada em uma pasta autônoma:
\`\`\`text
apps/api/src/slices/<feature>/
├── schemas.py       # Contratos OpenAPI & DTOs Pydantic v2
├── models.py        # Tabelas do banco SQLAlchemy 2.0 Async
├── service.py       # Lógica pura de negócio
├── router.py        # Rotas HTTP e documentação
└── tests/           # Testes de integração da fatia
\`\`\`

### Multi-Tenancy e RBAC
Suporte nativo a múltiplos workspaces com hierarquia rígida de papéis:
- **Owner (Nível 4):** Acesso total à organização
- **Admin (Nível 3):** Gestão de membros e configurações
- **Member (Nível 2):** Criação e edição de dados
- **Viewer (Nível 1):** Apenas leitura

Proteja qualquer rota com a dependência declarativa:
\`\`\`python
@router.post("/projects")
async def create_project(
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.MEMBER))]
):
    ...
\`\`\`
            `,
          },
          {
            id: "contratos-openapi",
            title: "Contratos & OpenAPI 3.1",
            category: "Arquitetura & Engenharia",
            summary: "Sincronização estática a frio e geração de tipos TypeScript via Orval.",
            content: `
### Extração a Frio de Contratos
No SoftForge você não precisa subir servidores para obter o OpenAPI. O script extrai estaticamente a especificação em milissegundos:
\`\`\`bash
python tools/scripts/export_openapi.py
\`\`\`

### Geração de Hooks com Orval
No frontend, o Orval lê \`apps/api/openapi.json\` e gera:
- Modelos TypeScript 100% tipados em \`src/api/generated/models/\`
- Hooks TanStack Query (\`useQuery\`, \`useMutation\`) com cancelamento automático
- Tipagem estrita de ponta a ponta sem risco de incompatibilidade entre frontend e backend.
            `,
          },
          {
            id: "desenvolvimento-com-ia",
            title: "Fluxo de Desenvolvimento com IA",
            category: "Arquitetura & Engenharia",
            summary: "Como orientar Cursor, Antigravity e Claude Code com o arquivo AGENTS.md.",
            content: `
### A Constituição do Projeto (.ai/AGENTS.md)
O arquivo \`.ai/AGENTS.md\` ensina ao modelo de linguagem todas as restrições arquiteturais antes de ele escrever uma linha de código:
1. **Regra de Ouro:** NUNCA criar camadas horizontais genéricas.
2. **Separação Rígida:** DTOs Pydantic nunca se misturam com instâncias SQLAlchemy ORM.
3. **Guardrail Obrigatório:** Nenhuma alteração é concluída sem que \`verify.py\` passe com 100% de sucesso.

### Ciclo do Agente Autônomo:
Prompt do Usuário ➔ \`slice_scaffold.py\` ➔ Implementação ➔ \`export_openapi.py\` ➔ \`verify.py\` ➔ Entrega Garantida!
            `,
          },
        ],
      },
    ],
  },
  en: {
    label: "English",
    navTitle: "SoftForge Documentation",
    backToApp: "Back to App",
    categories: [
      {
        name: "Getting Started",
        articles: [
          {
            id: "inicio-rapido",
            title: "Getting Started Guide",
            category: "Getting Started",
            summary: "Prerequisites, service startup, and your first slice in 2 minutes.",
            content: `
### Prerequisites
Make sure you have installed:
- **Python 3.12+**
- **Node.js 20+**
- **Docker & Docker Compose** (optional for SQLite, recommended for PostgreSQL)

### Initial Setup

1. **Configure Environment Variables:**
\`\`\`bash
cp .env.example .env
\`\`\`

2. **Initialize Backend with Virtual Environment:**
\`\`\`bash
python -m venv apps/api/.venv
.\\apps\\api\\.venv\\Scripts\\python.exe -m pip install -e "apps/api[dev]"
\`\`\`

3. **Initialize Frontend:**
\`\`\`bash
cd apps/web
npm install
npm run dev
\`\`\`

Frontend App: **http://localhost:5173**  
Swagger OpenAPI Docs: **http://localhost:8000/docs**

---

### Creating Your First Slice in 2 Minutes
Run the intelligent scaffolding tool from the project root:
\`\`\`bash
python tools/scripts/slice_scaffold.py --name invoices
\`\`\`
This scaffolds Pydantic v2 schemas, SQLAlchemy 2.0 Async models, service, router, and integration tests with in-memory SQLite.
            `,
          },
          {
            id: "faq-troubleshooting",
            title: "FAQ & Troubleshooting",
            category: "Getting Started",
            summary: "Frequently asked questions regarding SQLite, Docker, ports, and dual auth.",
            content: `
### Can I run SoftForge without Docker?
**Yes.** During prototyping and development, the backend runs directly in the Python virtual environment and tests use in-memory SQLite, requiring zero external dependencies.

### How does dual authentication work?
SoftForge accepts JWT tokens via both \`HttpOnly\` cookies (maximum browser security against XSS) and \`Authorization: Bearer <token>\` headers (ideal for external clients and mobile apps).

### How to execute the guardrails verification pipeline?
Run at any time:
\`\`\`bash
python tools/scripts/verify.py
\`\`\`
The script validates OpenAPI contracts, executes the Ruff linter, and runs Pytest integration tests.
            `,
          },
        ],
      },
      {
        name: "Architecture & Engineering",
        articles: [
          {
            id: "manual-do-framework",
            title: "Framework Manual",
            category: "Architecture & Engineering",
            summary: "Vertical Slice Architecture, SQLAlchemy 2.0 Async, and multi-tenant RBAC.",
            content: `
### Vertical Slice Architecture
Instead of scattering code across horizontal layers (controllers, services, repositories), each feature lives self-contained in a vertical slice:
\`\`\`text
apps/api/src/slices/<feature>/
├── schemas.py       # OpenAPI contracts & Pydantic v2 DTOs
├── models.py        # SQLAlchemy 2.0 Async database tables
├── service.py       # Pure business logic
├── router.py        # HTTP routes and documentation
└── tests/           # Isolated slice integration tests
\`\`\`

### Multi-Tenancy & RBAC
Native support for multi-workspace SaaS products with strict role hierarchy:
- **Owner (Level 4):** Full organization and billing control
- **Admin (Level 3):** Member and project management
- **Member (Level 2):** Create and update resources
- **Viewer (Level 1):** Read-only access
            `,
          },
          {
            id: "contratos-openapi",
            title: "Contracts & OpenAPI 3.1",
            category: "Architecture & Engineering",
            summary: "Cold static schema extraction and TypeScript code generation with Orval.",
            content: `
### Cold Static Extraction
You don't need running servers or live databases to inspect or export OpenAPI schemas:
\`\`\`bash
python tools/scripts/export_openapi.py
\`\`\`

### Orval Code Generation
In the frontend, Orval reads \`apps/api/openapi.json\` and generates:
- Fully typed TypeScript models in \`src/api/generated/models/\`
- TanStack Query hooks (\`useQuery\`, \`useMutation\`) with automatic cancellation
- End-to-end type safety preventing client/server drift before code reaches production.
            `,
          },
          {
            id: "desenvolvimento-com-ia",
            title: "AI Development Workflow",
            category: "Architecture & Engineering",
            summary: "Steering Cursor, Antigravity, and Claude Code using the AGENTS.md guide.",
            content: `
### The System Constitution (.ai/AGENTS.md)
The \`.ai/AGENTS.md\` file enforces architectural boundaries on language models before they write code:
1. **Golden Rule:** Never create generic horizontal layers.
2. **Strict Separation:** Pydantic DTOs never mix directly with raw SQLAlchemy ORM entities.
3. **Mandatory Guardrail:** No task is complete without passing \`verify.py\` with 100% success.
            `,
          },
        ],
      },
    ],
  },
};
