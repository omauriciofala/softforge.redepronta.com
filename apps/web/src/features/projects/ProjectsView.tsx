import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import { FolderGit2, Plus, Sparkles } from "lucide-react";

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

export const ProjectsView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  // Estados de criação de projeto
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDesc, setNewProjectDesc] = useState("");
  const [isCreatingProject, setIsCreatingProject] = useState(false);

  // Estados de tarefas rápidas por projeto
  const [activeProjectForTask, setActiveProjectForTask] = useState<string | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [projectTasks, setProjectTasks] = useState<Record<string, Task[]>>({});

  const fetchProjects = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<{ items: Project[]; total: number }>(
        `/api/v1/workspaces/${activeWorkspace.id}/projects`
      );
      setProjects(res.data.items);
    } catch (err) {
      console.error("Erro ao carregar projetos:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [activeWorkspace?.id]);

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
      console.error("Erro ao criar projeto:", err);
    }
  };

  const loadTasks = async (projectId: string) => {
    if (!activeWorkspace) return;
    try {
      const res = await AXIOS_INSTANCE.get<Task[]>(
        `/api/v1/workspaces/${activeWorkspace.id}/projects/${projectId}/tasks`
      );
      setProjectTasks((prev) => ({ ...prev, [projectId]: res.data }));
      setActiveProjectForTask((prev) => (prev === projectId ? null : projectId));
    } catch (err) {
      console.error("Erro ao carregar tarefas:", err);
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
      console.error("Erro ao criar tarefa:", err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <FolderGit2 className="h-6 w-6 text-primary" />
            Projetos & Tarefas
          </h2>
          <p className="text-sm text-muted-foreground">
            Gerencie fatias de negócio, metas e tarefas operadas por humanos e agentes de IA.
          </p>
        </div>
        <Button onClick={() => setIsCreatingProject(!isCreatingProject)} className="gap-2">
          <Plus className="h-4 w-4" />
          Novo Projeto
        </Button>
      </div>

      {isCreatingProject && (
        <Card className="border-primary/40 bg-card/60 backdrop-blur shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Cadastrar Novo Projeto</CardTitle>
            <CardDescription>
              Projetos respeitam o isolamento de tenant do workspace e quotas do plano contratado.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateProject} className="space-y-4 max-w-lg">
              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">Nome do Projeto</label>
                <Input
                  placeholder="Ex: Motor de Recomendação com IA"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  required
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">Descrição (Opcional)</label>
                <Input
                  placeholder="Ex: Pipeline RAG com busca vetorial e embeddings"
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit">Salvar Projeto</Button>
                <Button type="button" variant="outline" onClick={() => setIsCreatingProject(false)}>
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : projects.length === 0 ? (
        <Card className="text-center py-12 border-dashed">
          <CardContent className="space-y-3">
            <Sparkles className="h-10 w-10 text-muted-foreground mx-auto" />
            <p className="text-sm font-medium text-muted-foreground">
              Nenhum projeto cadastrado neste workspace ainda.
            </p>
            <Button size="sm" onClick={() => setIsCreatingProject(true)}>
              Criar Primeiro Projeto
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((proj) => {
            const isTasksOpen = activeProjectForTask === proj.id;
            const tasks = projectTasks[proj.id] || [];

            return (
              <Card key={proj.id} className="hover:border-primary/50 transition-colors flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base font-semibold truncate">{proj.name}</CardTitle>
                    <Badge variant="outline" className="text-xs shrink-0">
                      {proj.tasks_count} tarefas
                    </Badge>
                  </div>
                  {proj.description && (
                    <CardDescription className="text-xs line-clamp-2">{proj.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>Criado em {new Date(proj.created_at).toLocaleDateString()}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs"
                      onClick={() => loadTasks(proj.id)}
                    >
                      {isTasksOpen ? "Ocultar Tarefas" : "Ver Tarefas"}
                    </Button>
                  </div>

                  {isTasksOpen && (
                    <div className="border-t pt-3 space-y-2">
                      <form onSubmit={(e) => handleCreateTask(proj.id, e)} className="flex gap-1.5">
                        <Input
                          placeholder="Nova tarefa..."
                          value={newTaskTitle}
                          onChange={(e) => setNewTaskTitle(e.target.value)}
                          className="h-8 text-xs"
                        />
                        <Button type="submit" size="sm" className="h-8 text-xs shrink-0">
                          +
                        </Button>
                      </form>

                      <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1">
                        {tasks.length === 0 ? (
                          <p className="text-[11px] text-muted-foreground text-center py-2">
                            Nenhuma tarefa ativa.
                          </p>
                        ) : (
                          tasks.map((task) => (
                            <div
                              key={task.id}
                              className="flex items-center justify-between bg-muted/40 px-2 py-1.5 rounded text-xs"
                            >
                              <span className="truncate">{task.title}</span>
                              <Badge variant="secondary" className="text-[10px] shrink-0">
                                {task.status}
                              </Badge>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
