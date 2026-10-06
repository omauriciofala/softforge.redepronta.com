# GitHub Copilot Instructions for SoftForge

> **Referência Canônica:** `.agents/skills/karpathy-guidelines/SKILL.md`  
> **Master Agent Guidelines:** `AGENTS.md`

Ao gerar código ou sugerir alterações neste repositório, o GitHub Copilot deve seguir estritamente:

1. **Princípios de Andrej Karpathy:**
   - **Think Before Coding:** Entenda os modelos de dados e schemas antes de sugerir código. Exponha trade-offs e pergunte em caso de ambiguidade.
   - **Simplicity First:** Sugira o código mínimo viável. Não adicione bibliotecas externas, camadas de abstração ou configurabilidade desnecessária.
   - **Surgical Changes:** Altere apenas as linhas e arquivos solicitados. Mantenha formatação, docstrings e comentários existentes.
   - **Goal-Driven Execution:** Sempre inclua testes de integração com SQLite in-memory em `tests/test_<feature>_slice.py` e certifique-se de que `python tools/scripts/verify.py` passe sem falhas.

2. **Arquitetura Vertical Slice:**
   - Todo endpoint e lógica de negócio fica em `apps/api/src/slices/<feature>/`.
   - NUNCA crie repositórios universais ou controladores horizontais fora da fatia.

3. **Multi-Tenancy e Segurança:**
   - Sempre isole dados por `workspace_id`.
   - Sempre proteja rotas com `require_workspace_role(...)`.
