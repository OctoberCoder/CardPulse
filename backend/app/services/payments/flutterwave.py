import hashlib
import hmac
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from .base import PaymentGateway


class FlutterwaveClient(PaymentGateway):
    def __init__(self):
        self.settings = get_settings()
        self._base_url = "https://api.flutterwave.com/v3"
        self._secret_key = self.settings.flutterwave_secret_key
        self._webhook_hash = hashlib.sha256(self._secret_key.encode()).hexdigest()

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
        return await self._request("POST", "/payments", json={
            "tx_ref": reference,
            "amount": amount,
            "currency": "USD",
            "customer": {"email": email},
        })

    async def verify_payment(self, reference: str) -> dict:
        return await self._request("GET", f"/transactions/{reference}/verify")

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        return hmac.compare_digest(self._webhook_hash, signature)
