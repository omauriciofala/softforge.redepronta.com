import React, { useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth, type User } from "./AuthContext";

export interface AuthFormsProps {
  onOpenDocs?: () => void;
}

export const AuthForms: React.FC<AuthFormsProps> = ({ onOpenDocs }) => {
  const { login } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Limpa qualquer token residual ou inválido antes da tentativa de login
      localStorage.removeItem("softforge_access_token");

      if (isRegister) {
        await AXIOS_INSTANCE.post("/api/v1/auth/register", {
          email,
          password,
          full_name: fullName,
        });
      }

      // Realiza login
      const loginRes = await AXIOS_INSTANCE.post<{ access_token: string }>("/api/v1/auth/login", {
        email,
        password,
      });

      const token = loginRes.data.access_token;
      localStorage.setItem("softforge_access_token", token);

      const meRes = await AXIOS_INSTANCE.get<User>("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });

      login(token, meRes.data);
    } catch (err: any) {
      localStorage.removeItem("softforge_access_token");
      const msg = err.response?.data?.message || "Ocorreu um erro na autenticação.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg border-border">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary font-bold text-xl">
            ⚡
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">
            {isRegister ? "Criar conta no SoftForge" : "Bem-vindo ao SoftForge"}
          </CardTitle>
          <CardDescription>
            {isRegister
              ? "Preencha seus dados para iniciar seu espaço no framework"
              : "Entre com suas credenciais para acessar seus projetos"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium border border-destructive/20">
                {error}
              </div>
            )}

            {isRegister && (
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Nome Completo</label>
                <Input
                  type="text"
                  placeholder="Seu nome ou nome do agente"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-sm font-medium">E-mail</label>
              <Input
                type="email"
                placeholder="dev@softforge.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-sm font-medium">Senha</label>
              <Input
                type="password"
                placeholder="Mínimo 8 caracteres"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Processando..." : isRegister ? "Registrar e Entrar" : "Entrar na Plataforma"}
            </Button>

            <div className="text-center pt-2 space-y-2">
              <button
                type="button"
                className="text-sm text-primary hover:underline block w-full"
                onClick={() => {
                  setIsRegister(!isRegister);
                  setError(null);
                }}
              >
                {isRegister
                  ? "Já possui uma conta? Faça login"
                  : "Não possui uma conta? Registre-se agora"}
              </button>

              {onOpenDocs && (
                <button
                  type="button"
                  className="text-xs text-muted-foreground hover:text-foreground inline-flex items-center gap-1 pt-2 border-t w-full justify-center"
                  onClick={onOpenDocs}
                >
                  <span>📖</span> Acessar Manual do Framework & Docs
                </button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
