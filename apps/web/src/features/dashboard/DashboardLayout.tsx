import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { LanguageSwitcher } from "@/core/i18n";
import { useTheme } from "@/core/theme";
import { useAuth } from "@/features/auth/AuthContext";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";

// Modulos integrados
import { ApiKeysView } from "@/features/apikeys/ApiKeysView";
import { AuditView } from "@/features/audit/AuditView";
import { BillingView } from "@/features/billing/BillingView";
import { NotificationBell } from "@/features/notifications/NotificationBell";
import { NotificationsView } from "@/features/notifications/NotificationsView";
import { ProjectsView } from "@/features/projects/ProjectsView";
import { StorageView } from "@/features/storage/StorageView";
import { ThemesView } from "@/features/themes/ThemesView";
import { WebhooksView } from "@/features/webhooks/WebhooksView";
import { MembersView } from "@/features/members/MembersView";
import { DevTasksView } from "@/features/dev_tasks/DevTasksView";

// Icones oficiais do Tabler
import {
  IconBook,
  IconChevronRight,
  IconCreditCard,
  IconDatabase,
  IconFolders,
  IconKey,
  IconLogout,
  IconMoon,
  IconPalette,
  IconPlus,
  IconRobot,
  IconSearch,
  IconShieldCheck,
  IconSun,
  IconUsers,
  IconWebhook,
} from "@tabler/icons-react";

export type DashboardTab =
  | "projects"
  | "dev_tasks"
  | "billing"
  | "notifications"
  | "audit"
  | "webhooks"
  | "apikeys"
  | "members"
  | "storage"
  | "themes";

