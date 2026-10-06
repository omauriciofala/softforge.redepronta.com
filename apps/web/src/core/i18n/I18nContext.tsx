import React, { createContext, useContext, useEffect, useState, useMemo } from "react";
import { ptBR } from "./locales/pt-BR";
import { enUS } from "./locales/en-US";
import { AXIOS_INSTANCE } from "@/lib/api-client";

export type Locale = "pt-BR" | "en-US";

type PathImpl<T, K extends keyof T> = K extends string
  ? T[K] extends Record<string, any>
    ? `${K}.${PathImpl<T[K], keyof T[K]>}`
    : K
  : never;

type Path<T> = PathImpl<T, keyof T>;
export type I18nKey = Path<typeof ptBR>;

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const STORAGE_KEY = "softforge_locale";
const DEFAULT_LOCALE: Locale = "pt-BR";

const translations: Record<Locale, any> = {
  "pt-BR": ptBR,
  "en-US": enUS,
};

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as Locale | null;
    if (saved && (saved === "pt-BR" || saved === "en-US")) {
      return saved;
    }
    // Detecção automática de idioma do navegador
    if (typeof navigator !== "undefined" && navigator.language?.toLowerCase().startsWith("en")) {
      return "en-US";
    }
    return DEFAULT_LOCALE;
  });

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem(STORAGE_KEY, newLocale);
  };

  useEffect(() => {
    // Sincroniza o cabeçalho Accept-Language no Axios para chamadas à API
    AXIOS_INSTANCE.defaults.headers.common["Accept-Language"] = locale;
    document.documentElement.lang = locale;
  }, [locale]);

  const t = useMemo(() => {
    return (key: string, params?: Record<string, string | number>): string => {
      const keys = key.split(".");
      let result: any = translations[locale];

      for (const k of keys) {
        if (result && typeof result === "object" && k in result) {
          result = result[k];
        } else {
          // Fallback para pt-BR se não encontrado no idioma atual
          let fallback: any = translations[DEFAULT_LOCALE];
          for (const fb of keys) {
            if (fallback && typeof fallback === "object" && fb in fallback) {
              fallback = fallback[fb];
            } else {
              return key;
            }
          }
          result = fallback;
          break;
        }
      }

      if (typeof result !== "string") {
        return key;
      }

      if (params) {
        return Object.entries(params).reduce((acc, [paramKey, value]) => {
          return acc.replace(new RegExp(`\\{${paramKey}\\}`, "g"), String(value));
        }, result);
      }

      return result;
    };
  }, [locale]);

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n deve ser utilizado dentro de um I18nProvider");
  }
  return context;
};
