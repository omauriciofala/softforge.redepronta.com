import React from "react";
import { useI18n, Locale } from "./I18nContext";

interface LanguageSwitcherProps {
  className?: string;
  variant?: "button" | "select";
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  className = "",
  variant = "button",
}) => {
  const { locale, setLocale, t } = useI18n();

  const toggleLanguage = () => {
    const nextLocale: Locale = locale === "pt-BR" ? "en-US" : "pt-BR";
    setLocale(nextLocale);
  };

  if (variant === "select") {
    return (
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        aria-label={t("language.switchLanguage")}
        className={`px-3 py-1.5 text-xs font-medium rounded-md border border-border bg-card text-foreground focus:outline-none focus:ring-2 focus:ring-primary ${className}`}
      >
        <option value="pt-BR">🇧🇷 {t("language.ptBR")}</option>
        <option value="en-US">🇺🇸 {t("language.enUS")}</option>
      </select>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleLanguage}
      title={t("language.switchLanguage")}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-md border border-border bg-card hover:bg-accent text-foreground transition-colors ${className}`}
    >
      <span>{locale === "pt-BR" ? "🇧🇷" : "🇺🇸"}</span>
      <span>{locale === "pt-BR" ? "PT" : "EN"}</span>
    </button>
  );
};
