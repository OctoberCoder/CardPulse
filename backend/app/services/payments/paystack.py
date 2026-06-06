import hashlib
import hmac
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from .base import PaymentGateway


class PaystackClient(PaymentGateway):
    def __init__(self):
        self.settings = get_settings()
        self._base_url = "https://api.paystack.co"
        self._secret_key = self.settings.paystack_secret_key

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def _request(self, method: str, path: str, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._secret_key}"
        headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method, f"{self._base_url}{path}",
                headers=headers, **kwargs, timeout=30.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def initialize_payment(self, email: str, amount: float, reference: str) -> dict:
        return await self._request("POST", "/transaction/initialize", json={
            "email": email,
            "amount": int(amount * 100),
            "reference": reference,
        })

    async def verify_payment(self, reference: str) -> dict:
        return await self._request("GET", f"/transaction/verify/{reference}")

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        expected = hmac.new(
            self._secret_key.encode(), body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
