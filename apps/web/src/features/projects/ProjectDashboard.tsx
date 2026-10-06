import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "../auth/AuthContext";
import { useWorkspaces } from "../workspaces/WorkspaceContext";

interface Task {
  id: string;
  project_id: string;
  title: string;
  status: string;
  priority: string;
}

interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  is_archived: boolean;
  created_at: string;
  tasks_count: number;
}

export interface ProjectDashboardProps {
  onOpenDocs?: () => void;
}

export const ProjectDashboard: React.FC<ProjectDashboardProps> = ({ onOpenDocs }) => {
  const { user, logout } = useAuth();
  const { workspaces, activeWorkspace, setActiveWorkspace, createWorkspace } = useWorkspaces();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);

  // Estados de criação de projeto
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDesc, setNewProjectDesc] = useState("");
  const [isCreatingProject, setIsCreatingProject] = useState(false);

  // Estados de criação de workspace
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [isCreatingWs, setIsCreatingWs] = useState(false);

  // Estados de tarefas rápidas
  const [activeProjectForTask, setActiveProjectForTask] = useState<string | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [projectTasks, setProjectTasks] = useState<Record<string, Task[]>>({});

  const fetchProjects = async () => {
    if (!activeWorkspace) return;
    setLoadingProjects(true);
    try {
      const res = await AXIOS_INSTANCE.get<{ items: Project[]; total: number }>(
        `/api/v1/workspaces/${activeWorkspace.id}/projects`
      );
      setProjects(res.data.items);
    } catch (err) {
      console.error("Erro ao buscar projetos:", err);
    } finally {
      setLoadingProjects(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [activeWorkspace]);

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorkspaceName.trim()) return;
    try {
      await createWorkspace(newWorkspaceName);
      setNewWorkspaceName("");
      setIsCreatingWs(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !newProjectName.trim()) return;
    try {
      await AXIOS_INSTANCE.post(`/api/v1/workspaces/${activeWorkspace.id}/projects`, {
        name: newProjectName,
        description: newProjectDesc || null,
      });
      setNewProjectName("");
      setNewProjectDesc("");
      setIsCreatingProject(false);
      fetchProjects();
    } catch (err) {
      console.error(err);
    }
  };

  const loadTasks = async (projectId: string) => {
    if (!activeWorkspace) return;
    try {
      const res = await AXIOS_INSTANCE.get<Task[]>(
        `/api/v1/workspaces/${activeWorkspace.id}/projects/${projectId}/tasks`
      );
      setProjectTasks((prev) => ({ ...prev, [projectId]: res.data }));
      setActiveProjectForTask(projectId);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateTask = async (projectId: string, e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !newTaskTitle.trim()) return;
    try {
      await AXIOS_INSTANCE.post(
        `/api/v1/workspaces/${activeWorkspace.id}/projects/${projectId}/tasks`,
        {
          title: newTaskTitle,
          status: "todo",
          priority: "medium",
        }
      );
      setNewTaskTitle("");
      loadTasks(projectId);
      fetchProjects();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navbar */}
      <header className="border-b bg-card px-6 py-3 shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="font-extrabold text-xl tracking-tight text-primary flex items-center gap-1.5">
            <span>⚡</span> SoftForge
          </span>
          <span className="text-muted-foreground">/</span>
          {/* Seletor de Workspace */}
          <div className="flex items-center space-x-2">
            {workspaces.length > 0 ? (
              <select
                className="bg-background border rounded-md px-3 py-1.5 text-sm font-medium focus:ring-1 focus:ring-primary focus:outline-none"
                value={activeWorkspace?.id || ""}
                onChange={(e) => {
                  const ws = workspaces.find((w) => w.id === e.target.value);
                  if (ws) setActiveWorkspace(ws);
                }}
              >
                {workspaces.map((ws) => (
                  <option key={ws.id} value={ws.id}>
                    {ws.name} ({ws.role})
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-sm text-muted-foreground">Nenhum workspace</span>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsCreatingWs(!isCreatingWs)}
            >
              + Novo Tenant
            </Button>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {onOpenDocs && (
            <Button variant="outline" size="sm" onClick={onOpenDocs} className="gap-1.5 text-xs">
              <span>📖</span> Docs & Manual
            </Button>
          )}

          <div className="text-right">
            <p className="text-sm font-semibold">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
          <Button variant="ghost" size="sm" onClick={logout}>
            Sair
          </Button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Painel de Criação Rápida de Workspace */}
        {isCreatingWs && (
          <Card className="border-primary/30 bg-primary/5">
            <CardHeader>
              <CardTitle className="text-lg">Criar Novo Workspace (Tenant)</CardTitle>
              <CardDescription>
                Organize equipes e recursos isolados com controle de acesso baseado em papéis (RBAC).
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateWorkspace} className="flex gap-3 max-w-md">
                <Input
                  placeholder="Nome do Workspace (ex: Fintech Corp)"
                  value={newWorkspaceName}
                  onChange={(e) => setNewWorkspaceName(e.target.value)}
                  required
                />
                <Button type="submit">Criar</Button>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setIsCreatingWs(false)}
                >
                  Cancelar
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Header do Workspace Ativo */}
        {activeWorkspace ? (
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight">{activeWorkspace.name}</h1>
                <Badge variant="secondary" className="uppercase font-mono text-[10px]">
                  {activeWorkspace.role}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                Slug: <code className="bg-muted px-1.5 py-0.5 rounded">{activeWorkspace.slug}</code>
              </p>
            </div>
            <Button onClick={() => setIsCreatingProject(!isCreatingProject)}>
              + Novo Projeto
            </Button>
          </div>
        ) : (
          <div className="text-center py-16 border rounded-xl bg-card">
            <p className="text-muted-foreground mb-4">Você ainda não possui nenhum workspace configurado.</p>
            <Button onClick={() => setIsCreatingWs(true)}>Criar meu primeiro Workspace</Button>
          </div>
        )}

        {/* Form para Novo Projeto */}
        {isCreatingProject && (
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-lg">Novo Projeto Vertical</CardTitle>
              <CardDescription>
                Cada projeto pertence a este workspace e pode conter tarefas e recursos vinculados.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateProject} className="space-y-3 max-w-lg">
                <Input
                  placeholder="Nome do Projeto (ex: App Mobile v1)"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  required
                />
                <Input
                  placeholder="Descrição resumida do projeto (opcional)"
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                />
                <div className="flex gap-2 pt-2">
                  <Button type="submit">Salvar Projeto</Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setIsCreatingProject(false)}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Grade de Projetos */}
        {activeWorkspace && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Projetos Ativos ({projects.length})</h2>
              {loadingProjects && <span className="text-xs text-muted-foreground">Atualizando...</span>}
            </div>

            {projects.length === 0 && !loadingProjects ? (
              <div className="text-center py-12 border border-dashed rounded-lg">
                <p className="text-sm text-muted-foreground mb-3">Nenhum projeto cadastrado neste workspace.</p>
                <Button variant="outline" size="sm" onClick={() => setIsCreatingProject(true)}>
                  Criar Primeiro Projeto
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects.map((project) => (
                  <Card key={project.id} className="flex flex-col justify-between hover:shadow-md transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-lg font-semibold">{project.name}</CardTitle>
                        <Badge variant="outline">{project.tasks_count} tarefas</Badge>
                      </div>
                      <CardDescription className="line-clamp-2">
                        {project.description || "Sem descrição informada."}
                      </CardDescription>
                    </CardHeader>

                    <CardContent className="space-y-3 flex-1">
                      {activeProjectForTask === project.id && (
                        <div className="border-t pt-3 space-y-2">
                          <p className="text-xs font-semibold text-muted-foreground uppercase">Tarefas do Projeto:</p>
                          <div className="space-y-1 max-h-40 overflow-y-auto">
                            {(projectTasks[project.id] || []).map((t) => (
                              <div
                                key={t.id}
                                className="flex items-center justify-between text-xs p-1.5 rounded bg-muted/50 border"
                              >
                                <span className="font-medium">{t.title}</span>
                                <Badge variant="secondary" className="text-[9px]">
                                  {t.status}
                                </Badge>
                              </div>
                            ))}
                            {(projectTasks[project.id] || []).length === 0 && (
                              <p className="text-xs text-muted-foreground italic">Nenhuma tarefa criada.</p>
                            )}
                          </div>

                          <form
                            onSubmit={(e) => handleCreateTask(project.id, e)}
                            className="flex gap-2 pt-2"
                          >
                            <Input
                              placeholder="Nova tarefa..."
                              className="h-8 text-xs"
                              value={newTaskTitle}
                              onChange={(e) => setNewTaskTitle(e.target.value)}
                              required
                            />
                            <Button size="sm" className="h-8 text-xs" type="submit">
                              Add
                            </Button>
                          </form>
                        </div>
                      )}
                    </CardContent>

                    <CardFooter className="border-t pt-3">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="w-full text-xs"
                        onClick={() => {
                          if (activeProjectForTask === project.id) {
                            setActiveProjectForTask(null);
                          } else {
                            loadTasks(project.id);
                          }
                        }}
                      >
                        {activeProjectForTask === project.id ? "Ocultar Tarefas" : "Ver / Gerenciar Tarefas"}
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};
