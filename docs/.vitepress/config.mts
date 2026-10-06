import { defineConfig } from "vitepress";

export default defineConfig({
  title: "SoftForge",
  description: "AI-Native Fullstack Framework",
  base: "/",
  outDir: "./dist",
  ignoreDeadLinks: true,
  themeConfig: {
    // Busca 100% local e offline (Minisearch embutido no cliente, sem requisições externas)
    search: {
      provider: "local",
    },
    socialLinks: [
      {
        icon: "github",
        link: "https://github.com/omauriciofala/softforge.redepronta.com",
      },
    ],
  },
  locales: {
    root: {
      label: "Português",
      lang: "pt-BR",
      themeConfig: {
        nav: [
          { text: "Início Rápido", link: "/pt-br/01-inicio-rapido" },
          { text: "Manual", link: "/pt-br/02-manual-do-framework" },
          { text: "Stack Tecnológica", link: "/pt-br/06-stack-tecnologica" },
          { text: "Fluxo com IA", link: "/pt-br/03-fluxo-de-desenvolvimento-com-ia" },
        ],
        sidebar: [
          {
            text: "Primeiros Passos",
            items: [
              { text: "Guia de Início Rápido", link: "/pt-br/01-inicio-rapido" },
              { text: "Stack Tecnológica Oficial", link: "/pt-br/06-stack-tecnologica" },
              { text: "FAQ & Solução de Problemas", link: "/pt-br/05-faq-e-troubleshooting" },
            ],
          },
          {
            text: "Arquitetura & Fatias",
            items: [
              { text: "Manual do Framework", link: "/pt-br/02-manual-do-framework" },
              { text: "Fatia: Auth & Social OAuth2", link: "/pt-br/08-autenticacao-social-oauth2" },
              { text: "Fatia: Billing & Mercado Pago", link: "/pt-br/07-fatia-billing-mercado-pago" },
              { text: "Fatia: Auditoria & Compliance", link: "/pt-br/10-fatia-auditoria-compliance" },
              { text: "Fatia: Notificações & WebSockets", link: "/pt-br/11-fatia-notificacoes-inapp-websocket" },
              { text: "Fatia: Webhooks Outbound", link: "/pt-br/12-fatia-webhooks-outbound" },
              { text: "Fatia: Chaves de API & PAT (M2M)", link: "/pt-br/13-fatia-api-keys-pat" },
              { text: "Fatia: Convites & Membros (RBAC)", link: "/pt-br/14-fatia-convites-e-membros-rbac" },
              { text: "Fatia: Storage & Arquivos", link: "/pt-br/15-fatia-storage-e-arquivos" },
              { text: "Fatia: Rate Limiting & Proteção", link: "/pt-br/16-rate-limiting-e-protecao-contra-abuso" },
              { text: "Fatia: Feature Flags & Toggles", link: "/pt-br/17-fatia-feature-flags-e-toggles" },
              { text: "Internacionalização (i18n)", link: "/pt-br/18-internacionalizacao-i18n" },
              { text: "Sistema de Temas & Multi-Frontends", link: "/pt-br/19-sistema-de-temas-e-multi-frontends" },
              { text: "Interface & Dashboard Frontend", link: "/pt-br/20-interface-dashboard-frontend" },
              { text: "Fila Assíncrona & Workers (Arq)", link: "/pt-br/09-background-workers-arq" },
              { text: "Fluxo com IA (AGENTS.md)", link: "/pt-br/03-fluxo-de-desenvolvimento-com-ia" },
              { text: "Contratos & OpenAPI 3.1", link: "/pt-br/04-contratos-e-openapi" },
            ],
          },
        ],
      },
    },
    en: {
      label: "English",
      lang: "en-US",
      link: "/en/",
      themeConfig: {
        nav: [
          { text: "Getting Started", link: "/en/01-getting-started" },
          { text: "Manual", link: "/en/02-framework-manual" },
          { text: "Tech Stack", link: "/en/06-tech-stack" },
          { text: "AI Workflow", link: "/en/03-ai-development-workflow" },
        ],
        sidebar: [
          {
            text: "Getting Started",
            items: [
              { text: "Quickstart Guide", link: "/en/01-getting-started" },
              { text: "Official Tech Stack", link: "/en/06-tech-stack" },
              { text: "FAQ & Troubleshooting", link: "/en/05-faq-and-troubleshooting" },
            ],
          },
          {
            text: "Architecture & Slices",
            items: [
              { text: "Framework Manual", link: "/en/02-framework-manual" },
              { text: "Slice: Auth & Social OAuth2", link: "/en/08-social-auth-oauth2" },
              { text: "Slice: Billing & Mercado Pago", link: "/en/07-billing-and-payments" },
              { text: "Slice: Audit & Compliance", link: "/en/10-audit-and-compliance" },
              { text: "Slice: Notifications & WebSockets", link: "/en/11-inapp-notifications-websocket" },
              { text: "Slice: Outbound Webhooks", link: "/en/12-outbound-webhooks" },
              { text: "Slice: API Keys & PAT (M2M)", link: "/en/13-api-keys-pat" },
              { text: "Slice: Team Invites & RBAC", link: "/en/14-team-invites-and-rbac" },
              { text: "Slice: Storage & File Management", link: "/en/15-storage-and-file-management" },
              { text: "Slice: Rate Limiting & Protection", link: "/en/16-rate-limiting-and-abuse-protection" },
              { text: "Slice: Feature Flags & Toggles", link: "/en/17-feature-flags-and-tenant-toggles" },
              { text: "Internationalization (i18n)", link: "/en/18-internationalization-i18n" },
              { text: "Themes & Multi-Frontends", link: "/en/19-theme-system-and-multi-frontends" },
              { text: "Frontend Dashboard & UI", link: "/en/20-frontend-dashboard-interface" },
              { text: "Async Queue & Workers (Arq)", link: "/en/09-background-workers-arq" },
              { text: "AI Development Workflow", link: "/en/03-ai-development-workflow" },
              { text: "Contracts & OpenAPI 3.1", link: "/en/04-contracts-and-openapi" },
            ],
          },
        ],
      },
    },
  },
});
