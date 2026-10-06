# Regras de Arquitetura: Vertical Slice Architecture

## O que é uma Fatia Vertical no SoftForge?
Uma fatia vertical é uma unidade funcional autônoma que resolve um problema de negócio específico de ponta a ponta.

### Diretrizes de Isolamento:
1. **Sem acoplamento lateral desnecessário:** Uma fatia não deve importar modelos internos ou serviços privados de outra fatia. Se duas fatias precisarem se comunicar, devem fazê-lo através de:
   - Chaves estrangeiras com IDs primitivos (`workspace_id`, `user_id`).
   - Dependências públicas documentadas em `dependencies.py`.
2. **Coesão máxima:** Se você precisar alterar uma regra de faturamento, você só mexe na pasta `slices/billing/`. Nenhuma outra parte do backend ou frontend quebra.
3. **Simplicidade sobre abstração:** Prefira código direto e legível dentro da fatia a criar camadas abstratas ou padrões de design complexos antes da necessidade real.
