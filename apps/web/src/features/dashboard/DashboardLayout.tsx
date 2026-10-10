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

import {
  Bell,
  BookOpen,
  Bot,
  CreditCard,
  FolderGit2,
  HardDrive,
  Key,
  LogOut,
  Palette,
  Plus,
  ShieldCheck,
  Users,
  Webhook,
} from "lucide-react";

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
    { id: "projects", label: "Projetos", icon: FolderGit2 },
    { id: "dev_tasks", label: "Tarefas de IA", icon: Bot },
    { id: "billing", label: "Billing & Pix", icon: CreditCard },
    { id: "notifications", label: "Notificações", icon: Bell },
    { id: "audit", label: "Auditoria", icon: ShieldCheck },
    { id: "webhooks", label: "Webhooks", icon: Webhook },
    { id: "apikeys", label: "Chaves de API", icon: Key },
    { id: "members", label: "Equipe & RBAC", icon: Users },
    { id: "storage", label: "Arquivos & Storage", icon: HardDrive },
    { id: "themes", label: "Temas & Cores", icon: Palette },
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

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r bg-card flex flex-col justify-between shrink-0 shadow-sm z-20">
        <div className="flex flex-col h-full overflow-hidden">
          {/* Brand Header */}
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-2 truncate">
              {activeTheme?.custom_logo_url ? (
                <img
                  src={activeTheme.custom_logo_url}
                  alt="Logo Tenant"
                  className="h-7 w-7 object-contain rounded"
                />
              ) : (
                <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-black text-sm shrink-0 shadow">
                  ⚡
                </div>
              )}
              <span className="font-extrabold text-base tracking-tight truncate">
                {activeTheme?.theme_name ? activeTheme.theme_name.split(" ")[0] : "SoftForge"}
              </span>
            </div>
            <Badge variant="outline" className="text-[10px] uppercase font-mono shrink-0">
              {activeTheme?.theme_engine || "react"}
            </Badge>
          </div>

          {/* Workspace Switcher */}
          <div className="p-3 border-b bg-muted/20">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold uppercase text-muted-foreground">Workspace</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-5 px-1 text-[11px] text-primary"
                onClick={() => setIsCreatingWs(!isCreatingWs)}
              >
                <Plus className="h-3 w-3 mr-0.5" /> Novo
              </Button>
            </div>

            {isCreatingWs ? (
              <form onSubmit={handleCreateWorkspace} className="space-y-1.5 mt-2">
                <Input
                  placeholder="Nome do Tenant..."
                  value={newWsName}
                  onChange={(e) => setNewWsName(e.target.value)}
                  className="h-7 text-xs"
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
                    X
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
                className="w-full bg-background border rounded px-2 py-1.5 text-xs font-medium focus:ring-1 focus:ring-primary focus:outline-none truncate"
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

          {/* Navigation Items */}
          <nav className="flex-1 overflow-y-auto p-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as DashboardTab)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-left ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm font-semibold"
                      : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t bg-muted/10 space-y-2">
          {onOpenDocs && (
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenDocs}
              className="w-full justify-start gap-2 text-xs h-8"
            >
              <BookOpen className="h-3.5 w-3.5" />
              Documentação OpenAPI
            </Button>
          )}

          <div className="flex items-center justify-between pt-1">
            <div className="truncate mr-2">
              <p className="text-xs font-semibold truncate">{user?.full_name}</p>
              <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
              title="Encerrar Sessão"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Topbar */}
        <header className="h-14 border-b bg-card px-6 flex items-center justify-between shrink-0 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold capitalize text-foreground">
              {navItems.find((n) => n.id === activeTab)?.label}
            </span>
            {activeWorkspace && (
              <>
                <span className="text-muted-foreground text-xs">/</span>
                <span className="text-xs text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded">
                  {activeWorkspace.name}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <NotificationBell onOpenFullView={() => setActiveTab("notifications")} />
          </div>
        </header>

        {/* Dynamic Body */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto">
            {!activeWorkspace ? (
              <Card className="text-center py-16">
                <CardHeader>
                  <CardTitle className="text-xl">Nenhum Workspace Selecionado</CardTitle>
                  <CardDescription>
                    Crie ou selecione um tenant na barra lateral para começar a gerenciar sua aplicação.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button onClick={() => setIsCreatingWs(true)}>+ Criar Workspace</Button>
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
