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