export interface DashboardLayoutProps {
  onOpenDocs?: () => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ onOpenDocs }) => {
  const { user, logout } = useAuth();
  const { workspaces, activeWorkspace, setActiveWorkspace, createWorkspace } = useWorkspaces();
  const { activeTheme } = useTheme();

  const [activeTab, setActiveTab] = useState<DashboardTab>("projects");
  const [isCreatingWs, setIsCreatingWs] = useState(false);
  const [newWsName, setNewWsName] = useState("");
  const [isDark, setIsDark] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return document.documentElement.classList.contains("dark");
    }
    return false;
  });

  const toggleDarkMode = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName.trim()) return;
    try {
      await createWorkspace(newWsName.trim());
      setNewWsName("");
      setIsCreatingWs(false);
    } catch (err) {
      console.error(err);
    }
  };

  const navItems = [
    { id: "projects", label: "Projetos", icon: IconFolders },
    { id: "dev_tasks", label: "Tarefas de IA", icon: IconRobot },
    { id: "billing", label: "Billing & Pix", icon: IconCreditCard },
    { id: "audit", label: "Auditoria", icon: IconShieldCheck },
    { id: "webhooks", label: "Webhooks", icon: IconWebhook },
    { id: "apikeys", label: "Chaves de API", icon: IconKey },
    { id: "members", label: "Equipe & RBAC", icon: IconUsers },
    { id: "storage", label: "Arquivos & Storage", icon: IconDatabase },
    { id: "themes", label: "Temas & Cores", icon: IconPalette },
  ];

  const renderActiveView = () => {
    switch (activeTab) {
      case "projects":
        return <ProjectsView />;
      case "dev_tasks":
        return <DevTasksView />;
      case "billing":
        return <BillingView />;
      case "notifications":
        return <NotificationsView />;
      case "audit":
        return <AuditView />;
      case "webhooks":
        return <WebhooksView />;
      case "apikeys":
        return <ApiKeysView />;
      case "members":
        return <MembersView />;
      case "storage":
        return <StorageView />;
      case "themes":
        return <ThemesView />;
      default:
        return <ProjectsView />;
    }
  };

  const currentNav = navItems.find((n) => n.id === activeTab);
  const userInitials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase()
    : "U";

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
      {/* Sidebar Navigation - Estilo Tabler */}
      <aside className="w-64 border-r border-border bg-card flex flex-col justify-between shrink-0 shadow-sm z-20">
        <div className="flex flex-col h-full overflow-hidden">
          {/* Brand Header */}
          <div className="h-16 px-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2.5 truncate">
              {activeTheme?.custom_logo_url ? (
                <img
                  src={activeTheme.custom_logo_url}
                  alt="Logo Tenant"
                  className="h-8 w-8 object-contain rounded-md"
                />
              ) : (
                <div className="h-8 w-8 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-black text-sm shrink-0 shadow-sm">
                  ⚡
                </div>
              )}
              <div className="flex flex-col leading-tight truncate">
                <span className="font-bold text-sm tracking-tight truncate">
                  {activeTheme?.theme_name ? activeTheme.theme_name.split(" ")[0] : "SoftForge"}
                </span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
                  Dashboard
                </span>
              </div>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono px-1.5 py-0 border-border text-muted-foreground">
              {activeTheme?.theme_engine || "tabler"}
            </Badge>
          </div>

          {/* Workspace Switcher - Tabler Styled */}
          <div className="p-3 border-b border-border bg-muted/30">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Workspace
              </span>
              <button
                type="button"
                className="flex items-center gap-0.5 text-[11px] font-semibold text-primary hover:underline"
                onClick={() => setIsCreatingWs(!isCreatingWs)}
              >
                <IconPlus size={12} stroke={2} /> Novo
              </button>
            </div>

            {isCreatingWs ? (
              <form onSubmit={handleCreateWorkspace} className="space-y-1.5 mt-2">
                <Input
                  placeholder="Nome do Tenant..."
                  value={newWsName}
                  onChange={(e) => setNewWsName(e.target.value)}
                  className="h-7 text-xs bg-background"
                  autoFocus
                />
                <div className="flex gap-1">
                  <Button type="submit" size="sm" className="h-6 text-[10px] flex-1">
                    Criar
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="h-6 text-[10px]"
                    onClick={() => setIsCreatingWs(false)}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            ) : workspaces.length > 0 ? (
              <select
                value={activeWorkspace?.id || ""}
                onChange={(e) => {
                  const ws = workspaces.find((w) => w.id === e.target.value);
                  if (ws) setActiveWorkspace(ws);
                }}
                className="w-full bg-background border border-border rounded-md px-2.5 py-1.5 text-xs font-medium focus:ring-1 focus:ring-primary focus:outline-none truncate shadow-sm transition-colors"
              >
                {workspaces.map((ws) => (
                  <option key={ws.id} value={ws.id}>
                    {ws.name} ({ws.role})
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-xs text-muted-foreground">Nenhum workspace</span>
            )}
          </div>

          {/* Navigation Items - Estilo Tabler (com indicador lateral) */}
          <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
            <div className="px-2 pb-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
              Navegação
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as DashboardTab)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-xs transition-all text-left group ${
                    isActive
                      ? "bg-primary/10 text-primary font-semibold border-l-2 border-primary shadow-2xs"
                      : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
                  }`}
                >
                  <Icon
                    size={18}
                    stroke={isActive ? 2 : 1.5}
                    className={`shrink-0 transition-transform ${
                      isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                    }`}
                  />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer - Perfil e Ações */}
        <div className="p-3 border-t border-border bg-muted/20 space-y-2.5">
          {onOpenDocs && (
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenDocs}
              className="w-full justify-start gap-2 text-xs h-8 border-border bg-background shadow-2xs hover:bg-muted"
            >
              <IconBook size={15} stroke={1.5} />
              <span>Documentação OpenAPI</span>
            </Button>
          )}

          {/* User Info & Quick Logout */}
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2 truncate mr-2">
              <div className="h-7 w-7 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center shrink-0 border border-primary/20">
                {userInitials}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold truncate leading-tight">{user?.full_name}</p>
                <p className="text-[10px] text-muted-foreground truncate leading-tight">{user?.email}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
              title="Encerrar Sessão"
            >
              <IconLogout size={16} stroke={1.5} />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Topbar - Estilo Tabler */}
        <header className="h-16 border-b border-border bg-card px-6 flex items-center justify-between shrink-0 shadow-2xs">
          {/* Breadcrumb / Title */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground font-medium">Dashboard</span>
            <IconChevronRight size={14} className="text-muted-foreground" stroke={1.5} />
            <span className="font-semibold text-foreground">
              {currentNav?.label || "Geral"}
            </span>
            {activeWorkspace && (
              <span className="ml-2 font-mono text-[10px] bg-muted text-muted-foreground px-2 py-0.5 rounded-full border border-border">
                {activeWorkspace.name}
              </span>
            )}
          </div>

          {/* Quick Search & Actions */}
          <div className="flex items-center gap-3">
            {/* Search Pill - Tabler Style */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted/40 border border-border text-xs text-muted-foreground">
              <IconSearch size={14} stroke={1.5} />
              <span className="text-muted-foreground">Buscar rápido...</span>
              <kbd className="ml-2 px-1.5 py-0.2 bg-background border border-border rounded text-[10px] font-mono text-muted-foreground shadow-2xs">
                ⌘K
              </kbd>
            </div>

            {/* Alternador Claro / Escuro */}
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
              onClick={toggleDarkMode}
              title={isDark ? "Alternar para modo claro" : "Alternar para modo escuro"}
            >
              {isDark ? <IconSun size={17} stroke={1.5} /> : <IconMoon size={17} stroke={1.5} />}
            </Button>

            <LanguageSwitcher />
            <NotificationBell onOpenFullView={() => setActiveTab("notifications")} />
          </div>
        </header>

        {/* Dynamic Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-background">
          <div className="max-w-6xl mx-auto space-y-6">
            {!activeWorkspace ? (
              <Card className="text-center py-16 border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-xl font-bold">Nenhum Workspace Selecionado</CardTitle>
                  <CardDescription>
                    Crie ou selecione um tenant na barra lateral para começar a gerenciar sua aplicação.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button onClick={() => setIsCreatingWs(true)} className="gap-1.5 shadow-sm">
                    <IconPlus size={16} stroke={2} /> Criar Workspace
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <ErrorBoundary fallbackTitle="Falha ao carregar visão">
                {renderActiveView()}
              </ErrorBoundary>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};
