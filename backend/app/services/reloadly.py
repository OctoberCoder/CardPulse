import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings


class ReloadlyClient:
    """Real Reloadly API client. Uses OAuth2 client credentials."""

    def __init__(self):
        self.settings = get_settings()
        self._base_url = "https://api.reloadly.com"
        self._token = None

    async def _get_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self._base_url}/o/token", json={
                "client_id": self.settings.reloadly_client_id,
                "client_secret": self.settings.reloadly_client_secret,
                "grant_type": "client_credentials",
                "audience": "https://api.reloadly.com",
            })
            resp.raise_for_status()
            return resp.json()["access_token"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def _request(self, method: str, path: str, **kwargs):
        if not self._token:
            self._token = await self._get_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method, f"{self._base_url}{path}",
                headers=headers, **kwargs, timeout=30.0,
            )
            if resp.status_code == 401:
                self._token = await self._get_token()
                headers["Authorization"] = f"Bearer {self._token}"
                resp = await client.request(
                    method, f"{self._base_url}{path}",
                    headers=headers, **kwargs, timeout=30.0,
                )
            resp.raise_for_status()
            return resp.json()

    async def list_products(self, page: int = 1, size: int = 50) -> list[dict]:
        return await self._request("GET", f"/gift-cards/products?page={page}&size={size}")

    async def get_product(self, product_id: int) -> dict:
        return await self._request("GET", f"/gift-cards/products/{product_id}")

    async def place_order(self, product_id: int, quantity: int, recipient_email: str) -> dict:
        return await self._request("POST", "/gift-cards/orders", json={
            "productId": product_id,
            "quantity": quantity,
            "recipientEmail": recipient_email,
        })

    async def check_order(self, order_id: str) -> dict:
        return await self._request("GET", f"/gift-cards/orders/{order_id}")

    async def get_balance(self) -> dict:
        return await self._request("GET", "/gift-cards/balance")


class MockReloadlyClient:
    """For testing / development without a real Reloadly account."""

    async def list_products(self, page: int = 1, size: int = 50) -> list[dict]:
        return [
            {"id": 1, "productName": "Amazon $100", "targetCurrency": "USD",
             "fixedRecipientDenominations": [100], "senderFee": 0.5, "distributorFee": 0.0},
            {"id": 2, "productName": "Apple $50", "targetCurrency": "USD",
             "fixedRecipientDenominations": [50], "senderFee": 0.3, "distributorFee": 0.0},
        ]

    async def get_product(self, product_id: int) -> dict:
        return {"id": product_id, "productName": f"Product {product_id}", "targetCurrency": "USD",
                "fixedRecipientDenominations": [100], "senderFee": 0.5}

    async def place_order(self, product_id: int, quantity: int, recipient_email: str) -> dict:
        return {"transactionId": 123, "status": "SUCCESSFUL"}

    async def check_order(self, order_id: str) -> dict:
        return {"transactionId": order_id, "status": "SUCCESSFUL"}

    async def get_balance(self) -> dict:
        return {"balance": 500.0}


def get_reloadly_client() -> ReloadlyClient | MockReloadlyClient:
    """Returns MockReloadlyClient when no credentials are configured."""
    settings = get_settings()
    if not settings.reloadly_client_id:
        return MockReloadlyClient()
    return ReloadlyClient()
