---
name: pytest-skill
description: "Padrão oficial de testes automatizados para o SoftForge: testes assíncronos de Vertical Slices com httpx.AsyncClient, fixtures de autenticação JWT, validação de RBAC/multi-tenancy e integração com verify.py."
risk: safe
source: community-adapted-fastapi
date_added: "2026-10-11"
---

# FastAPI Slice Testing with Pytest (SoftForge)

Guia definitivo de testes automatizados para as fatias verticais do SoftForge em `apps/api/src/slices/`.

---

## 1. Princípios Inegociáveis

1. **Testes Obrigatórios por Fatia:** Toda nova fatia ou rota deve conter sua suíte de testes em `apps/api/src/slices/<feature>/tests/test_<feature>_slice.py`.
2. **Nenhuma Alteração sem 100% de Aprovação:** Os testes devem ser executados localmente e validados pelo guardrail:
   ```bash
   python tools/scripts/verify.py
   ```
3. **Testes Ponta-a-Ponta de Negócio:** Em vez de mockar internamente toda camada de banco, os testes do SoftForge exercitam o ciclo de vida completo da API usando o cliente HTTP assíncrono oficial.

---

## 2. Estrutura Padrão de Teste de Fatia

Todo teste deve utilizar a fixture `client: AsyncClient` e rodar sobre `@pytest.mark.asyncio`:

```python
import uuid
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_feature_lifecycle_and_rbac(client: AsyncClient) -> None:
    """Valida o ciclo de vida completo da fatia, incluindo autenticação e controle de acesso."""
    
    # 1. Cria usuário de teste com e-mail único
    email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Test User"},
    )
    assert reg_res.status_code == 201

    # 2. Faz login e obtém token JWT
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Executa a operação principal da fatia
    create_res = await client.post(
        "/api/v1/my-feature/items",
        json={"name": "Item Teste", "value": 100},
        headers=headers,
    )
    assert create_res.status_code == 201
    item_id = create_res.json()["id"]

    # 4. Consulta e valida os dados retornados
    get_res = await client.get(f"/api/v1/my-feature/items/{item_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Item Teste"
```

---

## 3. Padrão de Testes de RBAC e Isolamento Multi-Tenant

Sempre que a fatia pertencer ou interagir com workspaces, deve-se testar a segregação de permissões:

```python
@pytest.mark.asyncio
async def test_tenant_isolation_forbidden(client: AsyncClient) -> None:
    """Garante que usuários de outros workspaces recebam 403 Forbidden ao tentar acessar dados alheios."""
    
    # Usuário A cria recurso
    headers_a = await create_authenticated_user(client, "user_a@test.com")
    item_a = (await client.post("/api/v1/items", json={"title": "Doc A"}, headers=headers_a)).json()

    # Usuário B tenta acessar recurso do Usuário A
    headers_b = await create_authenticated_user(client, "user_b@test.com")
    forbidden_res = await client.get(f"/api/v1/items/{item_a['id']}", headers=headers_b)
    
    assert forbidden_res.status_code in (403, 404)
```

---

## 4. Testes Parametrizados de Validação de Input (422)

Use `@pytest.mark.parametrize` para testar limites de esquemas Pydantic e evitar repetição de código:

```python
@pytest.mark.parametrize(
    "invalid_payload,expected_status",
    [
        ({"email": "invalid-email", "password": "123"}, 422), # E-mail inválido
        ({"email": "ok@test.com", "password": ""}, 422),       # Senha vazia
        ({}, 422),                                             # Payload vazio
    ],
)
@pytest.mark.asyncio
async def test_validation_errors(client: AsyncClient, invalid_payload, expected_status) -> None:
    res = await client.post("/api/v1/auth/register", json=invalid_payload)
    assert res.status_code == expected_status
```

---

## 5. Como Executar os Testes

```bash
# Testar uma fatia específica rapidamente:
apps/api/.venv/Scripts/pytest.exe apps/api/src/slices/workspaces/tests/

# Testar todas as fatias com relatório resumido:
apps/api/.venv/Scripts/pytest.exe apps/api/src/slices/ -q

# Executar a verificação mestre do projeto (Testes + Linter + Alembic):
apps/api/.venv/Scripts/python.exe tools/scripts/verify.py
```

---

## 6. Checklist de Qualidade de Testes

- [ ] O teste cria seus próprios dados únicos (`uuid.uuid4().hex`) sem depender de ordem de execução?
- [ ] O teste valida o status code esperado e o schema do JSON retornado?
- [ ] O teste valida cenários negativos (`401 Unauthorized`, `403 Forbidden`, `422 Unprocessable Entity`)?
- [ ] Todos os 37+ testes existentes continuam passando com `pytest apps/api/src/slices/`?
