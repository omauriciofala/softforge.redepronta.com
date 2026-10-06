# FAQ & Solução de Problemas (Troubleshooting)

> **Perguntas Frequentes, Dicas de Depuração e Resolução de Erros**

---

## 1. Perguntas Frequentes (FAQ)

### Posso usar o SoftForge sem Docker?
**Sim.** Durante o desenvolvimento e criação de protótipos, você pode rodar a API usando o ambiente virtual Python (`.venv`) e o frontend com `npm run dev`. Os testes automatizados utilizam SQLite in-memory, o que dispensa qualquer banco externo.

### Como funciona a autenticação de dois níveis (Cookie + Bearer)?
O SoftForge aceita tokens JWT tanto via cabeçalho `Authorization: Bearer <token>` quanto via cookie `HttpOnly` com nome `access_token`. Isso garante máxima segurança no navegador contra ataques XSS e total compatibilidade com clientes de API externos, apps mobile e ferramentas como Postman.

### O que acontece se duas fatias precisarem compartilhar dados?
Fatias verticais não devem importar modelos privados umas das outras. Elas compartilham chaves primitivas (como `workspace_id: uuid.UUID` ou `user_id: uuid.UUID`). Se houver regras de negócio muito complexas compartilhadas, coloque a lógica em um serviço comum em `src/core/`.

---

## 2. Solução de Problemas Comuns

### Erro: `ModuleNotFoundError: No module named 'greenlet'`
- **Causa:** O SQLAlchemy 2.0 assíncrono requer a biblioteca `greenlet`.
- **Solução:** Execute `pip install "greenlet>=3.0.0"` no seu ambiente virtual.

### Erro: `Port 8000 or 5173 already in use`
- **Causa:** Outro processo está ocupando as portas padrão da API ou do Vite.
- **Solução:** Altere a porta em `.env` (`API_PORT=8001`) ou finalize o processo anterior.

### Como resetar o banco de dados local no Docker?
Execute:
```bash
docker compose down -v
docker compose up -d
```
Isso destruirá o volume `pgdata` e criará uma base limpa.
