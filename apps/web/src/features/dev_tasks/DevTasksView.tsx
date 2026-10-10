import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Clock,
  Code2,
  FileCode,
  History,
  MessageSquare,
  Play,
  Plus,
  Terminal,
  XCircle,
} from "lucide-react";

export interface DevTaskNote {
  id: string;
  task_id: string;
  author: string;
  note_type: "progress" | "decision" | "blocker" | "verification";
  content: string;
  created_at: string;
}

export interface DevTask {
  id: string;
  workspace_id: string;
  project_id: string | null;
  title: string;
  description: string | null;
  task_type: "feature" | "bugfix" | "refactor" | "test" | "doc" | "chore";
  priority: "low" | "medium" | "high" | "urgent";
  status: "todo" | "in_progress" | "review" | "completed" | "failed" | "blocked" | "cancelled";
  target_files: string[];
  acceptance_criteria: string[];
  verification_command: string | null;
  verification_output: string | null;
  git_branch: string | null;
  assigned_agent: string | null;
  created_by_id: string | null;
  created_at: string;
  updated_at: string;
  notes: DevTaskNote[];
}

export const DevTasksView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [tasks, setTasks] = useState<DevTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filtros
  const [statusFilter, setStatusFilter] = useState<string>("all");

  // Estado de criação
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newType, setNewType] = useState<DevTask["task_type"]>("feature");
  const [newPriority, setNewPriority] = useState<DevTask["priority"]>("medium");
  const [newTargetFiles, setNewTargetFiles] = useState("");
  const [newCriteria, setNewCriteria] = useState("");
  const [newVerifyCmd, setNewVerifyCmd] = useState("pytest");
  const [newAgent, setNewAgent] = useState("antigravity");
  const [submitting, setSubmitting] = useState(false);

  // Estados de ações interativas
  const [activeTaskNotes, setActiveTaskNotes] = useState<string | null>(null);
  const [completingTaskId, setCompletingTaskId] = useState<string | null>(null);
  const [noteContent, setNoteContent] = useState<Record<string, string>>({});
  const [addingNoteId, setAddingNoteId] = useState<string | null>(null);
  const [blockReason, setBlockReason] = useState<Record<string, string>>({});
  const [blockingId, setBlockingId] = useState<string | null>(null);

  const fetchTasks = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const url =
        statusFilter === "all"
          ? `/api/v1/workspaces/${activeWorkspace.id}/dev-tasks`
          : `/api/v1/workspaces/${activeWorkspace.id}/dev-tasks?status=${statusFilter}`;
      const res = await AXIOS_INSTANCE.get<{ items: DevTask[]; total: number }>(url);
      setTasks(res.data.items);
    } catch (err: any) {
      console.error("Erro ao listar tarefas de desenvolvimento:", err);
      setErrorMsg("Não foi possível carregar as tarefas do agente.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [activeWorkspace?.id, statusFilter]);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !newTitle.trim()) return;

    setSubmitting(true);
    try {
      const target_files = newTargetFiles
        ? newTargetFiles.split(",").map((s) => s.trim()).filter(Boolean)
        : [];
      const acceptance_criteria = newCriteria
        ? newCriteria.split(",").map((s) => s.trim()).filter(Boolean)
        : [];

      await AXIOS_INSTANCE.post(`/api/v1/workspaces/${activeWorkspace.id}/dev-tasks`, {
        title: newTitle.trim(),
        description: newDesc.trim() || null,
        task_type: newType,
        priority: newPriority,
        target_files,
        acceptance_criteria,
        verification_command: newVerifyCmd.trim() || null,
        assigned_agent: newAgent.trim() || null,
      });

      setNewTitle("");
      setNewDesc("");
      setNewTargetFiles("");
      setNewCriteria("");
      setIsCreating(false);
      fetchTasks();
    } catch (err: any) {
      console.error("Erro ao criar DevTask:", err);
      alert(err.response?.data?.message || "Erro ao criar tarefa.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClaim = async (taskId: string, agentName: string = "antigravity") => {
    if (!activeWorkspace) return;
    try {
      await AXIOS_INSTANCE.post(`/api/v1/workspaces/${activeWorkspace.id}/dev-tasks/${taskId}/claim`, {
        agent_name: agentName,
      });
      fetchTasks();
    } catch (err: any) {
      alert(err.response?.data?.message || "Erro ao assumir tarefa.");
    }
  };

  const handleComplete = async (taskId: string) => {
    if (!activeWorkspace) return;
    setCompletingTaskId(taskId);
    try {
      await AXIOS_INSTANCE.post(
        `/api/v1/workspaces/${activeWorkspace.id}/dev-tasks/${taskId}/complete`,
        {
          summary: "Concluído via painel web com verificação estrita aprovada.",
          execute_verification: true,
        }
      );
      fetchTasks();
    } catch (err: any) {
      const msg = err.response?.data?.message || "Falha na verificação estrita da tarefa.";
      alert(`❌ ${msg}`);
      fetchTasks();
    } finally {
      setCompletingTaskId(null);
    }
  };

  const handleAddNote = async (taskId: string) => {
    if (!activeWorkspace) return;
    const content = noteContent[taskId]?.trim();
    if (!content) return;

    try {
      await AXIOS_INSTANCE.post(`/api/v1/workspaces/${activeWorkspace.id}/dev-tasks/${taskId}/notes`, {
        author: "web-operator",
        note_type: "progress",
        content,
      });
      setNoteContent((prev) => ({ ...prev, [taskId]: "" }));
      setAddingNoteId(null);
      fetchTasks();
    } catch (err: any) {
      alert(err.response?.data?.message || "Erro ao adicionar anotação.");
    }
  };

  const handleFailBlock = async (taskId: string) => {
    if (!activeWorkspace) return;
    const reason = blockReason[taskId]?.trim();
    if (!reason) return;

    try {
      await AXIOS_INSTANCE.post(`/api/v1/workspaces/${activeWorkspace.id}/dev-tasks/${taskId}/fail`, {
        reason,
        is_blocked: true,
        blocker_details: "Sinalizado manualmente via interface web.",
      });
      setBlockReason((prev) => ({ ...prev, [taskId]: "" }));
      setBlockingId(null);
      fetchTasks();
    } catch (err: any) {
      alert(err.response?.data?.message || "Erro ao registrar bloqueio.");
    }
  };

  // Contadores rápidos
  const totalCount = tasks.length;
  const inProgressCount = tasks.filter((t) => t.status === "in_progress").length;
  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const blockedCount = tasks.filter((t) => t.status === "blocked" || t.status === "failed").length;

  const getStatusBadge = (status: DevTask["status"]) => {
    switch (status) {
      case "todo":
        return <Badge variant="outline" className="text-muted-foreground border-muted-foreground/30">Pendente</Badge>;
      case "in_progress":
        return <Badge className="bg-blue-600 hover:bg-blue-700 text-white animate-pulse">Em Execução</Badge>;
      case "review":
        return <Badge className="bg-amber-500 hover:bg-amber-600 text-white">Revisão</Badge>;
      case "completed":
        return <Badge className="bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Concluída</Badge>;
      case "blocked":
        return <Badge variant="destructive" className="flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Bloqueada</Badge>;
      case "failed":
        return <Badge variant="destructive" className="flex items-center gap-1"><XCircle className="h-3 w-3" /> Falhou</Badge>;
      case "cancelled":
        return <Badge variant="outline" className="line-through text-muted-foreground">Cancelada</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority: DevTask["priority"]) => {
    switch (priority) {
      case "urgent":
        return <span className="text-[10px] font-bold text-red-500 uppercase tracking-wider">🔥 Urgente</span>;
      case "high":
        return <span className="text-[10px] font-bold text-amber-500 uppercase tracking-wider">⚡ Alta</span>;
      case "medium":
        return <span className="text-[10px] font-medium text-blue-500 uppercase tracking-wider">Média</span>;
      default:
        return <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Baixa</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Topo do Módulo */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Bot className="h-6 w-6 text-primary" />
            Tarefas de IA & Engenharia (DevTasks)
          </h2>
          <p className="text-sm text-muted-foreground">
            Orquestração técnica, monitoramento de agentes autônomos e guardrails estritos de verificação.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setIsCreating(!isCreating)}
            className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
          >
            <Plus className="h-4 w-4" />
            Nova Tarefa de IA
          </Button>
        </div>
      </div>

      {/* Métricas Rápidas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card/60 backdrop-blur shadow-sm border-border">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-medium">Total de Tarefas</CardDescription>
            <CardTitle className="text-2xl font-bold">{totalCount}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="bg-blue-500/10 border-blue-500/20 backdrop-blur shadow-sm">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-medium text-blue-500">Em Andamento</CardDescription>
            <CardTitle className="text-2xl font-bold text-blue-500">{inProgressCount}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="bg-emerald-500/10 border-emerald-500/20 backdrop-blur shadow-sm">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-medium text-emerald-500">Concluídas</CardDescription>
            <CardTitle className="text-2xl font-bold text-emerald-500">{completedCount}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="bg-red-500/10 border-red-500/20 backdrop-blur shadow-sm">
          <CardHeader className="p-4 pb-2">
            <CardDescription className="text-xs uppercase font-medium text-red-500">Bloqueadas / Falhas</CardDescription>
            <CardTitle className="text-2xl font-bold text-red-500">{blockedCount}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {errorMsg && (
        <div className="p-3 text-xs bg-red-500/10 border border-red-500/20 text-red-500 rounded-md">
          {errorMsg}
        </div>
      )}

      {/* Formulário de Criação Rápida */}
      {isCreating && (
        <Card className="border-primary/40 bg-card/90 shadow-md">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Code2 className="h-5 w-5 text-primary" />
              Criar Nova Tarefa para Agente de IA
            </CardTitle>
            <CardDescription>
              Tarefas técnicas exigem arquivos-alvo, critérios de aceite e comando determinístico de verificação.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Título da Tarefa</label>
                  <Input
                    placeholder="Ex: Refatorar autenticação JWT e adicionar rota de rotação"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    required
                    className="mt-1"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Descrição / Prompt do Agente</label>
                  <Input
                    placeholder="Contexto detalhado, decisões arquiteturais esperadas ou restrições..."
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Tipo de Tarefa</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value as any)}
                    className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    <option value="feature">Feature (Nova Funcionalidade)</option>
                    <option value="bugfix">Bugfix (Correção)</option>
                    <option value="refactor">Refactor (Refatoração)</option>
                    <option value="test">Test (Testes Automatizados)</option>
                    <option value="doc">Doc (Documentação)</option>
                    <option value="chore">Chore (Manutenção/DevOps)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Prioridade</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value as any)}
                    className="mt-1 flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  >
                    <option value="low">Baixa</option>
                    <option value="medium">Média</option>
                    <option value="high">Alta</option>
                    <option value="urgent">Urgente</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Arquivos-Alvo (separados por vírgula)</label>
                  <Input
                    placeholder="src/slices/auth/router.py, src/slices/auth/service.py"
                    value={newTargetFiles}
                    onChange={(e) => setNewTargetFiles(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-muted-foreground">Critérios de Aceite (separados por vírgula)</label>
                  <Input
                    placeholder="Testes passando, Retorno 200 OK, Lint sem erros"
                    value={newCriteria}
                    onChange={(e) => setNewCriteria(e.target.value)}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-muted-foreground flex items-center gap-1">
                    <Terminal className="h-3 w-3 text-primary" /> Comando de Verificação Estrita
                  </label>
                  <Input
                    placeholder="pytest apps/api/src/slices/auth/tests/ -v"
                    value={newVerifyCmd}
                    onChange={(e) => setNewVerifyCmd(e.target.value)}
                    className="mt-1 font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase text-muted-foreground flex items-center gap-1">
                    <Bot className="h-3 w-3 text-primary" /> Agente Designado
                  </label>
                  <Input
                    placeholder="antigravity, claude-code ou cursor"
                    value={newAgent}
                    onChange={(e) => setNewAgent(e.target.value)}
                    className="mt-1"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setIsCreating(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Cadastrando..." : "Criar Tarefa de IA"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Barra de Filtro de Status */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-border text-sm">
        <span className="text-xs font-semibold uppercase text-muted-foreground mr-2">Filtrar:</span>
        {[
          { id: "all", label: "Todas" },
          { id: "todo", label: "Pendentes" },
          { id: "in_progress", label: "Em Execução" },
          { id: "review", label: "Revisão" },
          { id: "completed", label: "Concluídas" },
          { id: "blocked", label: "Bloqueadas" },
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setStatusFilter(f.id)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              statusFilter === f.id
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Listagem de Tarefas */}
      {loading ? (
        <div className="py-12 flex justify-center items-center text-muted-foreground">
          <Clock className="h-6 w-6 animate-spin mr-2" /> Carregando tarefas de desenvolvimento...
        </div>
      ) : tasks.length === 0 ? (
        <Card className="p-8 text-center bg-card/30 border-dashed">
          <Bot className="h-10 w-10 text-muted-foreground mx-auto mb-2 opacity-50" />
          <h3 className="font-semibold text-foreground">Nenhuma tarefa encontrada</h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
            Não há tarefas registradas com os filtros atuais. Use o botão acima para criar ou consuma via CLI / Servidor MCP.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {tasks.map((task) => (
            <Card key={task.id} className="bg-card/70 backdrop-blur border-border hover:border-border/80 transition-all shadow-sm">
              <CardHeader className="p-5 pb-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {getStatusBadge(task.status)}
                    <Badge variant="outline" className="text-xs font-mono uppercase">
                      {task.task_type}
                    </Badge>
                    {getPriorityBadge(task.priority)}
                    {task.assigned_agent && (
                      <Badge variant="secondary" className="text-xs flex items-center gap-1 font-mono">
                        <Bot className="h-3 w-3 text-primary" />
                        {task.assigned_agent}
                      </Badge>
                    )}
                  </div>
                  <span className="text-[11px] text-muted-foreground font-mono">
                    ID: {task.id.slice(0, 8)}...
                  </span>
                </div>
                <CardTitle className="text-lg font-semibold mt-2">{task.title}</CardTitle>
                {task.description && (
                  <CardDescription className="text-sm text-foreground/80 mt-1">
                    {task.description}
                  </CardDescription>
                )}
              </CardHeader>

              <CardContent className="p-5 pt-0 space-y-3">
                {/* Arquivos-alvo */}
                {task.target_files && task.target_files.length > 0 && (
                  <div className="flex items-center gap-2 flex-wrap text-xs">
                    <span className="text-muted-foreground flex items-center gap-1 font-semibold">
                      <FileCode className="h-3.5 w-3.5" /> Arquivos:
                    </span>
                    {task.target_files.map((f, i) => (
                      <span key={i} className="bg-muted px-2 py-0.5 rounded font-mono text-[11px] text-foreground">
                        {f}
                      </span>
                    ))}
                  </div>
                )}

                {/* Critérios de Aceite */}
                {task.acceptance_criteria && task.acceptance_criteria.length > 0 && (
                  <div className="text-xs bg-muted/30 p-2.5 rounded-md border border-border/50">
                    <span className="font-semibold text-muted-foreground block mb-1">Critérios de Aceite:</span>
                    <ul className="space-y-1">
                      {task.acceptance_criteria.map((c, i) => (
                        <li key={i} className="flex items-center gap-2 text-foreground/90">
                          <CheckCircle2 className="h-3 w-3 text-emerald-500 shrink-0" />
                          <span>{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Comando de Verificação */}
                {task.verification_command && (
                  <div className="flex items-center gap-2 bg-slate-950 text-slate-100 px-3 py-1.5 rounded-md text-xs font-mono border border-slate-800">
                    <Terminal className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                    <span className="text-muted-foreground select-none">$</span>
                    <span className="overflow-x-auto">{task.verification_command}</span>
                  </div>
                )}

                {/* Barra de Ações Rápidas */}
                <div className="flex items-center justify-between pt-2 border-t border-border/40 gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    {task.status !== "in_progress" && task.status !== "completed" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleClaim(task.id, "antigravity")}
                        className="text-xs gap-1"
                      >
                        <Bot className="h-3.5 w-3.5 text-primary" />
                        Assumir (Claim)
                      </Button>
                    )}

                    {task.status !== "completed" && (
                      <Button
                        size="sm"
                        variant="default"
                        disabled={completingTaskId === task.id}
                        onClick={() => handleComplete(task.id)}
                        className="text-xs gap-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        <Play className="h-3.5 w-3.5" />
                        {completingTaskId === task.id ? "Verificando..." : "Concluir (Verify)"}
                      </Button>
                    )}

                    {task.status !== "completed" && task.status !== "blocked" && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setBlockingId(blockingId === task.id ? null : task.id)}
                        className="text-xs text-red-500 hover:text-red-600 gap-1"
                      >
                        <AlertTriangle className="h-3.5 w-3.5" />
                        Bloqueio
                      </Button>
                    )}

                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setAddingNoteId(addingNoteId === task.id ? null : task.id)}
                      className="text-xs gap-1"
                    >
                      <MessageSquare className="h-3.5 w-3.5" />
                      Adicionar Nota
                    </Button>
                  </div>

                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setActiveTaskNotes(activeTaskNotes === task.id ? null : task.id)}
                    className="text-xs gap-1 text-muted-foreground"
                  >
                    <History className="h-3.5 w-3.5" />
                    {task.notes?.length || 0} notas / histórico
                  </Button>
                </div>

                {/* Formulário Rápido de Nota */}
                {addingNoteId === task.id && (
                  <div className="pt-2 flex gap-2">
                    <Input
                      placeholder="Registrar nota de progresso ou decisão técnica..."
                      value={noteContent[task.id] || ""}
                      onChange={(e) => setNoteContent({ ...noteContent, [task.id]: e.target.value })}
                      className="text-xs h-8"
                    />
                    <Button size="sm" onClick={() => handleAddNote(task.id)} className="text-xs h-8">
                      Salvar
                    </Button>
                  </div>
                )}

                {/* Formulário Rápido de Bloqueio */}
                {blockingId === task.id && (
                  <div className="pt-2 flex gap-2">
                    <Input
                      placeholder="Motivo do impedimento técnico..."
                      value={blockReason[task.id] || ""}
                      onChange={(e) => setBlockReason({ ...noteContent, [task.id]: e.target.value })}
                      className="text-xs h-8 border-red-500/50"
                    />
                    <Button size="sm" variant="destructive" onClick={() => handleFailBlock(task.id)} className="text-xs h-8">
                      Confirmar Bloqueio
                    </Button>
                  </div>
                )}

                {/* Histórico e Timeline de Notas */}
                {activeTaskNotes === task.id && (
                  <div className="mt-3 pt-3 border-t border-border/50 space-y-2">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1">
                      <History className="h-3.5 w-3.5" /> Histórico de Execução & Guardrails
                    </h4>

                    {task.verification_output && (
                      <div className="p-2.5 rounded bg-slate-950 text-slate-200 text-xs font-mono space-y-1">
                        <span className="text-[10px] text-muted-foreground uppercase block font-sans">
                          Última Saída do Guardrail:
                        </span>
                        <pre className="whitespace-pre-wrap max-h-40 overflow-y-auto">{task.verification_output}</pre>
                      </div>
                    )}

                    {(!task.notes || task.notes.length === 0) ? (
                      <p className="text-xs text-muted-foreground italic">Nenhuma anotação registrada ainda.</p>
                    ) : (
                      <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                        {task.notes.map((n) => (
                          <div key={n.id} className="text-xs p-2 rounded bg-muted/40 border border-border/40">
                            <div className="flex items-center justify-between text-muted-foreground text-[10px] mb-1">
                              <span className="font-semibold text-foreground">{n.author} ({n.note_type})</span>
                              <span>{new Date(n.created_at).toLocaleString("pt-BR")}</span>
                            </div>
                            <p className="whitespace-pre-wrap text-foreground/90">{n.content}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
