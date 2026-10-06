import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useTheme } from "@/core/theme";
import { Check, CheckCircle2, Code2, Palette } from "lucide-react";

const COLOR_PRESETS = [
  { name: "Blue (Oficial)", color: "#2563eb" },
  { name: "Indigo", color: "#4f46e5" },
  { name: "Emerald", color: "#10b981" },
  { name: "Violet", color: "#7c3aed" },
  { name: "Rose", color: "#f43f5e" },
  { name: "Orange", color: "#ea580c" },
];

export const ThemesView: React.FC = () => {
  const { activeTheme, systemThemes, updateTheme } = useTheme();

  const [selectedSlug, setSelectedSlug] = useState(activeTheme?.theme_slug || "default-react");
  const [primaryColor, setPrimaryColor] = useState(
    activeTheme?.custom_primary_color ||
      activeTheme?.css_variables["--sf-color-primary"] ||
      "#2563eb"
  );
  const [logoUrl, setLogoUrl] = useState(activeTheme?.custom_logo_url || "");
  const [customCss, setCustomCss] = useState(activeTheme?.custom_css || "");
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSaveTheme = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSavedSuccess(false);
    try {
      await updateTheme({
        theme_slug: selectedSlug,
        custom_primary_color: primaryColor,
        custom_logo_url: logoUrl || null,
        custom_css: customCss || null,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      console.error("Erro ao salvar personalização do tema:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSwitchThemeSlug = (slug: string) => {
    setSelectedSlug(slug);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Palette className="h-6 w-6 text-primary" />
          Temas & White-Labeling Agnóstico
        </h2>
        <p className="text-sm text-muted-foreground">
          Conecte múltiplos motores visuais (React, Bootstrap 5, Vue, PHP) e personalize cores, logo e estilos por tenant.
        </p>
      </div>

      {savedSuccess && (
        <div className="bg-green-500/10 border border-green-500/30 text-green-700 dark:text-green-300 p-3 rounded-lg text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-green-500" />
          <span>Configurações visuais salvas e propagadas dinamicamente para os Design Tokens do tenant!</span>
        </div>
      )}

      {/* Catálogo de Temas Instalados */}
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Motores & Temas Disponíveis no Sistema ({systemThemes.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {systemThemes.map((theme) => {
            const isSelected = selectedSlug === theme.slug;
            return (
              <Card
                key={theme.slug}
                onClick={() => handleSwitchThemeSlug(theme.slug)}
                className={`cursor-pointer transition-all hover:border-primary/60 ${
                  isSelected ? "border-primary ring-1 ring-primary bg-primary/5 shadow-sm" : ""
                }`}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        {theme.name}
                        {isSelected && <Badge className="bg-primary text-[10px]">Ativo</Badge>}
                      </CardTitle>
                      <CardDescription className="text-xs mt-1">
                        <code>{theme.slug}</code> • v{theme.version}
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="font-mono text-[10px] uppercase">
                      {theme.engine}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2 text-xs text-muted-foreground">
                  <p>{theme.description || "Sem descrição informada no manifesto."}</p>
                  <div className="flex items-center gap-2 text-[11px] pt-1">
                    <span>Autor: {theme.author || "SoftForge Community"}</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Customização de White-Labeling */}
      <Card className="border-border">
        <CardHeader>
          <CardTitle className="text-lg">Customização de Identidade Visual (Tenant)</CardTitle>
          <CardDescription className="text-xs">
            Ajuste a cor primária e a marca. Os Design Tokens Universais (<code>--sf-*</code>) serão atualizados em tempo real.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveTheme} className="space-y-6">
            {/* Seletor de Cores */}
            <div className="space-y-3">
              <label className="text-xs font-semibold uppercase text-muted-foreground block">
                Cor Primária do Tenant
              </label>
              <div className="flex flex-wrap items-center gap-3">
                {COLOR_PRESETS.map((p) => (
                  <button
                    key={p.color}
                    type="button"
                    onClick={() => setPrimaryColor(p.color)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-transform hover:scale-105"
                    style={{ borderColor: p.color }}
                  >
                    <span
                      className="w-3.5 h-3.5 rounded-full"
                      style={{ backgroundColor: p.color }}
                    />
                    <span>{p.name}</span>
                    {primaryColor.toLowerCase() === p.color.toLowerCase() && (
                      <Check className="h-3 w-3 ml-1" />
                    )}
                  </button>
                ))}

                <div className="flex items-center gap-2 ml-auto">
                  <span className="text-xs text-muted-foreground">Personalizada:</span>
                  <input
                    type="color"
                    value={primaryColor}
                    onChange={(e) => setPrimaryColor(e.target.value)}
                    className="h-8 w-12 rounded cursor-pointer border p-0.5 bg-background"
                  />
                  <code className="text-xs font-mono">{primaryColor}</code>
                </div>
              </div>
            </div>

            {/* URL do Logotipo */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase text-muted-foreground block">
                URL do Logotipo Customizado
              </label>
              <Input
                placeholder="https://cdn.seuservico.com/logos/meu-tenant.png"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                className="text-xs"
              />
              <p className="text-[11px] text-muted-foreground">
                Se informado, substituirá a logo padrão na barra lateral e nas telas do sistema.
              </p>
            </div>

            {/* CSS Customizado */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase text-muted-foreground block flex items-center gap-1.5">
                <Code2 className="h-4 w-4" />
                CSS Personalizado Injetado
              </label>
              <textarea
                rows={4}
                placeholder="/* Adicione regras CSS específicas para este workspace */&#10;:root { --radius: 0.75rem; }"
                value={customCss}
                onChange={(e) => setCustomCss(e.target.value)}
                className="w-full bg-background border rounded-md p-3 font-mono text-xs focus:ring-1 focus:ring-primary focus:outline-none"
              />
            </div>

            <Button type="submit" disabled={isSaving} className="gap-2">
              {isSaving ? "Salvando Alterações..." : "Salvar & Aplicar Tema no Workspace"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
