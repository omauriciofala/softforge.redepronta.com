# Regra de Ouro: Documentação Contínua para IA (Documentation-First)

> **"Se não está documentado no ecossistema, para a IA não existe."**

---

## 1. O Princípio Vital

O SoftForge é um framework **AI-Native**, o que significa que ele foi construído tanto para humanos quanto para Agentes Autônomos de IA (Cursor, Antigravity, Claude Code, Copilot, etc.) operarem, evoluírem e criarem sistemas complexos sobre sua base.

Agentes de IA não possuem memória mística sobre decisões passadas: **eles leem a documentação, os esquemas e o código em tempo real**. Se você implementar um comportamento ou mudar uma regra arquitetural e não documentá-la imediatamente, o próximo agente de IA irá alucinar, refazer o padrão incorretamente ou quebrar convenções.

---

## 2. As Regras Inegociáveis

1. **Documentação Evolui com o Código:**
   - Toda alteração arquitetural, novo slice ou nova ferramenta DEVE ser documentada no mesmo commit/tarefa em que o código foi escrito.
   - Jamais considere uma funcionalidade como "concluída" se a documentação não foi atualizada.

2. **Locais Obrigatórios de Atualização:**
   - **Para Agentes de IA:**
     - `.ai/AGENTS.md`: Quando novas convenções mestras forem criadas.
     - `.ai/rules/`: Regras especializadas (fatias verticais, contratos, documentação).
     - `contracts/openapi.json`: Atualizado via `python tools/scripts/export_openapi.py`.
   - **Para Humanos e Manuais Offline:**
     - `docs/pt-br/` e `docs/en/`: Guias temáticos em Markdown.
     - `docs/manual-offline.html`: Quando houver novos princípios de design ou arquitetura.

3. **Como Documentar uma Nova Fatia (`slice`):**
   - Registre a finalidade da fatia e seus endpoints no arquivo de contratos.
   - Descreva os esquemas de entrada e saída com `Field(description="...")`. O Swagger e o OpenAPI devem ser autoexplicativos.
   - Adicione exemplos práticos no manual do framework.

4. **Regra de Build da Documentação:**
   - Ao alterar os arquivos em `docs/`, recompile os arquivos estáticos:
     ```bash
     cd docs && npx vitepress build
     ```
   - Isso garante que a visualização offline (`docs/dist`) e os scripts de inicialização (`docs.bat` e `docs.ps1`) permaneçam sincronizados com a versão mais recente.
