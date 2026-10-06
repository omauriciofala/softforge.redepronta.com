import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { DOCS_DATA, type DocArticle } from "./docsData";

interface DocsViewerProps {
  onClose: () => void;
}

export const DocsViewer: React.FC<DocsViewerProps> = ({ onClose }) => {
  const [lang, setLang] = useState<"pt-br" | "en">("pt-br");
  const locale = DOCS_DATA[lang];

  // Artigo selecionado (padrão: primeiro artigo da primeira categoria)
  const [selectedArticleId, setSelectedArticleId] = useState<string>("inicio-rapido");

  // Localiza o artigo ativo
  let activeArticle: DocArticle = locale.categories[0].articles[0];
  for (const cat of locale.categories) {
    const found = cat.articles.find((a) => a.id === selectedArticleId);
    if (found) {
      activeArticle = found;
      break;
    }
  }

  // Lista linear de artigos para paginação anterior / próximo
  const allArticles = locale.categories.flatMap((c) => c.articles);
  const currentIndex = allArticles.findIndex((a) => a.id === activeArticle.id);
  const prevArticle = currentIndex > 0 ? allArticles[currentIndex - 1] : null;
  const nextArticle = currentIndex < allArticles.length - 1 ? allArticles[currentIndex + 1] : null;

  // Renderizador simplificado de Markdown (trata cabeçalhos, código e listas)
  const renderContent = (rawText: string) => {
    const lines = rawText.trim().split("\n");
    const elements: React.ReactNode[] = [];
    let inCodeBlock = false;
    let codeBuffer: string[] = [];
    let codeLang = "";

    lines.forEach((line, index) => {
      if (line.startsWith("```")) {
        if (inCodeBlock) {
          elements.push(
            <div key={`code-${index}`} className="relative my-4">
              {codeLang && (
                <span className="absolute top-2 right-2 text-[10px] font-mono uppercase text-zinc-400 bg-zinc-800 px-1.5 py-0.5 rounded">
                  {codeLang}
                </span>
              )}
              <pre className="overflow-x-auto rounded-lg bg-zinc-950 p-4 text-xs font-mono text-zinc-100 border border-zinc-800">
                <code>{codeBuffer.join("\n")}</code>
              </pre>
            </div>
          );
          codeBuffer = [];
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
          codeLang = line.replace("```", "").trim();
        }
        return;
      }

      if (inCodeBlock) {
        codeBuffer.push(line);
        return;
      }

      if (line.startsWith("### ")) {
        elements.push(
          <h3 key={index} className="text-lg font-bold text-foreground mt-6 mb-2">
            {line.replace("### ", "")}
          </h3>
        );
      } else if (line.startsWith("## ")) {
        elements.push(
          <h2 key={index} className="text-xl font-bold text-foreground mt-8 mb-3 border-b pb-2">
            {line.replace("## ", "")}
          </h2>
        );
      } else if (line.startsWith("- ")) {
        elements.push(
          <li key={index} className="ml-5 list-disc text-sm text-muted-foreground my-1">
            {line.replace("- ", "")}
          </li>
        );
      } else if (/^\d+\.\s/.test(line)) {
        elements.push(
          <li key={index} className="ml-5 list-decimal text-sm text-muted-foreground my-1 font-medium">
            {line.replace(/^\d+\.\s/, "")}
          </li>
        );
      } else if (line.startsWith("---")) {
        elements.push(<hr key={index} className="my-6 border-border" />);
      } else if (line.trim().length > 0) {
        elements.push(
          <p key={index} className="text-sm text-muted-foreground leading-relaxed my-2">
            {line}
          </p>
        );
      }
    });

    return elements;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Navbar */}
      <header className="border-b bg-card px-6 py-3 sticky top-0 z-30 shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span className="font-extrabold text-xl tracking-tight text-primary flex items-center gap-1.5">
            <span>⚡</span> SoftForge
          </span>
          <span className="text-muted-foreground">/</span>
          <Badge variant="outline" className="font-mono text-xs">
            Docs & Manual
          </Badge>
        </div>

        <div className="flex items-center space-x-3">
          {/* Seletor de Idioma */}
          <div className="flex items-center rounded-lg border bg-muted/40 p-0.5 text-xs font-medium">
            <button
              onClick={() => setLang("pt-br")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                lang === "pt-br"
                  ? "bg-background text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              🇧🇷 PT-BR
            </button>
            <button
              onClick={() => setLang("en")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                lang === "en"
                  ? "bg-background text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              🇺🇸 EN
            </button>
          </div>

          <Button variant="default" size="sm" onClick={onClose}>
            {locale.backToApp}
          </Button>
        </div>
      </header>

      {/* Main Layout with Sidebar */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Left Sidebar */}
        <aside className="w-72 border-r p-6 space-y-6 hidden md:block shrink-0">
          <div className="font-bold text-sm tracking-wider uppercase text-muted-foreground">
            {locale.navTitle}
          </div>

          <nav className="space-y-6">
            {locale.categories.map((category) => (
              <div key={category.name} className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground/80 px-2">
                  {category.name}
                </h4>
                <div className="space-y-1">
                  {category.articles.map((article) => {
                    const isActive = article.id === activeArticle.id;
                    return (
                      <button
                        key={article.id}
                        onClick={() => setSelectedArticleId(article.id)}
                        className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex items-center justify-between ${
                          isActive
                            ? "bg-primary/10 text-primary font-medium border border-primary/20"
                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                        }`}
                      >
                        <span>{article.title}</span>
                        {isActive && <span className="h-1.5 w-1.5 rounded-full bg-primary" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </nav>
        </aside>

        {/* Article Content Viewer */}
        <main className="flex-1 p-6 md:p-10 max-w-4xl space-y-6">
          <div className="space-y-2">
            <Badge variant="secondary" className="text-xs">
              {activeArticle.category}
            </Badge>
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
              {activeArticle.title}
            </h1>
            <p className="text-base text-muted-foreground">{activeArticle.summary}</p>
          </div>

          <hr className="border-border" />

          {/* Article Body */}
          <Card className="p-6 bg-card/60 border-border">
            <div className="prose prose-zinc dark:prose-invert max-w-none">
              {renderContent(activeArticle.content)}
            </div>
          </Card>

          {/* Pagination Footer */}
          <div className="flex items-center justify-between pt-6 border-t">
            {prevArticle ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedArticleId(prevArticle.id)}
              >
                ← {prevArticle.title}
              </Button>
            ) : (
              <div />
            )}

            {nextArticle && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedArticleId(nextArticle.id)}
              >
                {nextArticle.title} →
              </Button>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};
