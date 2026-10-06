# SoftForge Backend (FastAPI + Vertical Slice Architecture)

## Princípios da Arquitetura
1. **Vertical Slice:** Todas as funcionalidades de negócio ficam em `src/slices/<feature>/`. Cada pasta contém:
   - `schemas.py`: Modelos Pydantic v2 (contratos OpenAPI de entrada/saída).
   - `models.py`: Entidades ORM SQLAlchemy 2.0 (tabelas do banco).
   - `service.py`: Lógica pura de negócio.
   - `router.py`: Endpoints HTTP FastAPI.
   - `tests/`: Testes automatizados da fatia.
2. **Core Reutilizável:** Apenas utilitários transversais (conexão com banco, JWT, logging e middlewares) residem em `src/core/`.
3. **Observabilidade:** Logging estruturado via Loguru com injeção de `request_id`.
