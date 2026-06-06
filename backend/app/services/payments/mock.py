from .base import PaymentGateway
import hashlib


class MockPaymentClient(PaymentGateway):
    """For testing / development without real payment provider keys."""

    async def initialize_payment(self, email: str, amount: float, reference: str) -> dict:
        return {
            "status": True,
            "message": "Mock payment initialized",
            "data": {
                "authorization_url": f"https://mock-pay.cardpulse/authorize/{reference}",
                "reference": reference,
                "amount": amount,
            },
        }

    async def verify_payment(self, reference: str) -> dict:
        return {
            "status": True,
            "message": "Mock payment verified",
            "data": {"status": "success", "reference": reference},
        }

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        return signature == hashlib.sha256(body).hexdigest()
