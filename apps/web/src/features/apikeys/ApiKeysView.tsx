import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import { AlertTriangle, Check, Copy, Key, Plus } from "lucide-react";

interface ApiKeyItem {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  expires_at?: string;
  last_used_at?: string;
  is_revoked: boolean;
  created_at: string;
}

interface NewKeyCreated {
  id: string;
  name: string;
  raw_key: string;
  key_prefix: string;
}

export const ApiKeysView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKeyData, setCreatedKeyData] = useState<NewKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchKeys = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const res = await AXIOS_INSTANCE.get<ApiKeyItem[]>(
        `/api/v1/workspaces/${activeWorkspace.id}/api-keys`
      );
      setKeys(res.data);
    } catch (err) {
      console.error("Erro ao carregar chaves de API:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, [activeWorkspace?.id]);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !newKeyName.trim()) return;

    try {
      const res = await AXIOS_INSTANCE.post<NewKeyCreated>(
        `/api/v1/workspaces/${activeWorkspace.id}/api-keys`,
        {
          name: newKeyName,
          scopes: ["read", "write"],
          expires_in_days: 90,
        }
      );
      setCreatedKeyData(res.data);
      setNewKeyName("");
      setIsCreating(false);
      fetchKeys();
    } catch (err) {
      console.error("Erro ao gerar chave de API:", err);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!activeWorkspace) return;
    if (!confirm("Revogar esta chave de API imediatamente? Essa ação não pode ser desfeita.")) return;

    try {
      await AXIOS_INSTANCE.delete(`/api/v1/workspaces/${activeWorkspace.id}/api-keys/${keyId}`);
      fetchKeys();
    } catch (err) {
      console.error(err);
    }
  };

  const copyRawKey = () => {
    if (createdKeyData?.raw_key) {
      navigator.clipboard.writeText(createdKeyData.raw_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Key className="h-6 w-6 text-primary" />
            Chaves de API & Tokens PAT
          </h2>
          <p className="text-sm text-muted-foreground">
            Autenticação Machine-to-Machine para agentes externos de IA, scripts e pipelines CI/CD.
          </p>
        </div>

        <Button onClick={() => setIsCreating(!isCreating)} className="gap-2">
          <Plus className="h-4 w-4" />
          Gerar Chave de API
        </Button>
      </div>

      {/* Alerta de Chave Recém-Criada */}
      {createdKeyData && (
        <Card className="border-yellow-500/50 bg-yellow-500/10 shadow-md">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2 text-yellow-700 dark:text-yellow-400">
                <AlertTriangle className="h-5 w-5" />
                Guarde sua Chave de API Agora
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setCreatedKeyData(null)}>
                Entendido
              </Button>
            </div>
            <CardDescription className="text-xs">
              Por motivos de segurança com hash SHA-256 no banco, esta chave <strong>não será exibida novamente</strong>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={createdKeyData.raw_key}
                className="w-full font-mono text-xs bg-background border rounded px-3 py-2 select-all"
              />
              <Button onClick={copyRawKey} variant="default" className="shrink-0 gap-1.5">
                {copied ? <Check className="h-4 w-4 text-green-300" /> : <Copy className="h-4 w-4" />}
                {copied ? "Copiado!" : "Copiar Chave"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isCreating && (
        <Card className="border-primary/40 bg-card/60 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-lg">Gerar Nova Chave de Acesso</CardTitle>
            <CardDescription>
              As chaves concedem acesso total ou granular à API do tenant no cabeçalho <code>Authorization: Bearer &lt;key&gt;</code>.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateKey} className="space-y-4 max-w-lg">
              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">Nome Identificador</label>
                <Input
                  placeholder="Ex: Agente Autônomo Claude / GitHub Actions"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                  className="mt-1"
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit">Gerar Chave</Button>
                <Button type="button" variant="outline" onClick={() => setIsCreating(false)}>
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/50 border-b text-muted-foreground uppercase font-semibold text-[11px]">
                <tr>
                  <th className="py-3 px-4">Nome</th>
                  <th className="py-3 px-4">Prefixo Mascarado</th>
                  <th className="py-3 px-4">Escopos</th>
                  <th className="py-3 px-4">Criada em</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Ação</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto" />
                    </td>
                  </tr>
                ) : keys.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-muted-foreground">
                      Nenhuma chave de API gerada.
                    </td>
                  </tr>
                ) : (
                  keys.map((k) => (
                    <tr key={k.id} className="hover:bg-muted/20 transition-colors">
                      <td className="py-3 px-4 font-semibold text-foreground">{k.name}</td>
                      <td className="py-3 px-4 font-mono text-muted-foreground">
                        {k.key_prefix}...••••••••
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-1">
                          {k.scopes.map((s) => (
                            <Badge key={s} variant="outline" className="text-[10px]">
                              {s}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {new Date(k.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={k.is_revoked ? "destructive" : "secondary"}
                          className="text-[10px]"
                        >
                          {k.is_revoked ? "Revogada" : "Ativa"}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        {!k.is_revoked && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRevokeKey(k.id)}
                            className="h-7 text-xs text-destructive hover:bg-destructive/10"
                          >
                            Revogar
                          </Button>
                        )}
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
