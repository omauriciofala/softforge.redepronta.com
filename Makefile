.PHONY: help up down restart logs build migrate export-spec codegen test-api test-web test lint typecheck verify scaffold docs

help: ## Exibe a lista de comandos disponíveis
	@echo "SoftForge — AI-Native Framework"
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

up: ## Sobe todos os serviços em segundo plano (Postgres, API, Web)
	docker compose up -d

down: ## Derruba todos os containers
	docker compose down

restart: down up ## Reinicia todos os serviços

logs: ## Exibe logs dos containers em tempo real
	docker compose logs -f

build: ## Reconstrói as imagens Docker
	docker compose build

migrate: ## Executa as migrações do Alembic no backend
	docker compose exec api alembic upgrade head

export-spec: ## Exporta openapi.json a frio da API
	docker compose exec api python -m tools.scripts.export_openapi

codegen: export-spec ## Gera hooks e tipos no frontend a partir do openapi.json
	cd apps/web && npm run codegen

test-api: ## Roda os testes unitários e de integração do backend
	docker compose exec api pytest -v

test-web: ## Roda os testes do frontend
	cd apps/web && npm test

test: test-api test-web ## Roda todos os testes (backend e frontend)

lint-api: ## Executa checagem de linter e formatação com Ruff
	docker compose exec api ruff check .

lint-web: ## Executa ESLint no frontend
	cd apps/web && npm run lint

lint: lint-api lint-web ## Executa todos os linters

typecheck-api: ## Validação estática de tipos com mypy no backend
	docker compose exec api mypy src

typecheck-web: ## Validação estática de tipos com tsc no frontend
	cd apps/web && npm run typecheck

typecheck: typecheck-api typecheck-web ## Executa todas as checagens de tipos

verify: lint typecheck test ## Pipeline unificado de guardrails para Agentes de IA

scaffold: ## Cria uma nova fatia vertical (ex: make scaffold name=invoices)
	python tools/scripts/slice_scaffold.py --name $(name)

docs: ## Inicia o servidor de documentação offline VitePress na porta 5174
	cd docs && npx vitepress dev --port 5174
