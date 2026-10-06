# Catálogo de Temas & Multi-Frontends do SoftForge

Este diretório contém os pacotes de temas visuais e templates de frontends suportados pelo framework SoftForge.

## Filosofia Multi-Frontend
O SoftForge **não possui vendor-lock visual**. O backend fornece uma API robusta com contratos abertos OpenAPI 3.1 e **Design Tokens Universais (`--sf-*`)** em CSS.
Qualquer tecnologia de interface pode ser utilizada como tema:
- **React / Next.js / Vite**: `themes/default-react` (tema oficial padrão)
- **Bootstrap 5 / HTML5 / JS**: `themes/bootstrap-starter` (tema de referência clássico)
- **Vue 3 / Nuxt**: Suportado via `engine: "vue"`
- **PHP / Blade / Laravel / WordPress**: Suportado via `engine: "php"`
- **Svelte / SvelteKit**: Suportado via `engine: "svelte"`
- **HTMX / Go Templates / Django**: Suportado via `engine: "other"`

## Como Registrar um Novo Tema
1. Crie uma subpasta em `themes/<nome-do-tema>/`.
2. Adicione o arquivo de manifesto declarativo `softforge-theme.json` validado pelo esquema `themes/theme-schema.json`.
3. Defina os tokens de cores, tipografia e geometria.
4. A API do SoftForge (`GET /api/v1/system/themes`) detectará o novo tema automaticamente sem necessidade de rebuild.
