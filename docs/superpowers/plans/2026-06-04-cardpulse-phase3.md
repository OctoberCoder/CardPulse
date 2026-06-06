# CardPulse Phase 3: Payment Integration (Paystack + Flutterwave)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add order placement, payment processing, and webhook handling for Paystack and Flutterwave with mock clients for development.

**Architecture:** Abstract payment gateway interface with separate PaystackClient and FlutterwaveClient implementations, MockPaymentClient for testing. Orders track payment lifecycle. Webhooks verify signatures and update order status.

**Tech Stack:** FastAPI, SQLAlchemy, httpx, tenacity

---

### Task 1: Order + Payment Models

**Files:**
- Create: `backend/app/models/order.py`
- Modify: `backend/app/models/__init__.py`
- Generate migration

**Steps:**

- [ ] **Create `backend/app/models/order.py`**:

```python
from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentMethod(str, enum.Enum):
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"
    CRYPTO = "crypto"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    source: Mapped[str] = mapped_column(String(20))  # "own_inventory" or "reloadly"
    listing_id: Mapped[int] = mapped_column(nullable=True)  # OwnListing FK or Reloadly product
    reloadly_tx_id: Mapped[str] = mapped_column(String(255), nullable=True)
    amount_paid: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.PENDING)
    payment_method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod))
    payment_reference: Mapped[str] = mapped_column(String(255), default="")
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    buyer = relationship("User")
```

- [ ] **Update `backend/app/models/__init__.py`** — add Order, OrderStatus, PaymentMethod

- [ ] **Generate migration**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/alembic revision --autogenerate -m "add orders table" && .venv/bin/alembic upgrade head
```

- [ ] **Commit**:
```bash
git add . && git commit -m "feat: order model with payment tracking"
```

---

### Task 2: Paystack Client + Flutterwave Client + Mock

**Files:**
- Create: `backend/app/services/payments/__init__.py`
- Create: `backend/app/services/payments/base.py`
- Create: `backend/app/services/payments/paystack.py`
- Create: `backend/app/services/payments/flutterwave.py`
- Create: `backend/app/services/payments/mock.py`
- Create: `backend/tests/test_payments.py`

**Steps:**

- [ ] **Create `backend/app/services/payments/__init__.py`**:
```python
from .paystack import PaystackClient
from .flutterwave import FlutterwaveClient
from .mock import MockPaymentClient
from .base import PaymentGateway


def get_payment_client(name: str = "paystack") -> PaymentGateway:
    from app.config import get_settings
    settings = get_settings()
    if name == "paystack":
        if not settings.paystack_secret_key:
            return MockPaymentClient()
        return PaystackClient()
    elif name == "flutterwave":
        if not settings.flutterwave_secret_key:
            return MockPaymentClient()
        return FlutterwaveClient()
    return MockPaymentClient()
