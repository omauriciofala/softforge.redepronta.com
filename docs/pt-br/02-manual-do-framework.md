# Manual do Framework SoftForge

> **Arquitetura, Padrões de Projeto e Convenções Internas**  
> *Referência técnica completa do ecossistema SoftForge.*

---

## 1. Filosofia: Por que Vertical Slice Architecture?

Na arquitetura clássica em camadas (Controllers, Services, Repositories), o código de uma funcionalidade fica espalhado por pastas distantes. Quando um agente de IA tenta criar ou alterar um recurso, ele precisa ler e manter dezenas de arquivos em seu contexto de tokens, aumentando drasticamente o risco de alucinações e efeitos colaterais.

No **SoftForge**, cada funcionalidade vive isolada em uma fatia vertical:
```text
apps/api/src/slices/<feature>/
├── schemas.py       # Contratos OpenAPI e DTOs (Pydantic v2)
├── models.py        # Modelos ORM (SQLAlchemy 2.0 Async)
├── service.py       # Lógica pura de negócio
├── router.py        # Endpoints HTTP da fatia
└── tests/           # Testes de integração isolados
```

---

## 2. Anatomia dos Arquivos de uma Fatia

### 2.1 `schemas.py` (Contratos de Dados)
Define exatamente o que entra e o que sai da API:
- `CreateRequest` e `UpdateRequest` com validações via `Field(...)`.
- `Response` com `model_config = ConfigDict(from_attributes=True)` para serialização direta de entidades SQLAlchemy.

### 2.2 `models.py` (Entidades do Banco)
Herda de `src.core.database.Base`:
- Fornece automaticamente: `id` (UUID cross-database), `created_at` e `updated_at`.
- Utiliza a tipagem estrita `Mapped[...]` e `mapped_column(...)`.

### 2.3 `service.py` (Lógica de Negócio)
Funções assíncronas puras recebendo `session: AsyncSession`:
- Sem lógica HTTP (nada de `Request` ou `Response`).
- Dispara exceções de domínio padronizadas (`NotFoundException`, `ForbiddenException`, `AppException`).

### 2.4 `router.py` (Camada HTTP)
Conecta a lógica de negócio à API FastAPI:
- Aplica dependências de segurança e RBAC (`require_workspace_role`).
- Documenta `response_model`, status codes HTTP e tags para o Swagger.

---

## 3. Multi-Tenancy e Controle de Acesso (RBAC)

O SoftForge foi desenhado nativamente para produtos SaaS B2B com suporte a organizações/workspaces:
- **Hierarquia de Papéis:**
  1. `Owner` (Nível 4) — Controle total da organização e faturamento.
  2. `Admin` (Nível 3) — Gerencia membros e configurações de projetos.
  3. `Member` (Nível 2) — Cria e edita projetos, tarefas e recursos.
  4. `Viewer` (Nível 1) — Apenas visualização de dados.

### Protegendo Rotas com RBAC:
```python
from src.slices.workspaces.dependencies import require_workspace_role
from src.slices.workspaces.models import WorkspaceRole

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    membership: Annotated[WorkspaceMember, Depends(require_workspace_role(WorkspaceRole.ADMIN))],
):
    ...
```

---

## 4. Observabilidade & Logs Estruturados

O SoftForge utiliza **Loguru** com injeção automática de **Correlation ID (`X-Request-ID`)**:
- **Em Desenvolvimento:** Logs coloridos, legíveis e com indicação exata de arquivo, função e linha.
- **Em Produção:** JSON estruturado, ideal para ingestão em Datadog, Grafana Loki, CloudWatch ou análise por agentes de IA.
- Toda requisição HTTP responde com os headers `X-Request-ID` e `X-Process-Time` (ex: `12.45ms`).

---

## 5. Ciclo de Vida do Banco de Dados & Migrações (Alembic)

O SoftForge adota o **Alembic assíncrono** com suporte total a migrações orientadas a fatias verticais:

- **Descoberta Automática de Fatias:** O `apps/api/alembic/env.py` invoca `discover_and_import_models()`, detectando qualquer nova fatia criada em `apps/api/src/slices/*/models.py` sem exigir configuração manual.
- **Convenção de Constraints:** Utiliza nomes determinísticos (`pk_...`, `fk_...`, `uq_...`, `ix_...`) garantindo paridade e integridade no PostgreSQL.
- **Ferramenta Unificada (`tools/scripts/migrate.py`):**
  ```bash
  # Gerar nova migração baseada nas alterações dos models
  python tools/scripts/migrate.py makemigrations "adiciona_campo_prioridade"

  # Aplicar migrações pendentes no PostgreSQL
  python tools/scripts/migrate.py upgrade

  # Reverter última migração
  python tools/scripts/migrate.py downgrade -1

  # Validar SQL puro das migrações offline (sem conectar ao banco)
  python tools/scripts/migrate.py sql
  ```
- **Infraestrutura Local:** O arquivo `docker-compose.yml` na raiz sobe o PostgreSQL 16 oficial com um único comando: `docker compose up -d`.
