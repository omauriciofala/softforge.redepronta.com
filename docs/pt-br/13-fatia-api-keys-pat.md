# Fatia Vertical: Chaves de API & PAT (Machine-to-Machine)

> **Autenticação Machine-to-Machine (M2M) para Agentes Autônomos de IA, CLI e pipelines CI/CD com hash SHA-256 e isolamento multi-tenant.**

---

## 1. Visão Geral da Fatia

A fatia `apikeys` (`apps/api/src/slices/apikeys/`) fornece o canal oficial de autenticação programática e autônoma do SoftForge:

- **Autenticação M2M First-Class:** Permite que agentes externos de IA (ex: Cursor, Claude Dev, AutoPR, GitHub Actions, scripts em Python ou Go) executem operações na API sem depender de sessões de navegador ou tokens JWT de vida curta.
- **Armazenamento Seguro por Hash SHA-256:** O segredo em texto puro (`sf_live_...`) é gerado com alta entropia criptográfica (`secrets.token_urlsafe(32)`) e exibido **apenas uma vez** no momento da criação. O banco de dados armazena exclusivamente o digest hexadecimal SHA-256 (`hashed_key`).
- **Identificação Visual via Prefixo Mascarado:** A listagem de chaves expõe um prefixo mascarado (`key_prefix`, ex: `sf_live_a1b2...9xyz`), viabilizando que administradores identifiquem a chave sem expor credenciais.
- **Validade Temporal & Expiração Configurável:** Cada chave pode ser gerada com validade permanente ou com prazo de expiração em dias (`expires_in_days`), após o qual a autenticação é rejeitada automaticamente com HTTP 401 Unauthorized.
- **Revogação Instantânea:** Chaves podem ser revogadas a qualquer momento por administradores do workspace, cessando imediatamente o acesso.
- **Isolamento Rígido Multi-Tenant:** Toda chave de API pertence estritamente ao seu workspace de origem. Tentativas de acessar recursos de outros workspaces são barradas pelo RBAC com HTTP 403 Forbidden.
- **Auditoria & Webhooks Integrados:** Eventos de criação (`api_key.created`) e revogação (`api_key.revoked`) disparam registros imutáveis na trilha de auditoria e notificações para webhooks outbound configurados.

---

## 2. Diagrama de Autenticação M2M

```mermaid
sequenceDiagram
    autonumber
    actor Agente as Agente de IA / Script CI
    participant API as API SoftForge (FastAPI)
    participant Auth as Auth Dependency (get_current_user)
    participant Service as ApiKey Service
    participant DB as Banco PostgreSQL (api_keys)
    participant Resource as Endpoint (/projects)

    Agente->>API: GET /api/v1/workspaces/{id}/projects
    Note over Agente,API: Header "X-API-Key: sf_live_..." ou "Authorization: Bearer sf_live_..."
    API->>Auth: Injeta dependência get_current_user
    Auth->>Service: authenticate_api_key(session, raw_key)
    Service->>Service: Calcula hash SHA-256 da chave recebida
    Service->>DB: Busca chave ativa onde hashed_key = digest
    DB-->>Service: Retorna ApiKey + Usuário criador
    Service->>Service: Valida is_revoked=False e expires_at > now()
    Service->>DB: Atualiza last_used_at = now()
    Service-->>Auth: Retorna Usuário criador
    Auth->>Resource: Prossegue com contexto de segurança e tenant validado
    Resource-->>Agente: HTTP 200 OK (Dados dos projetos)
```

---

## 3. Como Utilizar as Chaves de API

As chaves de API do SoftForge podem ser enviadas de duas formas padrão na requisição HTTP:

### Opção A: Cabeçalho `X-API-Key` (Recomendado para Scripts e Agentes)

```bash
curl -X GET "https://api.softforge.redepronta.com/api/v1/workspaces/{workspace_id}/projects" \
  -H "X-API-Key: sf_live_SUA_CHAVE_SECRETA_AQUI"
```

### Opção B: Cabeçalho `Authorization: Bearer` (Padrão RFC 6750)

```bash
curl -X GET "https://api.softforge.redepronta.com/api/v1/auth/me" \
  -H "Authorization: Bearer sf_live_SUA_CHAVE_SECRETA_AQUI"
```

---

## 4. Endpoints da Fatia

| Método | Rota | Descrição | Permissão Mínima |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/workspaces/{workspace_id}/api-keys` | Cria uma nova chave de API e retorna o segredo bruto | `Admin` |
| `GET` | `/api/v1/workspaces/{workspace_id}/api-keys` | Lista as chaves de API registradas (com máscara) | `Admin` |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/api-keys/{key_id}` | Revoga imediatamente a chave de API | `Admin` |

---

## 5. Exemplo de Resposta na Criação

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "workspace_id": "7ca64c12-3211-419b-a0d3-5b8719bc16da",
  "user_id": "1ea29b33-4182-411a-82dc-3b4908ef1234",
  "name": "Cursor AI Agent",
  "key_prefix": "sf_live_a1b2...9xyz",
  "scopes": ["*"],
  "expires_at": "2026-11-05T12:00:00Z",
  "last_used_at": null,
  "is_revoked": false,
  "revoked_at": null,
  "created_at": "2026-10-06T12:00:00Z",
  "raw_key": "sf_live_4kH8jL2mN9pQ1rS3tU5vW7xY0zA2bC4dE6fG8hI0"
}
```

> [!IMPORTANT]
> O campo `raw_key` é retornado **exclusivamente na criação**. Ele nunca é armazenado em formato legível e não pode ser recuperado se perdido. Caso seja esquecido, revogue a chave anterior e gere uma nova.

---

## 6. Validação Automática & Testes

A fatia conta com 100% de cobertura nos testes determinísticos do Pytest (`test_apikeys_slice.py`):
1. **Geração e Hashing:** Garante formato do prefixo e conformidade com o algoritmo SHA-256.
2. **Ciclo de Vida CRUD:** Criação, mascaramento na listagem e revogação.
3. **Autenticação Real & Isolamento:** Autenticação direta via `X-API-Key` e `Authorization: Bearer`, além do bloqueio entre workspaces com HTTP 403 Forbidden.
4. **Proteção Contra Chaves Inválidas:** Resposta 401 Unauthorized para chaves forjadas, revogadas ou expiradas.
