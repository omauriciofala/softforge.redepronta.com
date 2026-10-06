import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import { RefreshCw, Search, ShieldCheck } from "lucide-react";

interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  user_email?: string;
  ip_address?: string;
  created_at: string;
  details?: Record<string, any>;
}

export const AuditView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  const fetchLogs = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<{ items: AuditLog[]; total: number }>(
        `/api/v1/workspaces/${activeWorkspace.id}/audit-logs?page=1&page_size=50`
      );
      setLogs(res.data.items);
    } catch (err) {
      console.error("Erro ao carregar logs de auditoria:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [activeWorkspace?.id]);

  const filteredLogs = logs.filter(
    (log) =>
      log.action.toLowerCase().includes(search.toLowerCase()) ||
      (log.user_email && log.user_email.toLowerCase().includes(search.toLowerCase())) ||
      log.resource_type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            Trilha de Auditoria & Compliance
          </h2>
          <p className="text-sm text-muted-foreground">
            Registro imutável de todas as ações sensíveis executadas no tenant por usuários ou agentes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Filtrar por ação ou e-mail..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-9 text-xs"
            />
          </div>
          <Button variant="outline" size="sm" onClick={fetchLogs} className="gap-1.5 h-9">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/50 border-b text-muted-foreground uppercase font-semibold text-[11px]">
                <tr>
                  <th className="py-3 px-4">Ação</th>
                  <th className="py-3 px-4">Tipo de Recurso</th>
                  <th className="py-3 px-4">Usuário</th>
                  <th className="py-3 px-4">Endereço IP</th>
                  <th className="py-3 px-4">Data & Horário</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="text-center py-12">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto" />
                    </td>
                  </tr>
                ) : filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-12 text-muted-foreground">
                      Nenhum evento de auditoria encontrado.
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-muted/20 transition-colors">
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="font-mono text-[11px] bg-background">
                          {log.action}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 font-medium text-foreground">
                        {log.resource_type}
                        {log.resource_id && (
                          <span className="text-muted-foreground text-[10px] block font-mono">
                            ID: {log.resource_id.substring(0, 8)}...
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {log.user_email || <span className="italic">Sistema / Worker</span>}
                      </td>
                      <td className="py-3 px-4 font-mono text-muted-foreground">
                        {log.ip_address || "127.0.0.1"}
                      </td>
                      <td className="py-3 px-4 text-muted-foreground whitespace-nowrap">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
