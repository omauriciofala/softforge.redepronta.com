# Regras de Engenharia Reversa e Migração Segura (Zero Contaminação)

## Visão Geral
Ao analisar sistemas externos ou repositórios legados para incorporar funcionalidades ao SoftForge, os agentes de IA e desenvolvedores DEVEM seguir rigorosamente estas diretrizes de quarentena, integridade de stack e preservação do design system.

---

## 1. Quarentena e Isolamento de Código Legado (Zero Lixo)
1. **Pasta Exclusiva de Quarentena (`staging/`):**
   - Todo repositório externo, dump de banco, payload de exemplo ou código legado DEVE residir em `staging/<nome-do-sistema>/`.
   - NUNCA copie pastas de projetos externos diretamente para dentro de `apps/api/`, `apps/web/` ou `tools/`.
2. **Proteção Total do Git:**
   - O `.gitignore` protege a pasta `staging/*`. NUNCA use `git add -f` para forçar o commit de arquivos legados, dependências (`node_modules/`, `venv/`, `vendor/`) ou credenciais expostas no código de origem.
3. **Uso do Roteiro de Extração:**
   - Toda análise deve iniciar com `python tools/scripts/reverse_engineering.py init --name <sistema>` e ter o `EXTRACTION_SPEC.md` preenchido antes da codificação.

---

## 2. Princípio da Extração Pura de Funcionalidade
O objetivo da engenharia reversa **NÃO É PORTAR CÓDIGO**, mas sim **RECONSTRUIR CAPACIDADES DE NEGÓCIO**.

### O que EXTRAIR do sistema original:
- Requisitos funcionais e jornadas do usuário (User Stories).
- Entidades, campos, tipos primitivos e restrições de integridade.
- Regras de cálculo, fluxos de validação e transições de estado.
- Payloads de entrada e saída esperados pelos clientes.

### O que NUNCA trazer do sistema original:
- Código-fonte copiado/colado de frameworks diferentes (Django, Flask, Express, Spring, Laravel, etc.).
- Bibliotecas ORM antigas ou drivers de banco estranhos ao SQLAlchemy 2.0.
- Tratamentos de erro ad-hoc ou prints de depuração.

---

## 3. Preservação Rígida do Design System e da UI
1. **Zero Distorção Visual:**
   - A interface do usuário DEVE manter 100% da identidade visual e coerência do SoftForge.
   - NUNCA copie folhas de estilo legadas (`.css`, `.scss`, `.less`), classes inline ou bibliotecas de terceiros (Bootstrap, Ant Design, MUI, Materialize, Bulma, jQuery).
2. **Componentização Oficial:**
   - Toda nova tela em `apps/web/src/features/<fatia>/` deve ser montada exclusivamente com:
     - Componentes base de `@/components/ui/` (`Card`, `Button`, `Badge`, `Dialog`, `Input`, `Table`, etc.).
     - Classes utilitárias do Tailwind CSS e tokens do tema ativo (`bg-background`, `text-foreground`, `border-border`).
     - Ícones do `lucide-react`.
     - Cliente HTTP oficial (`@/lib/api-client`).

---

## 4. Invariantes Backend Obrigatórios
1. **Vertical Slice Architecture:** Todo o código do domínio pertence a `apps/api/src/slices/<nome_da_fatia>/`.
2. **Contratos Pydantic v2:** Declare modelos de entrada e saída com tipos estritos em `schemas.py`.
3. **Modelos SQLAlchemy 2.0:** Todas as tabelas devem herdar de `src.core.database.Base` e incluir a coluna `workspace_id` para multi-tenancy.
4. **Service Assíncrono:** Todas as operações de banco devem ser assíncronas recebendo `session: AsyncSession`.
5. **Erros Padronizados:** Use as exceções de `src.core.errors` (`NotFoundException`, `AppException`, etc.).

---

## 5. Verificação e Auditoria
Antes de declarar a migração de qualquer funcionalidade concluída:
1. Execute a auditoria de conformidade:
   ```bash
   python tools/scripts/reverse_engineering.py audit --slice <nome_da_fatia>
   ```
2. Exporte a especificação OpenAPI:
   ```bash
   python tools/scripts/export_openapi.py
   ```
3. Execute o pipeline unificado de guardrails:
   ```bash
   python tools/scripts/verify.py
   ```
