import uuid
from typing import Any, Protocol

from src.slices.billing.models import PaymentInvoice, PaymentMethod


class PaymentGateway(Protocol):
    """Protocolo agnóstico para provedores de pagamento."""

    async def create_charge(
        self,
        invoice: PaymentInvoice,
        payer_email: str,
        payer_cpf_cnpj: str | None = None,
    ) -> dict[str, Any]:
        ...

    async def fetch_payment_status(self, payment_id: str) -> dict[str, Any]:
        ...


class MercadoPagoGateway:
    """Adaptador de Pagamentos para Mercado Pago (Pix Transparente, Boleto e Cartão).

    Suporta operação em modo Sandbox/Mock para testes locais e modo live com Access Token.
    """

    def __init__(self, access_token: str | None = None) -> None:
        self.access_token = access_token
        self.is_live = bool(access_token and not access_token.startswith("TEST-MOCK"))

    async def create_charge(
        self,
        invoice: PaymentInvoice,
        payer_email: str,
        payer_cpf_cnpj: str | None = None,
    ) -> dict[str, Any]:
        if not self.is_live:
            # Geração Mock offline determinística para dev e testes locais
            fake_payment_id = f"mp_mock_{uuid.uuid4().hex[:12]}"
            amount_reais = invoice.amount_cents / 100.0

            if invoice.payment_method == PaymentMethod.PIX:
                return {
                    "provider_payment_id": fake_payment_id,
                    "status": "pending",
                    "pix_qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    "pix_copy_paste": f"00020126580014br.gov.bcb.pix0136{fake_payment_id}520400005303986540{amount_reais:.2f}5802BR5913SoftForge SaaS6009Sao Paulo62070503***6304ABCD",
                }
            elif invoice.payment_method == PaymentMethod.BOLETO:
                return {
                    "provider_payment_id": fake_payment_id,
                    "status": "pending",
                    "boleto_url": f"https://www.mercadopago.com.br/payments/{fake_payment_id}/ticket",
                    "boleto_barcode": "23793.38128 60000.000003 01000.000002 1 90000000004900",
                }
            else:
                return {
                    "provider_payment_id": fake_payment_id,
                    "status": "paid",
                }

        # Em produção com Access Token:
        import httpx

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "transaction_amount": invoice.amount_cents / 100.0,
                "description": f"SoftForge Assinatura - {invoice.subscription_id}",
                "payment_method_id": "pix" if invoice.payment_method == PaymentMethod.PIX else "bolbradesco",
                "payer": {
                    "email": payer_email,
                    "identification": {
                        "type": "CPF" if len(payer_cpf_cnpj or "") <= 11 else "CNPJ",
                        "number": payer_cpf_cnpj or "00000000000",
                    },
                },
            }
            resp = await client.post("https://api.mercadopago.com/v1/payments", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            point_of_interaction = data.get("point_of_interaction", {})
            transaction_data = point_of_interaction.get("transaction_data", {})

            return {
                "provider_payment_id": str(data.get("id")),
                "status": data.get("status", "pending"),
                "pix_qr_code": transaction_data.get("qr_code_base64"),
                "pix_copy_paste": transaction_data.get("qr_code"),
                "boleto_url": transaction_data.get("ticket_url"),
                "boleto_barcode": transaction_data.get("barcode"),
            }

    async def fetch_payment_status(self, payment_id: str) -> dict[str, Any]:
        if not self.is_live:
            return {"status": "approved", "id": payment_id}

        import httpx

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = await client.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
            resp.raise_for_status()
            return resp.json()
