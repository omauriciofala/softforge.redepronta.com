# Regra de Engenharia: Política de Versionamento & Releases (SemVer)

> **Referência Canônica:** `CHANGELOG.md` e `docs/pt-br/21-politica-de-versionamento-e-releases.md`  
> Esta diretriz define como versões, quebras de compatibilidade e deploys são geridos no SoftForge.

---

## 1. Modelo SemVer Híbrido

O SoftForge adota o **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH`) em conjunto com um modelo contínuo no branch `main`:

- **Branch `main` (Rolling Release Contínuo):** O código no branch `main` é sempre deployável, passa 100% pelos guardrails do `verify.py` e serve como base imediata para scaffolds e forks.
- **Tags & Releases Formais (`vX.Y.Z`):** Marcos estáveis publicados no GitHub Releases acompanhados de notas detalhadas no `CHANGELOG.md`.

---

## 2. Escopo Global Unificado (Monorepo)

O SoftForge não fragmenta versões por pacote. O Backend (`apps/api`), o Frontend (`apps/web`), o Catálogo de Temas (`themes/`), o Scaffolder de IA e os Manuais compartilham exatamente o mesmo número de versão global (ex: `v1.0.0`).

---

## 3. Critérios de Incremento

| Incremento | Quando Aplicar | Exemplos no SoftForge |
| :--- | :--- | :--- |
| **`MAJOR` (Quebra de Contrato)** | Mudanças incompatíveis na API pública, banco de dados ou convenções do framework. | Alterações destrutivas no banco sem retrocompatibilidade; remoção de rotas/schemas da OpenAPI; reformulação estrutural do core. |
| **`MINOR` (Novo Recurso)** | Funcionalidades adicionadas de forma retrocompatível. | Novas fatias verticais (`apps/api/src/slices/`); novos temas no catálogo; novos endpoints; adições não obrigatórias em schemas. |
| **`PATCH` (Correções)** | Correções de bugs e manutenção sem alteração de contratos. | Correção de lógica em services; ajustes de segurança em dependências; melhorias em documentação e testes. |

---

## 4. Política de Breaking Changes

- **Transição Direta em MAJOR:** Mudanças com quebra de contrato podem ser lançadas diretamente na próxima versão `MAJOR`.
- **Requisitos Obrigatórios para Breaking Changes:**
  1. Migração Alembic reversível fornecida em `apps/api/alembic/versions/`.
  2. Guia de migração passo a passo documentado na seção da versão no `CHANGELOG.md`.
  3. Contratos OpenAPI atualizados via `export_openapi.py`.

---

## 5. Ferramenta de Release Automatizada

Toda release deve ser executada obrigatoriamente através do script:
```bash
python tools/scripts/release.py --bump [major|minor|patch] --tag -m "Descrição da Release"
```
O script executa `verify.py` como pré-requisito inegociável antes de comitar ou gerar tags.
