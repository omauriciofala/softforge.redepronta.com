import React, { createContext, useContext, useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";

export interface ThemeManifest {
  name: string;
  slug: string;
  version: string;
  engine: string;
  author?: string;
  description?: string;
  tokens: {
    colors?: Record<string, string>;
    typography?: Record<string, string>;
    geometry?: Record<string, string>;
  };
  assets?: {
    stylesheets?: string[];
    scripts?: string[];
  };
}

export interface WorkspaceThemeData {
  workspace_id: string;
  theme_slug: string;
  theme_name: string;
  theme_engine: string;
  custom_logo_url: string | null;
  custom_primary_color: string | null;
  custom_css: string | null;
  tokens: Record<string, any>;
  tokens_override: Record<string, any>;
  css_variables: Record<string, string>;
}

export interface ThemeContextType {
  activeTheme: WorkspaceThemeData | null;
  systemThemes: ThemeManifest[];
  isLoading: boolean;
  refreshTheme: () => Promise<void>;
  updateTheme: (data: {
    theme_slug?: string;
    custom_logo_url?: string | null;
    custom_primary_color?: string | null;
    custom_css?: string | null;
    tokens_override?: Record<string, any>;
  }) => Promise<void>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function hexToHsl(hex: string): string | null {
  const cleanHex = hex.replace("#", "").trim();
  if (cleanHex.length !== 6 && cleanHex.length !== 3) return null;
  const fullHex =
    cleanHex.length === 3
      ? cleanHex
          .split("")
          .map((c) => c + c)
          .join("")
      : cleanHex;

  const r = parseInt(fullHex.substring(0, 2), 16) / 255;
  const g = parseInt(fullHex.substring(2, 4), 16) / 255;
  const b = parseInt(fullHex.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h = Math.round(h * 60);
  }

  return `${Math.round(h)} ${(s * 100).toFixed(1)}% ${(l * 100).toFixed(1)}%`;
}

function applyCssTokensToDom(themeData: WorkspaceThemeData | null) {
  if (!themeData) return;

  const root = document.documentElement;

  // 1. Injetar todas as variáveis universais (--sf-*)
  if (themeData.css_variables) {
    Object.entries(themeData.css_variables).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });
  }

  // 2. Mapear para variáveis CSS nativas do Tailwind e Shadcn UI
  const primaryColor =
    themeData.custom_primary_color ||
    themeData.css_variables["--sf-color-primary"] ||
    "#2563eb";

  const hsl = hexToHsl(primaryColor);
  if (hsl) {
    root.style.setProperty("--primary", hsl);
  }

  if (themeData.css_variables["--sf-radius"]) {
    root.style.setProperty("--radius", themeData.css_variables["--sf-radius"]);
  }

  // 3. Injetar CSS customizado do tenant se existir
  let styleEl = document.getElementById("sf-workspace-custom-css") as HTMLStyleElement | null;
  if (themeData.custom_css) {
    if (!styleEl) {
      styleEl = document.createElement("style");
      styleEl.id = "sf-workspace-custom-css";
      document.head.appendChild(styleEl);
    }
    styleEl.textContent = themeData.custom_css;
  } else if (styleEl) {
    styleEl.remove();
  }
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { activeWorkspace } = useWorkspaces();
  const [activeTheme, setActiveTheme] = useState<WorkspaceThemeData | null>(null);
  const [systemThemes, setSystemThemes] = useState<ThemeManifest[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Carrega catálogo de temas disponíveis no sistema uma vez
  useEffect(() => {
    AXIOS_INSTANCE.get<ThemeManifest[]>("/api/v1/system/themes")
      .then((res) => setSystemThemes(res.data))
      .catch((err) => console.warn("Não foi possível carregar temas do sistema:", err));
  }, []);

  // Busca e aplica o tema ativo toda vez que o workspace ativo muda
  const fetchWorkspaceTheme = async () => {
    if (!activeWorkspace) {
      setActiveTheme(null);
      return;
    }
    setIsLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<WorkspaceThemeData>(
        `/api/v1/workspaces/${activeWorkspace.id}/theme`
      );
      setActiveTheme(res.data);
      applyCssTokensToDom(res.data);
    } catch (err) {
      console.warn("Erro ao buscar tema do workspace:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaceTheme();
  }, [activeWorkspace?.id]);

  const updateTheme = async (data: {
    theme_slug?: string;
    custom_logo_url?: string | null;
    custom_primary_color?: string | null;
    custom_css?: string | null;
    tokens_override?: Record<string, any>;
  }) => {
    if (!activeWorkspace) return;
    setIsLoading(true);
    try {
      const res = await AXIOS_INSTANCE.patch<WorkspaceThemeData>(
        `/api/v1/workspaces/${activeWorkspace.id}/theme`,
        data
      );
      setActiveTheme(res.data);
      applyCssTokensToDom(res.data);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ThemeContext.Provider
      value={{
        activeTheme,
        systemThemes,
        isLoading,
        refreshTheme: fetchWorkspaceTheme,
        updateTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme deve ser utilizado dentro de um ThemeProvider");
  }
  return context;
};
