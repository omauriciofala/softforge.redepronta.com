# FAQ & Solução de Problemas (Troubleshooting)

> **Perguntas Frequentes, Dicas de Depuração e Resolução de Erros**

---

## 1. Perguntas Frequentes (FAQ)

### Posso usar o SoftForge sem Docker?
**Sim.** Durante o desenvolvimento e criação de protótipos, você pode rodar a API usando o ambiente virtual Python (`.venv`) e o frontend com `npm run dev`. Os testes automatizados utilizam SQLite in-memory, o que dispensa qualquer banco externo.

### Como funciona a autenticação de dois níveis (Cookie + Bearer)?
O SoftForge aceita tokens JWT tanto via cabeçalho `Authorization: Bearer <token>` quanto via cookie `HttpOnly` com nome `access_token`. Isso garante máxima segurança no navegador contra ataques XSS e total compatibilidade com clientes de API externos, apps mobile e ferramentas como Postman.

### O que acontece se duas fatias precisarem compartilhar dados?
Fatias verticais não devem importar modelos privados umas das outras. Elas compartilham chaves primitivas (como `workspace_id: uuid.UUID` ou `user_id: uuid.UUID`). Se houver regras de negócio complexas compartilhadas, a lógica vive em um serviço compartilhado em `src/core/`.

### Regra de Ouro: Por que toda funcionalidade deve ser rigorosamente documentada?
O SoftForge é operado tanto por humanos quanto por **Agentes Autônomos de IA** (Cursor, Antigravity, Claude Code, Copilot). 
Modelos de IA operam lendo o código e a documentação viva em tempo real. **Se uma funcionalidade ou regra não estiver documentada, para a IA ela simplesmente não existe.** Isso gera alucinações, reescritas desnecessárias e quebras de contratos. Portanto, no SoftForge, a documentação evolui obrigatoriamente junto com o código a cada entrega.

---

## 2. Solução de Problemas Comuns

### Por que abrir `docs/dist/index.html` diretamente no navegador (`file:///`) abre sem estilos (layout quebrado)?
- **Causa:** O VitePress (e outros SSGs modernos como Next e Vite) compila o CSS e JS com caminhos absolutos (ex: `/assets/style.css`). Quando você dá dois cliques no arquivo no Windows Explorer pelo protocolo `file:///`:
  1. A barra inicial `/` aponta para a raiz do disco rígido (`V:\assets\...`), resultando em erro 404 para os arquivos de estilo.
  2. Os navegadores modernos (Edge, Chrome, Brave) bloqueiam módulos JavaScript (`<script type="module">`) em páginas locais por políticas de segurança (CORS).
- **Como resolver:**
  1. **Opção Recomendada (VitePress completo com busca e tema):** Dê um duplo clique no arquivo `docs.bat` na raiz do projeto (ou execute `.\docs.ps1` no PowerShell). Ele serve os arquivos estáticos e abre em `http://localhost:5174`.
  2. **Opção Sem Servidor (Zero Dependências):** Abra diretamente o arquivo `docs/manual-offline.html` com dois cliques. Ele foi compilado com CSS 100% inlined e funciona nativamente no protocolo `file:///`.

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
