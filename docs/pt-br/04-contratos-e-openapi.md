# Contratos & OpenAPI 3.1

> **Sincronização Tipada de Ponta a Ponta**  
> *FastAPI, Pydantic v2, Orval e TanStack Query.*

---

## 1. Fonte Única da Verdade

No SoftForge, o frontend nunca cria tipos manuais ou URLs "chumbadas".
Toda a comunicação é baseada no contrato **OpenAPI 3.1.0** gerado automaticamente a partir dos modelos Pydantic v2 do FastAPI.

---

## 2. Extração Estática a Frio (`export_openapi.py`)

Em frameworks tradicionais, para exportar a especificação OpenAPI você precisa rodar a API, subir banco de dados e bater em `http://localhost:8000/openapi.json`.

No SoftForge, o script `tools/scripts/export_openapi.py` extrai a especificação completa **a frio**, em menos de 1 segundo, instanciando o objeto FastAPI diretamente com banco mockado:
```bash
python tools/scripts/export_openapi.py
```
Isso gera o arquivo canônico `apps/api/openapi.json`.

---

## 3. Geração Automática de Hooks no Frontend (`Orval`)

O SoftForge integra o **Orval** diretamente ao ciclo de desenvolvimento do frontend. 

### Execução Automática no `dev` e `build`
Ao rodar qualquer um dos comandos abaixo em `apps/web/`, o Orval é disparado antes de iniciar o servidor ou compilar:
```bash
# Durante o desenvolvimento (roda codegen e inicia o Vite)
npm run dev

# Na compilação de produção (roda codegen, checa tipos com tsc e empacota o build)
npm run build

# Ou sob demanda:
npm run codegen
```

O Orval gera:
- **Modelos TypeScript 100% tipados** em `apps/web/src/api/generated/models/`.
- **Hooks do TanStack Query** (`useQuery`, `useMutation`) para cada endpoint da API com gerenciamento automático de cache e estados de loading/error.
- **Cliente Axios Pré-configurado** (`apps/web/src/lib/api-client.ts`) com envio seguro de cookies `HttpOnly` e interceptors para bearer tokens.

---

## 4. Política de Git & Qualidade Contínua

- **Diretório Ignorado no Git:** A pasta `apps/web/src/api/generated/` está listada no `.gitignore` para manter o histórico de commits limpo e livre de artefatos efêmeros gerados por máquina.
- **Validação no Pipeline (`verify.py`):** O script `tools/scripts/verify.py` executa o typecheck completo do frontend (`npm run typecheck`), garantindo que qualquer quebra de contrato entre backend e frontend seja detectada imediatamente antes de qualquer entrega ou commit.
