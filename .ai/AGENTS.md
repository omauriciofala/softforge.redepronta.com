# SoftForge — Master Agent Guidelines (AGENTS.md)
> **Instruções Mestras para Agentes Autônomos de IA e Assistentes de Código**  
> *Leia este documento com prioridade máxima antes de planejar ou alterar qualquer arquivo neste repositório.*

---

## 1. Princípios Inegociáveis

1. **Vertical Slice Architecture (Fatias Verticais):**
   - NUNCA crie camadas horizontais genéricas (ex: controllers globais, repositórios universais).
   - Todo novo domínio de negócio pertence a `apps/api/src/slices/<feature_name>/`.
   - Cada fatia deve conter: `schemas.py`, `models.py`, `service.py`, `router.py` e sua pasta de testes `tests/`.

2. **OpenAPI 3.1 como Fonte Única da Verdade:**
   - Schemas Pydantic em `schemas.py` definem a API pública.
   - O frontend NUNCA inventa tipos ou faz chamadas sem passar pelos contratos.
   - Sempre exporte o OpenAPI atualizado usando: `python tools/scripts/export_openapi.py`.

3. **Separação Rígida entre DTO e Banco:**
   - Modelos SQLAlchemy 2.0 (`models.py`) representam tabelas do banco.
   - Schemas Pydantic (`schemas.py`) representam dados recebidos e devolvidos pela API.
   - NUNCA exponha instâncias ORM diretamente para o cliente sem passar por validação com `response_model` ou `.model_validate()`.

4. **Multi-Tenancy e RBAC:**
   - Todo recurso pertencente a uma organização/workspace deve receber o `workspace_id` e ser protegido com `require_workspace_role(...)` em `apps/api/src/slices/workspaces/dependencies.py`.
   - NUNCA execute consultas sem filtrar pelo `workspace_id` adequado.

5. **Documentação Contínua Inegociável (Documentation-First):**
   - O SoftForge é operado por humanos e Agentes de IA. O que não estiver documentado, para a IA não existe.
   - Toda implementação de código, novo slice ou alteração de arquitetura DEVE atualizar a documentação (`docs/` e `.ai/`) concomitantemente. A documentação evolui junto com o framework.

---

## 2. Anatomia de uma Fatia Vertical (`apps/api/src/slices/<feature>/`)

```text
apps/api/src/slices/<feature>/
├── __init__.py           # Exporta roteador ou símbolos públicos
├── schemas.py            # Pydantic v2 (Create, Update, Response, Filters)
├── models.py             # Tabelas SQLAlchemy 2.0 herdando de Base (src.core.database)
├── service.py            # Lógica pura de negócio e consultas SQLAlchemy
├── router.py             # Endpoints FastAPI com tags, status e documentação
└── tests/
    ├── __init__.py
    └── test_<feature>_slice.py # Testes de integração assíncronos usando SQLite in-memory
```

---

## 3. Workflow Determinístico para Agentes de IA

Quando solicitado a implementar uma nova funcionalidade, siga rigorosamente estes 7 passos:

```mermaid
graph TD
    Step1["1. Executar Scaffold da Fatia"] --> Step2["2. Definir Schemas e Models"]
    Step2 --> Step3["3. Implementar Lógica no Service & Router"]
    Step3 --> Step4["4. Escrever Testes de Integração"]
    Step4 --> Step5["5. Exportar Contratos OpenAPI"]
    Step5 --> Step6["6. Atualizar Documentação"]
    Step6 --> Step7["7. Executar Pipeline de Verificação (verify)"]
```

### Passo 1: Scaffold
Execute o gerador automático para criar o esqueleto da nova fatia:
```bash
python tools/scripts/slice_scaffold.py --name <nome_da_fatia>
```

### Passo 2: Contratos & Modelos
- No arquivo `schemas.py`, declare as estruturas de entrada e saída. Use tipos primitivos estritos, `Field(description=...)` e validações do Pydantic.
- No arquivo `models.py`, herde de `src.core.database.Base` para herdar automaticamente `id` (UUID), `created_at` e `updated_at`.

### Passo 3: Service & Router
- Em `service.py`, escreva funções assíncronas puras recebendo `session: AsyncSession`.
- Em `router.py`, crie o `APIRouter` com tags descritivas e configure `response_model` em cada rota.

### Passo 4: Testes
- Crie testes em `tests/test_<feature>_slice.py` testando o ciclo completo (sucesso, validação inválida, autorização e 404).

### Passo 5: Exportação de Contratos
- Atualize a especificação OpenAPI:
```bash
python tools/scripts/export_openapi.py
```

### Passo 6: Atualizar Documentação
- Documente a nova fatia ou alteração nos guias correspondentes (`docs/pt-br/` e `docs/en/`).
- Atualize `.ai/AGENTS.md` ou `.ai/rules/` caso novas regras arquiteturais tenham sido introduzidas.
- Recompile a documentação estática:
```bash
cd docs && npx vitepress build
```

### Passo 7: Verificação de Qualidade
- Antes de entregar a resposta ao usuário, rode a suíte de verificação:
```bash
python tools/scripts/verify.py
```

---

## 4. Como Tratar Erros
- Use as exceções padronizadas de `src.core.errors`:
  - `NotFoundException("Recurso não encontrado")` -> Retorna 404
  - `UnauthorizedException("Token inválido")` -> Retorna 401
  - `ForbiddenException("Permissão insuficiente")` -> Retorna 403
  - `AppException("Regra de negócio violada", status_code=400)` -> Retorna 400
- Toda resposta de erro inclui automaticamente o `request_id` para correlação e auditoria.
