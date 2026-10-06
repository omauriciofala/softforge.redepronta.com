# Guia de Início Rápido (Quickstart)

> **SoftForge** — Framework Fullstack AI-Native  
> *Comece do zero ao seu primeiro módulo funcional em poucos minutos.*

---

## 1. Pré-requisitos
Antes de iniciar, certifique-se de ter instalado em sua máquina ou ambiente de desenvolvimento:
- **Python 3.12 ou superior** (com `pip` ou `uv`)
- **Node.js 20+** (com `npm` ou `pnpm`)
- **Docker e Docker Compose** (opcional para desenvolvimento local com SQLite, obrigatório para paridade total com PostgreSQL)

---

## 2. Passo a Passo Inicial

### Passo 1: Configurar Variáveis de Ambiente
Na raiz do repositório, copie o arquivo de exemplo para criar seu `.env`:
```bash
cp .env.example .env
```
Os valores padrão já estão pré-configurados para desenvolvimento local imediato.

### Passo 2: Inicializar o Backend
Crie o ambiente virtual Python e instale as dependências:
```bash
# Na raiz do projeto:
python -m venv apps/api/.venv

# No Windows:
.\apps\api\.venv\Scripts\python.exe -m pip install -e "apps/api[dev]"

# No Linux/macOS:
./apps/api/.venv/bin/python -m pip install -e "apps/api[dev]"
```

### Passo 3: Inicializar o Frontend
```bash
cd apps/web
npm install
npm run dev
```

O frontend estará disponível em: **[http://localhost:5173](http://localhost:5173)**  
A documentação interativa Swagger da API: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 3. Subindo com Docker (Recomendado)
Se tiver o Docker instalado, você pode rodar toda a stack com um único comando:
```bash
make up
# ou: docker compose up -d
```
Isso iniciará:
- **Banco de Dados:** PostgreSQL 16 na porta `5432`
- **Backend API:** FastAPI na porta `8000`
- **Frontend SPA:** React na porta `5173`

---

## 4. Criando sua Primeira Fatia em 2 Minutos

O SoftForge possui um gerador automatizado de fatias verticais para você ou seu agente de IA:
```bash
python tools/scripts/slice_scaffold.py --name invoices
```

Esse comando cria instantaneamente:
- `apps/api/src/slices/invoices/schemas.py` (Contratos Pydantic v2)
- `apps/api/src/slices/invoices/models.py` (Tabelas do banco com SQLAlchemy 2.0 Async)
- `apps/api/src/slices/invoices/service.py` (Lógica de negócio e CRUD)
- `apps/api/src/slices/invoices/router.py` (Rotas HTTP documentadas)
- `apps/api/src/slices/invoices/tests/` (Testes automatizados com banco isolado em memória)

Para ativar a nova fatia na API:
1. Abra `apps/api/src/main.py`.
2. Adicione:
```python
from src.slices.invoices.router import router as invoices_router
app.include_router(invoices_router, prefix=settings.API_V1_STR)
```
3. Exporte a especificação atualizada e execute a verificação:
```bash
python tools/scripts/export_openapi.py
python tools/scripts/verify.py
```
Pronto! Seu novo módulo está 100% tipado, testado e documentado!
