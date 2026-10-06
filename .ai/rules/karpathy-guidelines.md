# Regra de Engenharia: Princípios de Andrej Karpathy para IA

> **Referência Canônica:** `.agents/skills/karpathy-guidelines/SKILL.md`  
> Esta regra é de observância obrigatória para qualquer modelo de linguagem (LLM) ou agente autônomo operando neste repositório.

---

## Os 4 Princípios Fundamentais

### 1. Pense Antes de Codificar (Think Before Coding)
- **Inspecione o contexto:** Nunca gere código sem antes ler os arquivos de referência, modelos de dados e schemas relacionados.
- **Exponha Trade-offs:** Se houver ambiguidades arquiteturais (ex: síncrono vs fila, banco vs cache), apresente as opções com prós e contras antes de implementar.
- **Defenda a Arquitetura:** Rejeite soluções que violem o isolamento das fatias verticais, quebrem a multi-tenancy (`workspace_id`) ou adicionem dependências pesadas e desnecessárias.
- **Pergunte quando houver dúvida:** Nunca adivinhe requisitos de negócio.

### 2. Simplicidade em Primeiro Lugar (Simplicity First)
- **Código mínimo viável:** Escreva a menor quantidade de código necessária para resolver o problema de forma robusta e completa.
- **Zero abstrações especulativas:** Não crie repositórios genéricos, fábricas abstratas ou camadas intermediárias "para o futuro".
- **Sem configurabilidade desnecessária:** Resolva o caso concreto hoje. Não invente dezenas de variáveis de ambiente sem necessidade.

### 3. Modificações Cirúrgicas (Surgical Changes)
- **Escopo milimétrico:** Altere estritamente as linhas e arquivos necessários para a tarefa.
- **Preserve código alheio:** NUNCA reformate arquivos não relacionados ou reordene imports fora do seu escopo de trabalho.
- **Integridade da documentação:** Conserve todos os comentários, docstrings e explicações existentes.
- **Limpe seu próprio rastro:** Remova prints, scripts temporários e dados de teste antes de finalizar a resposta.

### 4. Execução Orientada a Metas e Verificação (Goal-Driven Execution)
- **Defina critérios de sucesso antes de codificar:** Saiba exatamente qual teste ou comando comprovará o sucesso da entrega.
- **Testes automatizados contínuos:** Todo novo slice ou alteração crítica deve possuir testes de integração com SQLite in-memory.
- **Portão de Qualidade:** Execute e garanta 100% de sucesso no script mestre antes de responder ao usuário:
  ```bash
  python tools/scripts/verify.py
  ```
- **Evidência concreta:** Nunca declare vitória sem apresentar os resultados reais dos testes executados.
