# SoftForge (softforge.redepronta.com)

> **Framework Fullstack AI-Native & Monorepo Starter**  
> *100% construído com e para IA • Spec-Driven • Vertical Slice Architecture • Docker-First*

---

## 🚀 Sobre o SoftForge

O **SoftForge** foi concebido do zero para permitir que desenvolvedores e **Agentes Autônomos de Inteligência Artificial** construam, testem e mantenham aplicações fullstack robustas com máxima precisão e zero atrito de contexto.

### Pilares Fundamentais:
- **Vertical Slice Architecture:** Cada funcionalidade (domínio) agrupa seus contratos (Pydantic / OpenAPI), modelos de banco (SQLAlchemy Async), regras de negócio, rotas e testes em uma única fatia coesa.
- **OpenAPI 3.1 como Fonte Única da Verdade:** O backend expõe contratos tipados estritos. O frontend gera hooks TanStack Query e tipos TypeScript automaticamente via Orval.
- **Guardrails Determinísticos para IA:** O diretório `.ai/` fornece o arquivo `AGENTS.md` e regras arquiteturais para orientar LLMs, além de comandos unificados de verificação (`make verify`).
- **Docker-First & DevContainers:** Sem problemas de "na minha máquina funciona". Todo o ambiente roda em paridade total via Docker Compose.

---

## 🧱 Estrutura do Repositório

```text
├── .ai/                    # Regras, convenções e instruções para Agentes de IA
├── .devcontainer/          # Ambiente padronizado de desenvolvimento
├── apps/
│   ├── api/                # Backend FastAPI + SQLAlchemy 2.0 Async + Alembic
│   └── web/                # Frontend Vite + React + Tailwind + shadcn/ui + Orval
├── tools/                  # Scripts de scaffolding e exportação de contratos
├── docker-compose.yml      # Orquestração local (PostgreSQL, API, Web)
└── Makefile                # Atalhos operacionais
```

---

## ⚡ Início Rápido

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose instalados.
- Make (opcional, mas recomendado).

### 1. Clonar e Iniciar Serviços
```bash
# Copie o arquivo de variáveis de ambiente
cp .env.example .env

# Suba os containers do banco, API e frontend
make up
# ou: docker compose up -d
```

- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **API Swagger / OpenAPI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI JSON Spec:** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

### 2. Guardrails e Verificação de Qualidade
Para rodar a bateria de testes, linters e checagem de tipos:
```bash
make verify
```

### 3. Criar uma Nova Fatia Vertical
```bash
make scaffold name=invoices
```
Isso gerará a estrutura da fatia tanto no backend (`apps/api/src/slices/invoices`) quanto o template correspondente no frontend.

### 4. Documentação Offline (VitePress)
Para iniciar a documentação local offline com busca embutida:
```bash
make docs
# ou: cd docs && npx vitepress dev --port 5174
```
Acesse em: **[http://localhost:5174](http://localhost:5174)**

---

## 📜 Licença Open Source
Este projeto é software livre e de código aberto sob a licença [MIT](LICENSE).
Repositório Oficial: **[https://github.com/omauriciofala/softforge.redepronta.com](https://github.com/omauriciofala/softforge.redepronta.com)**
