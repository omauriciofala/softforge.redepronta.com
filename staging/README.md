# SoftForge — Área de Staging e Quarentena para Engenharia Reversa

Este diretório (`staging/`) é a **área isolada de quarentena** para hospedar temporariamente repositórios, projetos legados ou códigos externos que serão analisados e reconstruídos no ecossistema SoftForge.

---

## 🛡️ Princípios Inegociáveis de Quarentena

1. **Zero Lixo no Repositório (Zero Git Pollution):**
   - O arquivo `.gitignore` do SoftForge ignora automaticamente qualquer pasta ou arquivo inserido aqui (`staging/*`), com exceção deste `README.md`, do template de extração e do `.gitkeep`.
   - Nenhum arquivo legado, dependência pesada (`node_modules/`, `.venv/`, `vendor/`), binário ou dado sensível deve ser comitado no Git.

2. **Extração Pura de Funcionalidade (Pure Functional Extraction):**
   - Do sistema legado, extraímos **exclusivamente**:
     - **Regras de Negócio e Algoritmos:** Lógica de cálculo, validações, transições de estado.
     - **Modelagem de Dados:** Entidades, tipos primitivos, relacionamentos e restrições.
     - **Contratos de Entrada e Saída:** Payloads de API, query params e códigos de status.
     - **Jornadas do Usuário (User Stories):** O que o usuário realiza em cada tela.

3. **Preservação Rígida do Stack e Design System do SoftForge:**
   - **Stack Backend:** O código gerado deve ser 100% SoftForge: FastAPI, SQLAlchemy 2.0 assíncrono herdando de `src.core.database.Base`, Pydantic v2 e isolamento multi-tenant por `workspace_id`. NUNCA importe bibliotecas ou padrões do backend legado (Django ORM, Prisma, TypeORM, Express, etc.).
   - **Design System Frontend:** Toda a interface deve ser desenvolvida do zero em `apps/web/src/features/<fatia>/` utilizando **exclusivamente**:
     - Componentes base do SoftForge em `apps/web/src/components/ui/` (Radix UI / Shadcn).
     - Classes utilitárias do Tailwind CSS v3 e tokens semânticos do tema (`bg-background`, `text-foreground`, `border-border`).
     - Ícones do `lucide-react`.
     - Cliente de API padronizado (`@/lib/api-client`).
   - **Proibição Absoluta de Copiar/Colar UI Externa:** NUNCA traga folhas de estilo legadas (CSS, SCSS, Less), bibliotecas de terceiros (Bootstrap, Ant Design, MUI, Materialize, Bulma) ou scripts jQuery/Vanilla legados.

---

## 📂 Organização das Frentes de Engenharia Reversa

Cada sistema a ser analisado deve residir em sua própria subpasta dentro de `staging/`:

```text
staging/
├── README.md                      # Este guia
├── TEMPLATE_EXTRACTION.md          # Modelo oficial de especificação funcional
└── <nome-do-sistema>/             # [Ignorado pelo Git]
    ├── EXTRACTION_SPEC.md         # Especificação gerada a partir do template
    └── source/                    # Código fonte do sistema legado (clone/pasta)
```

---

## 🚀 Workflow Determinístico de Migração

### Passo 1: Inicializar o Espaço de Análise
Execute a ferramenta nativa para criar a pasta do sistema e o roteiro de extração:
```bash
python tools/scripts/reverse_engineering.py init --name <nome_do_sistema>
```

### Passo 2: Copiar ou Clonar o Projeto Legado
Coloque o código do sistema original dentro de `staging/<nome_do_sistema>/source/` (ou diretamente na pasta do sistema).

### Passo 3: Mapear Regras em `EXTRACTION_SPEC.md`
Preencha a especificação (manualmente ou pedindo auxílio à IA) mapeando:
- Modelos legados -> Modelos SQLAlchemy do SoftForge
- Endpoints legados -> Schemas Pydantic e Rotas FastAPI
- Telas/Ações -> Componentes React do SoftForge

### Passo 4: Criar o Scaffold da Nova Fatia Vertical
Use o gerador oficial do SoftForge:
```bash
python tools/scripts/slice_scaffold.py --name <nome_da_fatia>
```

### Passo 5: Implementar Backend e Frontend
- Backend em `apps/api/src/slices/<nome_da_fatia>/`:
  - `models.py`: Modelos SQLAlchemy herdando de `Base` com `workspace_id`.
  - `schemas.py`: Schemas Pydantic v2 estritos.
  - `service.py`: Lógica pura assíncrona com `AsyncSession`.
  - `router.py`: Endpoints protegidos com `require_workspace_role(...)`.
  - `tests/test_<nome_da_fatia>_slice.py`: Testes de integração cobrindo os fluxos extraídos.
- Frontend em `apps/web/src/features/<nome_da_fatia>/`:
  - Views React utilizando componentes de `apps/web/src/components/ui/`.

### Passo 6: Auditar Conformidade Arquitetural
Verifique se a nova fatia respeita todos os isolamentos e não possui vazamento de código legado:
```bash
python tools/scripts/reverse_engineering.py audit --slice <nome_da_fatia>
```

### Passo 7: Exportar OpenAPI e Validar Guardrails
```bash
python tools/scripts/export_openapi.py
python tools/scripts/verify.py
```

### Passo 8: Limpeza ou Arquivamento
Quando a implementação estiver 100% concluída, testada e homologada, a pasta em `staging/<nome_do_sistema>` pode ser mantida como referência local ou removida com segurança, pois o Git jamais a indexou.
