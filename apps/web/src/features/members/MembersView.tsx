import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import { Mail, Plus, UserCheck, Users } from "lucide-react";

interface Member {
  id: string;
  user_id: string;
  role: string;
  user?: {
    full_name: string;
    email: string;
  };
}

interface Invite {
  id: string;
  email: string;
  role: string;
  token: string;
  status: string;
  expires_at: string;
}

export const MembersView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
  const [loading, setLoading] = useState(false);
  const [isInviting, setIsInviting] = useState(false);

  // Form states
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");

  const fetchMembersAndInvites = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const [membersRes, invitesRes] = await Promise.all([
        AXIOS_INSTANCE.get<Member[] | { items: Member[] }>(`/api/v1/workspaces/${activeWorkspace.id}/members`),
        AXIOS_INSTANCE.get<Invite[] | { items: Invite[] }>(`/api/v1/workspaces/${activeWorkspace.id}/invites`).catch(
          () => ({ data: [] })
        ),
      ]);
      const membersData = Array.isArray(membersRes.data)
        ? membersRes.data
        : (membersRes.data as any)?.items || [];
      const invitesData = Array.isArray(invitesRes.data)
        ? invitesRes.data
        : (invitesRes.data as any)?.items || [];
      setMembers(membersData);
      setInvites(invitesData);
    } catch (err) {
      console.error("Erro ao carregar membros do workspace:", err);
      setMembers([]);
      setInvites([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembersAndInvites();
  }, [activeWorkspace?.id]);

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeWorkspace || !inviteEmail.trim()) return;

    try {
      await AXIOS_INSTANCE.post(`/api/v1/workspaces/${activeWorkspace.id}/invites`, {
        email: inviteEmail,
        role: inviteRole,
      });
      setInviteEmail("");
      setIsInviting(false);
      fetchMembersAndInvites();
    } catch (err) {
      console.error("Erro ao enviar convite:", err);
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "owner":
        return <Badge className="bg-purple-600 text-white text-[10px] uppercase font-mono">Owner</Badge>;
      case "admin":
        return <Badge className="bg-blue-600 text-white text-[10px] uppercase font-mono">Admin</Badge>;
      case "member":
        return <Badge variant="secondary" className="text-[10px] uppercase font-mono">Member</Badge>;
      default:
        return <Badge variant="outline" className="text-[10px] uppercase font-mono">Viewer</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-6 w-6 text-primary" />
            Equipe & Controle de Acesso (RBAC)
          </h2>
          <p className="text-sm text-muted-foreground">
            Gerencie os membros da sua organização e envie convites por e-mail com tokens de 7 dias.
          </p>
        </div>

        <Button onClick={() => setIsInviting(!isInviting)} className="gap-2">
          <Plus className="h-4 w-4" />
          Convidar Membro
        </Button>
      </div>

      {isInviting && (
        <Card className="border-primary/40 bg-card/60 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-lg">Enviar Convite de Adesão</CardTitle>
            <CardDescription>
              Um link assinado com validade de 7 dias será despachado via fila assíncrona Arq.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSendInvite} className="space-y-4 max-w-lg">
              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">E-mail do Convidado</label>
                <Input
                  type="email"
                  placeholder="colega@empresa.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase text-muted-foreground">Papel (Cargo RBAC)</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full mt-1 bg-background border rounded-md px-3 py-2 text-xs font-medium focus:ring-1 focus:ring-primary focus:outline-none"
                >
                  <option value="viewer">Viewer (Apenas visualização de recursos)</option>
                  <option value="member">Member (Criação e edição de projetos)</option>
                  <option value="admin">Admin (Gestão de temas, webhooks e faturamento)</option>
                </select>
              </div>

              <div className="flex gap-2">
                <Button type="submit">Despachar Convite</Button>
                <Button type="button" variant="outline" onClick={() => setIsInviting(false)}>
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Tabela de Membros Ativos */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <UserCheck className="h-5 w-5 text-primary" />
            Membros Ativos ({members.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted/50 border-b text-muted-foreground uppercase font-semibold text-[11px]">
                <tr>
                  <th className="py-3 px-4">Nome</th>
                  <th className="py-3 px-4">E-mail</th>
                  <th className="py-3 px-4">Papel RBAC</th>
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={4} className="text-center py-8">
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent mx-auto" />
                    </td>
                  </tr>
                ) : (
                  members.map((m) => (
                  <tr key={m.id} className="hover:bg-muted/20 transition-colors">
                    <td className="py-3 px-4 font-semibold text-foreground">
                      {m.user?.full_name || "Membro"}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">{m.user?.email}</td>
                    <td className="py-3 px-4">{getRoleBadge(m.role)}</td>
                    <td className="py-3 px-4">
                      <Badge variant="outline" className="text-[10px] text-green-600 border-green-300">
                        Ativo
                      </Badge>
                    </td>
                  </tr>
                )))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Convites Pendentes */}
      {invites.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Mail className="h-5 w-5 text-muted-foreground" />
              Convites Pendentes ({invites.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/50 border-b text-muted-foreground uppercase font-semibold text-[11px]">
                  <tr>
                    <th className="py-3 px-4">E-mail Convidado</th>
                    <th className="py-3 px-4">Papel Proposto</th>
                    <th className="py-3 px-4">Expiração</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {invites.map((inv) => (
                    <tr key={inv.id} className="hover:bg-muted/20 transition-colors">
                      <td className="py-3 px-4 font-semibold text-foreground">{inv.email}</td>
                      <td className="py-3 px-4">{getRoleBadge(inv.role)}</td>
                      <td className="py-3 px-4 text-muted-foreground">
                        {new Date(inv.expires_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="secondary" className="text-[10px]">
                          {inv.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
