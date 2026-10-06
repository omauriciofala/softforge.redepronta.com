# Tema SoftForge Bootstrap Starter

Tema de referência para interfaces renderizadas em **Bootstrap 5.3 + Vanilla JavaScript**.

## Como utilizar
1. Abra `index.html` diretamente em seu navegador ou sirva via qualquer servidor estático HTTP (`npx serve .`, `python -m http.server`, Nginx, Apache).
2. O tema conecta-se à API SoftForge em `http://localhost:8000` (ou na mesma origem quando hospedado junto ao backend).
3. Demonstra a injeção em tempo real de Design Tokens Universais (`--sf-*`) mapeados diretamente para as variáveis nativas do Bootstrap (`--bs-primary`, `--bs-border-radius`, etc.).

## Estrutura
- `softforge-theme.json`: Manifesto de tokens e metadados lidos pela API SoftForge (`/api/v1/system/themes/bootstrap-starter`).
- `index.html`: Layout responsivo com navegação, tabela de temas do sistema e playground de white-labeling.
- `app.js`: Script de integração com os endpoints REST da API.
