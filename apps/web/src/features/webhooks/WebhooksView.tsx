import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import { Eye, EyeOff, Plus, Trash2, Webhook } from "lucide-react";

interface WebhookEndpoint {
  id: string;
  url: string;
  description?: string;
  secret: string;
  events: string[];
  is_active: boolean;
  created_at: string;
}

export const WebhooksView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [revealedSecrets, setRevealedSecrets] = useState<Record<string, boolean>>({});

  // Form states
  const [newUrl, setNewUrl] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newEvents, setNewEvents] = useState("project.created, task.completed");

  const fetchWebhooks = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<WebhookEndpoint[]>(
        `/api/v1/workspaces/${activeWorkspace.id}/webhooks`
      );
      setEndpoints(res.data);
    } catch (err) {
      console.error("Erro ao carregar webhooks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWebhooks();
  }, [activeWorkspace?.id]);

  const handleCreateWebhook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !newUrl.trim()) return;

    const eventsList = newEvents
      .split(",")
      .map((ev) => ev.trim())
      .filter(Boolean);

    try {
      await AXIOS_INSTANCE.post(`/api/v1/workspaces/${activeWorkspace.id}/webhooks`, {
        url: newUrl,
        description: newDesc || null,
        events: eventsList.length > 0 ? eventsList : ["*"],
      });
      setNewUrl("");
      setNewDesc("");
      setIsCreating(false);
      fetchWebhooks();
    } catch (err) {
      console.error("Erro ao cadastrar webhook:", err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!activeWorkspace) return;
    if (!confirm("Tem certeza que deseja desativar este webhook?")) return;
    try {
      await AXIOS_INSTANCE.delete(`/api/v1/workspaces/${activeWorkspace.id}/webhooks/${id}`);
      fetchWebhooks();
    } catch (err) {
      console.error(err);
    }
  };

  const toggleSecret = (id: string) => {
    setRevealedSecrets((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Webhook className="h-6 w-6 text-primary" />
            Webhooks Outbound
          </h2>
          <p className="text-sm text-muted-foreground">
            Despacho assíncrono via Arq com assinatura HMAC-SHA256 e proteção anti-replay.
          </p>
        </div>

        <Button onClick={() => setIsCreating(!isCreating)} className="gap-2">
          <Plus className="h-4 w-4" />
          Novo Endpoint
        </Button>
      </div>

      {isCreating && (
        <Card className="border-primary/40 bg-card/60 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-lg">Cadastrar Endpoint de Webhook</CardTitle>
            <CardDescription>
              O SoftForge enviará requisições HTTP POST com o cabeçalho <code>X-SoftForge-Signature</code>.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateWebhook} className="space-y-4 max-w-lg">
              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">URL de Destino</label>
                <Input
                  type="url"
                  placeholder="https://api.seuservico.com/webhooks"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  required
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">Descrição</label>
                <Input
                  placeholder="Ex: Disparador de pipeline de CI/CD"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">
                  Eventos Assinados (separados por vírgula)
                </label>
                <Input
                  value={newEvents}
                  onChange={(e) => setNewEvents(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit">Cadastrar Endpoint</Button>
                <Button type="button" variant="outline" onClick={() => setIsCreating(false)}>
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
      ) : endpoints.length === 0 ? (
        <Card className="text-center py-12 border-dashed">
          <CardContent className="space-y-2">
            <Webhook className="h-10 w-10 text-muted-foreground mx-auto" />
            <p className="text-sm font-medium text-muted-foreground">
              Nenhum endpoint de webhook configurado.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {endpoints.map((ep) => {
            const isSecretVisible = !!revealedSecrets[ep.id];
            return (
              <Card key={ep.id} className="hover:border-primary/40 transition-colors">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-sm font-mono truncate">{ep.url}</CardTitle>
                        <Badge variant={ep.is_active ? "secondary" : "outline"} className="text-[10px]">
                          {ep.is_active ? "Ativo" : "Inativo"}
                        </Badge>
                      </div>
                      {ep.description && (
                        <CardDescription className="text-xs">{ep.description}</CardDescription>
                      )}
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(ep.id)}
                      className="h-8 text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-xs text-muted-foreground">Eventos:</span>
                    {ep.events.map((ev) => (
                      <Badge key={ev} variant="outline" className="font-mono text-[10px]">
                        {ev}
                      </Badge>
                    ))}
                  </div>

                  <div className="flex items-center justify-between bg-muted/40 p-2 rounded text-xs">
                    <span className="text-muted-foreground">Chave Secreta HMAC:</span>
                    <div className="flex items-center gap-2">
                      <code className="font-mono">
                        {isSecretVisible ? ep.secret : "••••••••••••••••••••••••••••••••"}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => toggleSecret(ep.id)}
                      >
                        {isSecretVisible ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
