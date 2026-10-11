---
name: postgres-best-practices
description: "Diretrizes de modelagem relacional, índices declarativos no SQLAlchemy 2.0, prevenção de consultas N+1, migrações sem lock com Alembic e compatibilidade SQLite vs PostgreSQL."
risk: safe
source: community-adapted-supabase
date_added: "2026-10-11"
---

# PostgreSQL & SQLAlchemy Best Practices (SoftForge)

Guia de engenharia de banco de dados relacional e otimização para o SoftForge, cobrindo **SQLAlchemy 2.0 + Alembic**, compatibilidade entre **SQLite local/testes** e **PostgreSQL em produção**.

---

## 1. Princípios Inegociáveis

1. **Modelos Declarativos Padronizados:** Toda tabela deve herdar de `src.core.database.Base` e definir explicitamente `__tablename__`, chaves primárias e índices em chaves estrangeiras.
2. **Separação Rígida entre DTO e ORM:** Modelos SQLAlchemy representam persistência física. Schemas Pydantic em `schemas.py` representam a interface pública. Nunca retorne instâncias do modelo ORM diretamente para a API sem validação com `response_model` ou `.model_validate()`.
3. **Compatibilidade Dupla (SQLite Dev / Postgres Prod):** O código deve passar em 100% dos testes unitários em SQLite e ser capaz de rodar em PostgreSQL em produção sem alterações de sintaxe.

---

## 2. Índices Declarativos no SQLAlchemy 2.0

### Índices Compostos e em Chaves Estrangeiras
Toda coluna de chave estrangeira (`workspace_id`, `user_id`, `project_id`) deve possuir índice indexado para evitar *Full Table Scans* em joins:

```python
from sqlalchemy import Column, String, ForeignKey, Index
from src.core.database import Base

class StoredFile(Base):
    __tablename__ = "stored_files"

    id = Column(String(32), primary_key=True, index=True)
    workspace_id = Column(String(32), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    uploaded_by_user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename = Column(String(255), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False, index=True)

    __table_args__ = (
        # Índice composto para buscas filtradas por workspace e visibilidade
        Index("ix_stored_files_ws_public", "workspace_id", "is_public"),
    )
```

### Índices Parciais (Filtrados)
Para tabelas com grande volume de dados onde apenas uma fração é consultada com frequência (ex: apenas tarefas pendentes ou tokens não expirados):

```python
Index(
    "ix_pending_invites",
    WorkspaceInvite.workspace_id,
    postgresql_where=(WorkspaceInvite.status == "pending"),
)
```

---

## 3. Prevenção do Problema N+1 (Eager Loading)

Nunca itere sobre relacionamentos de modelos SQLAlchemy dentro de loops sem carregar os dados previamente com as estratégias de carregamento adequadas:

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

# 1. Relacionamentos Um-para-Muitos ou Muitos-para-Muitos: use selectinload
stmt = (
    select(Workspace)
    .where(Workspace.id == workspace_id)
    .options(selectinload(Workspace.members))
)
workspace = session.scalars(stmt).first()

# 2. Relacionamentos Muitos-para-Um (Foreign Keys): use joinedload
stmt = (
    select(DevTask)
    .where(DevTask.workspace_id == workspace_id)
    .options(joinedload(DevTask.creator))
)
tasks = session.scalars(stmt).all()
```

---

## 4. Migrações Seguras com Alembic

1. **Geração e Verificação de SQL:** Toda migração deve ser gerada via script padronizado e validada no guardrail mestre:
   ```bash
   python tools/scripts/verify.py
   ```
2. **Índices em Produção sem Travamento (PostgreSQL):**
   Para índices criados em tabelas já volumosas em PostgreSQL, utilizar a diretiva concorrente no script de migração:
   ```python
   def upgrade():
       # Executa sem travar leituras e escritas concorrentes
       op.create_index(
           'ix_large_table_col',
           'large_table',
           ['col'],
           postgresql_concurrently=True
       )
   ```
3. **Valores Padrão Não-Bloqueantes:** Ao adicionar colunas `NOT NULL` com valor padrão em tabelas existentes, use valores constantes (ex: `server_default='false'` ou `server_default='0'`). O PostgreSQL 11+ aplica defaults constantes em metadados instantaneamente sem reescrever a tabela.

---

## 5. Tipos de Dados Agnósticos (SQLite + PostgreSQL)

- **Identificadores Únicos (UUIDs):** Usar `String(32)` ou `CHAR(32)` armazenando strings hexadecimais sem traços (`uuid4().hex`), garantindo indexação B-Tree de alta performance tanto em SQLite quanto em PostgreSQL.
- **Campos JSON Estruturados:** Usar `sqlalchemy.JSON` para garantir compatibilidade com o tipo nativo do SQLite e o tipo `json/jsonb` do PostgreSQL.
- **Datas:** Sempre armazenar em UTC com `DateTime(timezone=True)` ou strings ISO-8601.

---

## 6. Checklist de Modelagem e Banco

- [ ] Todas as Foreign Keys possuem índice correspondente (`index=True`)?
- [ ] Consultas com relacionamentos utilizam `selectinload` ou `joinedload`?
- [ ] Nenhuma migração contém alterações destrutivas sem plano de reversão (`downgrade()`)?
- [ ] O comando de verificação `python tools/scripts/verify.py` executou `alembic upgrade head --sql` com sucesso?
