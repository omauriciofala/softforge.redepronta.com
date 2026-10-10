# Especificação de Extração Funcional e Engenharia Reversa
> **Sistema de Origem:** `{SYSTEM_NAME}`  
> **Status:** `Em Análise` | `Em Desenvolvimento` | `Migrado`  
> **Fatia Vertical de Destino no SoftForge:** `apps/api/src/slices/{TARGET_SLICE}/`  
> **Feature Frontend no SoftForge:** `apps/web/src/features/{TARGET_SLICE}/`  

---

## 1. Identificação do Sistema Legado

- **Nome do Projeto/Módulo:** `{SYSTEM_NAME}`
- **Origem / Repositório Original:** (ex: `https://github.com/empresa/legado-crm` ou caminho local)
- **Stack Original do Legado:** (ex: Express.js + MongoDB, Django + PostgreSQL, PHP/Laravel, Java/Spring Boot)
- **Framework de UI Original:** (ex: Bootstrap 4, Angular 1, Blade, JSP, jQuery) — *Lembrete: Nenhum elemento de UI antigo será reaproveitado no SoftForge*.
- **Data de Início da Análise:** `YYYY-MM-DD`

---

## 2. Escopo Funcional & Decisões Arquiteturais

### O que SERÁ migrado para o SoftForge:
- [ ] Regra 1: ...
- [ ] Regra 2: ...

### O que NÃO será migrado (Descarte / Otimização):
- [ ] Módulo legado obsoleto: ...
- [ ] Gambiarras ou regras descontinuadas: ...

---

## 3. Matriz de De-Para de Dados (Modelos)

Mapeamento das entidades originais para modelos SQLAlchemy 2.0 do SoftForge (herdeiros de `src.core.database.Base`).

| Entidade / Tabela Legada | Tabela SoftForge (`models.py`) | Campos Principais | Suporte a Multi-Tenancy |
| :--- | :--- | :--- | :--- |
| `tb_exemplo` | `{TARGET_SLICE}` | `id`, `workspace_id`, `name`, `status` | `workspace_id` obrigatório |

### Estrutura Detalhada dos Campos:
```python
# Exemplo de rascunho de models.py
class Exemplo(Base):
    __tablename__ = "{TARGET_SLICE}"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Demais campos mapeados...
```

---

## 4. Matriz de Contratos & Endpoints da API

Mapeamento das rotas antigas para contratos Pydantic v2 e endpoints FastAPI.

| Endpoint Original | Método | Rota SoftForge | Schemas (Input / Output) | Papel Mínimo (RBAC) |
| :--- | :--- | :--- | :--- | :--- |
| `/api/items` | `GET` | `/workspaces/{workspace_id}/{TARGET_SLICE}` | `None` / `list[ItemResponse]` | `VIEWER` |
| `/api/items` | `POST` | `/workspaces/{workspace_id}/{TARGET_SLICE}` | `ItemCreate` / `ItemResponse` | `MEMBER` |
| `/api/items/:id` | `GET` | `/workspaces/{workspace_id}/{TARGET_SLICE}/{id}` | `None` / `ItemResponse` | `VIEWER` |
| `/api/items/:id` | `PATCH`| `/workspaces/{workspace_id}/{TARGET_SLICE}/{id}` | `ItemUpdate` / `ItemResponse` | `MEMBER` |
| `/api/items/:id` | `DELETE`| `/workspaces/{workspace_id}/{TARGET_SLICE}/{id}` | `None` / `204 No Content` | `ADMIN` |

---

## 5. Regras de Negócio e Algoritmos (`service.py`)

Descreva aqui a lógica pura que estava em controllers/services legados e deve ser implementada no SoftForge:

1. **Validação de Entrada:**
   - Regra: ...
2. **Cálculos ou Processamento:**
   - Regra: ...
3. **Efeitos Colaterais / Notificações / Auditoria:**
   - Disparo de evento de auditoria (`src.slices.audit.service.record_audit_log`): ...
   - Notificação in-app (`src.slices.notifications.service.create_notification`): ...

---

## 6. Jornada do Usuário & Interface (Design System SoftForge)

> ⚠️ **ATENÇÃO:** NUNCA copie HTML, CSS, Bootstrap, Materialize ou arquivos de estilo do sistema legado.  
> A UI no SoftForge deve ser 100% nativa em React + Tailwind CSS + componentes de `@/components/ui/`.

### Telas a Criar em `apps/web/src/features/{TARGET_SLICE}/`:
- [ ] **Visão de Listagem / Dashboard:**
  - Componentes SoftForge: `Card`, `Badge`, `Button`, `Table`, `Input` de busca.
  - Ícone Lucide sugerido: ...
- [ ] **Modal ou Formulário de Criação / Edição:**
  - Componentes SoftForge: `Dialog`, `Form`, `Input`, `Select`, `Button`.
- [ ] **Ações de Detalhe / Exclusão:**
  - Confirmação com `AlertDialog`.

---

## 7. Critérios de Aceite e Matriz de Testes

Testes de integração a serem codificados em `apps/api/src/slices/{TARGET_SLICE}/tests/test_{TARGET_SLICE}_slice.py`:

- [ ] `test_{TARGET_SLICE}_crud_lifecycle`: Criação, leitura, atualização e exclusão completa.
- [ ] `test_{TARGET_SLICE}_multi_tenant_isolation`: Garantir que Workspace A não enxerga dados de Workspace B.
- [ ] `test_{TARGET_SLICE}_rbac_permissions`: Membros com papel VIEWER não conseguem deletar ou criar.
- [ ] `test_{TARGET_SLICE}_validation_rules`: Rejeição com status 422 para payloads inválidos.

---

## 8. Checklist de Validação Final

- [ ] Fatia vertical gerada via `python tools/scripts/slice_scaffold.py --name {TARGET_SLICE}`.
- [ ] Router registrado em `apps/api/src/main.py`.
- [ ] Auditoria de conformidade aprovada: `python tools/scripts/reverse_engineering.py audit --slice {TARGET_SLICE}`.
- [ ] Contratos exportados: `python tools/scripts/export_openapi.py`.
- [ ] Testes e guardrails 100% aprovados: `python tools/scripts/verify.py`.
- [ ] Documentação bilíngue criada/atualizada em `docs/pt-br/` e `docs/en/`.
