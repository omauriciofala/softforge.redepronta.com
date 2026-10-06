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
Isso gera o arquivo `apps/api/openapi.json`.

---

## 3. Geração Automática de Hooks no Frontend (`Orval`)

Com o `openapi.json` gerado, você executa o Orval dentro de `apps/web`:
```bash
cd apps/web
npm run codegen
```
O Orval gera:
- Modelos TypeScript 100% tipados em `apps/web/src/api/generated/models/`.
- Hooks do TanStack Query (`useQuery`, `useMutation`) para cada endpoint da API.
- Configuração automática do cliente Axios com cookies HttpOnly e interceptors.

Se o backend alterar o tipo de um campo ou remover um endpoint, o comando `npm run typecheck` no frontend falhará imediatamente no build, prevenindo qualquer bug em produção antes do commit!
