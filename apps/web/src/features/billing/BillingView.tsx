import React, { useEffect, useState } from "react";
import { AXIOS_INSTANCE } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useWorkspaces } from "@/features/workspaces/WorkspaceContext";
import { Check, CheckCircle2, Copy, CreditCard, QrCode, Shield, Zap } from "lucide-react";

interface Plan {
  id: string;
  name: string;
  slug: string;
  price_cents: number;
  billing_cycle: string;
  max_projects: number;
  max_members: number;
  features: string[];
}

interface Subscription {
  id: string;
  status: string;
  plan_slug: string;
  current_period_end?: string;
}

interface PixCheckoutResponse {
  checkout_id: string;
  qr_code?: string;
  qr_code_base64?: string;
  status: string;
}

export const BillingView: React.FC = () => {
  const { activeWorkspace } = useWorkspaces();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [pixModalData, setPixModalData] = useState<PixCheckoutResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchBillingData = async () => {
    if (!activeWorkspace) return;
    setLoading(true);
    try {
      const [plansRes, subRes] = await Promise.all([
        AXIOS_INSTANCE.get<Plan[]>("/api/v1/billing/plans"),
        AXIOS_INSTANCE.get<Subscription>(`/api/v1/billing/workspaces/${activeWorkspace.id}/subscription`).catch(
          () => ({ data: null })
        ),
      ]);
      setPlans(plansRes.data);
      if (subRes.data) {
        setSubscription(subRes.data);
      }
    } catch (err) {
      console.error("Erro ao carregar planos de billing:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBillingData();
  }, [activeWorkspace?.id]);

  const handleCheckout = async (planSlug: string) => {
    if (!activeWorkspace) return;
    setCheckoutLoading(true);
    try {
      const res = await AXIOS_INSTANCE.post<PixCheckoutResponse>(
        `/api/v1/billing/workspaces/${activeWorkspace.id}/checkout`,
        {
          plan_slug: planSlug,
          payment_method: "pix",
        }
      );
      setPixModalData(res.data);
    } catch (err) {
      console.error("Erro ao processar checkout:", err);
    } finally {
      setCheckoutLoading(false);
    }
  };

  const copyPixCode = () => {
    if (pixModalData?.qr_code) {
      navigator.clipboard.writeText(pixModalData.qr_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <CreditCard className="h-6 w-6 text-primary" />
          Planos & Assinaturas
        </h2>
        <p className="text-sm text-muted-foreground">
          Gerencie o faturamento do seu Workspace com Pix transparente via Mercado Pago e controle de quotas.
        </p>
      </div>

      {/* Modal / Card de Checkout Pix */}
      {pixModalData && (
        <Card className="border-primary/50 bg-primary/5 shadow-md">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2 text-primary">
                <QrCode className="h-5 w-5" />
                Pague com Pix Instantâneo
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setPixModalData(null)}>
                Fechar
              </Button>
            </div>
            <CardDescription>
              Escaneie o QR Code no aplicativo do seu banco ou use a chave Copia e Cola para liberação imediata.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col md:flex-row items-center gap-6">
            <div className="bg-white p-3 rounded-lg border shadow-sm flex items-center justify-center w-48 h-48 shrink-0">
              {pixModalData.qr_code_base64 ? (
                <img
                  src={`data:image/png;base64,${pixModalData.qr_code_base64}`}
                  alt="QR Code Pix"
                  className="w-full h-full object-contain"
                />
              ) : (
                <div className="text-center p-4">
                  <QrCode className="w-16 h-16 text-primary mx-auto mb-2" />
                  <span className="text-[10px] text-muted-foreground">Pix Transparente SoftForge</span>
                </div>
              )}
            </div>

            <div className="space-y-3 w-full">
              <label className="text-xs font-semibold uppercase text-muted-foreground">
                Código Copia e Cola
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value={pixModalData.qr_code || "00020126580014br.gov.bcb.pix0136softforge-checkout-demo"}
                  className="w-full font-mono text-xs bg-background border rounded px-3 py-2"
                />
                <Button onClick={copyPixCode} variant="outline" className="shrink-0 gap-1.5">
                  {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                  {copied ? "Copiado!" : "Copiar"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <Shield className="h-3.5 w-3.5 text-primary" />
                Pagamento seguro e processado com baixa latência pelo gateway do framework.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => {
            const isCurrent = subscription?.plan_slug === plan.slug;
            const priceFormatted = (plan.price_cents / 100).toLocaleString("pt-BR", {
              style: "currency",
              currency: "BRL",
            });

            return (
              <Card
                key={plan.id}
                className={`relative flex flex-col justify-between transition-shadow hover:shadow-md ${
                  isCurrent ? "border-primary shadow-sm" : ""
                }`}
              >
                {isCurrent && (
                  <Badge className="absolute -top-3 right-4 bg-primary text-primary-foreground">
                    Plano Ativo
                  </Badge>
                )}
                <CardHeader>
                  <CardTitle className="text-xl font-bold">{plan.name}</CardTitle>
                  <CardDescription className="text-xs">
                    {plan.slug === "enterprise"
                      ? "Escalabilidade máxima para operações corporativas com IA."
                      : plan.slug === "pro"
                      ? "Ideal para startups e times em crescimento acelerado."
                      : "Para projetos individuais e prototipagem ágil."}
                  </CardDescription>
                  <div className="mt-4">
                    <span className="text-3xl font-extrabold tracking-tight">{priceFormatted}</span>
                    <span className="text-xs text-muted-foreground ml-1">/mês</span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2 border-t pt-4 text-xs">
                    <div className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      <span>Até {plan.max_projects} Projetos simultâneos</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      <span>Até {plan.max_members} Membros na equipe</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      <span>Integração de Contratos OpenAPI 3.1</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary shrink-0" />
                      <span>Webhooks & Notificações WebSocket</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button
                    className="w-full gap-2"
                    variant={isCurrent ? "outline" : "default"}
                    disabled={isCurrent || checkoutLoading}
                    onClick={() => handleCheckout(plan.slug)}
                  >
                    {isCurrent ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-primary" />
                        Plano Atual
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4" />
                        Assinar via Pix
                      </>
                    )}
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};