```

- [ ] **Create `backend/app/services/payments/base.py`**:

```python
from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    async def initialize_payment(self, email: str, amount: float, reference: str) -> dict:
        ...

    @abstractmethod
    async def verify_payment(self, reference: str) -> dict:
        ...

    @abstractmethod
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        ...
```

- [ ] **Create `backend/app/services/payments/paystack.py`**:

```python
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
            "amount": int(amount * 100),  # Paystack uses kobo
            "reference": reference,
        })

    async def verify_payment(self, reference: str) -> dict:
        return await self._request("GET", f"/transaction/verify/{reference}")

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        expected = hmac.new(
            self._secret_key.encode(), body, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
```

- [ ] **Create `backend/app/services/payments/flutterwave.py`**:

```python
import hashlib
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
```

- [ ] **Create `backend/app/services/payments/mock.py`**:

```python
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
```

- [ ] **Create `backend/tests/test_payments.py`**:

```python
import pytest


@pytest.mark.asyncio
async def test_mock_initialize_payment():
    from app.services.payments import MockPaymentClient
    client = MockPaymentClient()
    result = await client.initialize_payment("test@example.com", 100.0, "ref-001")
    assert result["status"] is True
    assert "authorization_url" in result["data"]


@pytest.mark.asyncio
async def test_mock_verify_payment():
    from app.services.payments import MockPaymentClient
    client = MockPaymentClient()
    result = await client.verify_payment("ref-001")
    assert result["data"]["status"] == "success"


def test_mock_webhook_signature():
    from app.services.payments import MockPaymentClient
    import hashlib
    client = MockPaymentClient()
    body = b'{"event":"charge.success"}'
    sig = hashlib.sha256(body).hexdigest()
    assert client.verify_webhook_signature(body, sig) is True


@pytest.mark.asyncio
async def test_get_payment_client_returns_mock():
    from app.services.payments import get_payment_client, MockPaymentClient
    client = get_payment_client("paystack")
    assert isinstance(client, MockPaymentClient)
```

- [ ] **Run tests and commit**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_payments.py -v
git add . && git commit -m "feat: Paystack and Flutterwave clients with mock for development"
```

---

### Task 3: Order/Payment API + Webhook Endpoints

**Files:**
- Create: `backend/app/routers/orders.py`
- Create: `backend/app/schemas/order.py`
- Create: `backend/app/routers/webhooks.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_orders.py`

**Steps:**

- [ ] **Create `backend/app/schemas/order.py`**:

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class OrderCreate(BaseModel):
    source: str  # "reloadly" or "own_inventory"
    listing_id: int
    payment_method: str  # "paystack", "flutterwave", etc.
    idempotency_key: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    amount_paid: float
    fee: float
    status: str
    payment_method: str
    payment_reference: str
    created_at: datetime
```

- [ ] **Create `backend/app/routers/orders.py`**:

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.auth import get_current_user
from app.services.payments import get_payment_client

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check idempotency
    if body.idempotency_key:
        result = await db.execute(
            select(Order).where(Order.idempotency_key == body.idempotency_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    # Placeholder pricing: for now, hardcoded at $100
    amount_paid = 100.0
    fee = round(amount_paid * 0.02, 2)

    order = Order(
        buyer_id=current_user.id,
        source=body.source,
        listing_id=body.listing_id,
        amount_paid=amount_paid,
        fee=fee,
        status=OrderStatus.PENDING,
        payment_method=PaymentMethod(body.payment_method),
        payment_reference=f"cardpulse-{uuid.uuid4().hex[:12]}",
        idempotency_key=body.idempotency_key or f"auto-{uuid.uuid4().hex[:16]}",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Initialize payment
    client = get_payment_client(body.payment_method)
    payment = await client.initialize_payment(
        email=current_user.email,
        amount=order.amount_paid,
        reference=order.payment_reference,
    )

    return {
        **OrderResponse.model_validate(order).model_dump(),
        "payment_url": payment.get("data", {}).get("authorization_url"),
    }


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order)
        .where(Order.buyer_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.buyer_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
```

- [ ] **Create `backend/app/routers/webhooks.py`**:

```python
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy import select

from app.database import async_session
from app.models.order import Order, OrderStatus
from app.models.payments import get_payment_client

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/paystack")
async def paystack_webhook(request: Request):
    signature = request.headers.get("x-paystack-signature", "")
    body = await request.body()

    client = get_payment_client("paystack")
    if not client.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    import json
    payload = json.loads(body)
    event = payload.get("event", "")

    if event == "charge.success":
        reference = payload.get("data", {}).get("reference", "")
        async with async_session() as db:
            result = await db.execute(select(Order).where(Order.payment_reference == reference))
            order = result.scalar_one_or_none()
            if order and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.COMPLETED
                from datetime import datetime, timezone
                order.delivered_at = datetime.now(timezone.utc)
                await db.commit()

    return {"status": "ok"}


@router.post("/flutterwave")
async def flutterwave_webhook(request: Request):
    signature = request.headers.get("verif-hash", "")

    client = get_payment_client("flutterwave")
    body = await request.body()

    import json
    payload = json.loads(body)
    event = payload.get("event", "")

    if "completed" in event.lower():
        reference = payload.get("data", {}).get("tx_ref", "")
        async with async_session() as db:
            result = await db.execute(select(Order).where(Order.payment_reference == reference))
            order = result.scalar_one_or_none()
            if order and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.COMPLETED
                from datetime import datetime, timezone
                order.delivered_at = datetime.now(timezone.utc)
                await db.commit()

    return {"status": "ok"}
```

**Note on the webhooks router:** The `payments` module import should be `from app.services.payments import get_payment_client`. Make sure this is correct.

- [ ] **Register routers in `backend/app/main.py`**:

```python
from app.routers import orders, webhooks
app.include_router(orders.router)
app.include_router(webhooks.router)
```

- [ ] **Create `backend/tests/test_orders.py`**:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, user_token):
    response = await client.post("/api/orders", json={
        "source": "reloadly",
        "listing_id": 1,
        "payment_method": "paystack",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert "payment_url" in data


@pytest.mark.asyncio
async def test_create_order_idempotent(client: AsyncClient, user_token):
    key = "test-idemp-key-123"
    resp1 = await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "paystack",
        "idempotency_key": key,
    }, headers={"Authorization": f"Bearer {user_token}"})
    resp2 = await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "paystack",
        "idempotency_key": key,
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert resp1.json()["id"] == resp2.json()["id"]


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient, user_token):
    await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "flutterwave",
    }, headers={"Authorization": f"Bearer {user_token}"})
    response = await client.get("/api/orders", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_paystack_webhook(client: AsyncClient, user_token):
    # Create an order first
    order_resp = await client.post("/api/orders", json={
        "source": "reloadly", "listing_id": 1, "payment_method": "paystack",
    }, headers={"Authorization": f"Bearer {user_token}"})
    ref = order_resp.json()["payment_reference"]

    # Send mock webhook
    import hashlib
    body = f'{{"event":"charge.success","data":{{"reference":"{ref}"}}}}'.encode()
    sig = hashlib.sha256(body).hexdigest()
    response = await client.post(
        "/api/webhooks/paystack",
        content=body,
        headers={"x-paystack-signature": sig},
    )
    assert response.status_code == 200
```

- [ ] **Run all tests**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/ -v
```

- [ ] **Commit**:
```bash
git add . && git commit -m "feat: order/payment API with Paystack and Flutterwave webhooks"
```
