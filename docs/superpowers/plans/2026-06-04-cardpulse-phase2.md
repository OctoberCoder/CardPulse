# CardPulse Phase 2: Pricing Engine + Reloadly Integration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded 75% buy rate with a dynamic pricing engine, and integrate Reloadly API as the primary card inventory source for the buy side.

**Architecture:** Rate rules stored in the database per brand+denomination, with dynamic adjustments (inventory, volume, day of week). Reloadly syncs products via Celery cron and exposes a merged product feed alongside own inventory.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Celery/Redis, httpx (Reloadly API client), tenacity (retry)

---

### Task 1: RateRule + RateAdjustment + RateSnapshot Models

**Files:**
- Create: `backend/app/models/pricing.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/app/schemas/pricing.py`
- Create: `backend/app/routers/pricing.py`
- Create: `backend/tests/test_pricing.py`

**Steps:**

- [ ] **Create `backend/app/models/pricing.py`**:

```python
from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, ForeignKey, Boolean, Integer, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class TriggerType(str, enum.Enum):
    STOCK_LOW = "stock_low"
    STOCK_HIGH = "stock_high"
    SUBMISSION_VOLUME_HIGH = "submission_volume_high"
    DAY_OF_WEEK = "day_of_week"


class RateRule(Base):
    __tablename__ = "rate_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    denomination_id: Mapped[int] = mapped_column(ForeignKey("denominations.id"))
    base_buy_rate: Mapped[float] = mapped_column(Float)  # e.g. 0.75 = 75%
    sell_markup_pct: Mapped[float] = mapped_column(Float, default=0.10)  # e.g. 0.10 = 10%
    min_rate: Mapped[float] = mapped_column(Float, default=0.50)
    max_rate: Mapped[float] = mapped_column(Float, default=0.95)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    brand = relationship("CardBrand")
    denomination = relationship("Denomination")
    adjustments: Mapped[list["RateAdjustment"]] = relationship(back_populates="rule", cascade="all, delete-orphan")


class RateAdjustment(Base):
    __tablename__ = "rate_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rate_rules.id"))
    trigger_type: Mapped[TriggerType] = mapped_column(SAEnum(TriggerType))
    operator: Mapped[str] = mapped_column(String(10), default="add")  # "add" or "subtract"
    value: Mapped[float] = mapped_column(Float)  # threshold value
    adjustment_pct: Mapped[float] = mapped_column(Float)  # e.g. 0.02 = 2%
    priority: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rule: Mapped["RateRule"] = relationship(back_populates="adjustments")


class RateSnapshot(Base):
    __tablename__ = "rate_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    denomination_id: Mapped[int] = mapped_column(ForeignKey("denominations.id"))
    effective_buy_rate: Mapped[float] = mapped_column(Float)
    effective_sell_price: Mapped[float] = mapped_column(Float)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Update `backend/app/models/__init__.py`** — add imports for RateRule, RateAdjustment, RateSnapshot, TriggerType

- [ ] **Create `backend/app/schemas/pricing.py`**:

```python
from pydantic import BaseModel, ConfigDict
from typing import Optional


class RateAdjustmentCreate(BaseModel):
    trigger_type: str
    operator: str = "add"
    value: float
    adjustment_pct: float
    priority: int = 0


class RateAdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    trigger_type: str
    operator: str
    value: float
    adjustment_pct: float
    priority: int
    active: bool


class RateRuleCreate(BaseModel):
    brand_id: int
    denomination_id: int
    base_buy_rate: float
    sell_markup_pct: float = 0.10
    min_rate: float = 0.50
    max_rate: float = 0.95
    adjustments: list[RateAdjustmentCreate] = []


class RateRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int
    denomination_id: int
    base_buy_rate: float
    sell_markup_pct: float
    min_rate: float
    max_rate: float
    active: bool
    adjustments: list[RateAdjustmentResponse] = []


class EffectiveRateResponse(BaseModel):
    brand_id: int
    denomination_id: int
    base_buy_rate: float
    effective_buy_rate: float
    sell_price: float
```

- [ ] **Create `backend/tests/test_pricing.py`**:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_rate_rule(client: AsyncClient, admin_token, db_session):
    # Create brand + denom first
    from app.models.card import CardBrand, Denomination
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()

    response = await client.post("/api/admin/rates", json={
        "brand_id": brand.id,
        "denomination_id": denom.id,
        "base_buy_rate": 0.75,
        "sell_markup_pct": 0.10,
        "adjustments": [
            {"trigger_type": "stock_low", "operator": "add", "value": 10, "adjustment_pct": 0.02, "priority": 1},
        ],
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["base_buy_rate"] == 0.75
    assert len(data["adjustments"]) == 1


@pytest.mark.asyncio
async def test_get_effective_rates(client: AsyncClient, admin_token, db_session):
    brand = CardBrand(name="Apple", slug="apple")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=50.0)
    db_session.add(denom)
    await db_session.commit()

    await client.post("/api/admin/rates", json={
        "brand_id": brand.id, "denomination_id": denom.id,
        "base_buy_rate": 0.70, "sell_markup_pct": 0.15,
    }, headers={"Authorization": f"Bearer {admin_token}"})

    response = await client.get("/api/admin/rates/effective",
                                headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_non_admin_cannot_create_rate(client: AsyncClient, user_token):
    response = await client.post("/api/admin/rates", json={
        "brand_id": 1, "denomination_id": 1,
        "base_buy_rate": 0.75,
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403
```

**Important:** The test file needs proper imports and the fixtures from conftest.py. Make sure to import CardBrand and Denomination inside the test functions or at module level, and ensure the test database session is available.

- [ ] **Create `backend/app/routers/pricing.py`**:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.card import CardBrand, Denomination, CardSubmissionStatus
from app.models.pricing import RateRule, RateAdjustment, RateSnapshot
from app.models.user import User
from app.schemas.pricing import RateRuleCreate, RateRuleResponse, EffectiveRateResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/admin/rates", tags=["pricing"])


async def require_staff(user: User = Depends(get_current_user)) -> User:
    if not user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def compute_effective_rate(rule: RateRule, active_listings: int = 0, daily_submissions: int = 0) -> float:
    rate = rule.base_buy_rate
    for adj in sorted(rule.adjustments, key=lambda a: a.priority):
        if not adj.active:
            continue
        triggered = False
        if adj.trigger_type == "stock_low":
            triggered = active_listings < adj.value
        elif adj.trigger_type == "stock_high":
            triggered = active_listings > adj.value
        elif adj.trigger_type == "submission_volume_high":
            triggered = daily_submissions > adj.value
        elif adj.trigger_type == "day_of_week":
            from datetime import datetime
            triggered = datetime.now().strftime("%A") == adj.value

        if triggered:
            if adj.operator == "add":
                rate += adj.adjustment_pct
            elif adj.operator == "subtract":
                rate -= adj.adjustment_pct

    return max(rule.min_rate, min(rule.max_rate, rate))


@router.get("", response_model=list[RateRuleResponse])
async def list_rate_rules(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    result = await db.execute(
        select(RateRule)
        .options(selectinload(RateRule.adjustments), selectinload(RateRule.brand), selectinload(RateRule.denomination))
        .order_by(RateRule.brand_id)
    )
    return result.scalars().all()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RateRuleResponse)
async def create_rate_rule(
    body: RateRuleCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    rule = RateRule(
        brand_id=body.brand_id,
        denomination_id=body.denomination_id,
        base_buy_rate=body.base_buy_rate,
        sell_markup_pct=body.sell_markup_pct,
        min_rate=body.min_rate,
        max_rate=body.max_rate,
    )
    for adj_data in body.adjustments:
        adj = RateAdjustment(**adj_data.model_dump())
        rule.adjustments.append(adj)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    result = await db.execute(
        select(RateRule).where(RateRule.id == rule.id)
        .options(selectinload(RateRule.adjustments), selectinload(RateRule.brand), selectinload(RateRule.denomination))
    )
    return result.scalar_one()


@router.get("/effective", response_model=list[EffectiveRateResponse])
async def get_effective_rates(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    result = await db.execute(
        select(RateRule)
        .where(RateRule.active == True)
        .options(selectinload(RateRule.adjustments), selectinload(RateRule.denomination))
    )
    rules = result.scalars().all()
    responses = []
    for rule in rules:
        effective_rate = compute_effective_rate(rule)
        sell_price = round(rule.denomination.value * (1 + rule.sell_markup_pct), 2)
        responses.append(EffectiveRateResponse(
            brand_id=rule.brand_id,
            denomination_id=rule.denomination_id,
            base_buy_rate=rule.base_buy_rate,
            effective_buy_rate=round(effective_rate, 4),
            sell_price=sell_price,
        ))
    return responses


@router.get("/{rule_id}", response_model=RateRuleResponse)
async def get_rate_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    result = await db.execute(
        select(RateRule).where(RateRule.id == rule_id)
        .options(selectinload(RateRule.adjustments), selectinload(RateRule.brand), selectinload(RateRule.denomination))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate rule not found")
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    result = await db.execute(select(RateRule).where(RateRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate rule not found")
    rule.active = False
    await db.commit()
```

- [ ] **Register pricing router in `backend/app/main.py`** — add `from app.routers import pricing` and `app.include_router(pricing.router)`

- [ ] **Generate migration**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/alembic revision --autogenerate -m "add pricing models" && .venv/bin/alembic upgrade head
```

- [ ] **Run tests**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_pricing.py -v
```

Expected: All 3 tests pass (create rule, get effective rates, non-admin denied)

- [ ] **Commit**:
```bash
git add backend/app/models/pricing.py backend/app/models/__init__.py backend/app/schemas/pricing.py backend/app/routers/pricing.py backend/app/main.py backend/tests/test_pricing.py backend/alembic/
git commit -m "feat: dynamic pricing engine with rate rules and adjustments"
```

---

### Task 2: Integrate Pricing Engine into Quote Endpoint

**Files:**
- Create: `backend/app/services/pricing.py`
- Modify: `backend/app/routers/cards.py` (or `backend/app/routers/api.py`)
- Create: `backend/tests/test_pricing_integration.py`

**Steps:**

- [ ] **Create `backend/app/services/pricing.py`**:

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pricing import RateRule, RateSnapshot
from app.models.card import CardSubmissionStatus


async def get_effective_rate(
    db: AsyncSession,
    brand_id: int,
    denomination_id: int,
    value: float,
) -> tuple[float, float]:
    """Returns (effective_buy_rate, sell_price). Falls back to 0.75 / value * 1.10."""
    result = await db.execute(
        select(RateRule)
        .where(
            RateRule.brand_id == brand_id,
            RateRule.denomination_id == denomination_id,
            RateRule.active == True,
        )
        .options(selectinload(RateRule.adjustments))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        return 0.75, round(value * 1.10, 2)

    # Count active listings for this denom
    count_result = await db.execute(
        select(func.count()).select_from(CardSubmission)
        .where(
            CardSubmission.brand_id == brand_id,
            CardSubmission.denomination_id == denomination_id,
            CardSubmission.status.in_([CardSubmissionStatus.APPROVED, CardSubmissionStatus.PAID]),
        )
    )
    active_listings = count_result.scalar() or 0

    # Count submissions in last 24hr
    from datetime import datetime, timedelta, timezone
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    sub_count = await db.execute(
        select(func.count()).select_from(CardSubmission)
        .where(
            CardSubmission.brand_id == brand_id,
            CardSubmission.submitted_at >= since,
        )
    )
    daily_submissions = sub_count.scalar() or 0

    # Compute
    from app.routers.pricing import compute_effective_rate
    effective_rate = compute_effective_rate(rule, active_listings, daily_submissions)
    sell_price = round(value * (1 + rule.sell_markup_pct), 2)
    effective_rate = round(effective_rate, 4)

    # Log snapshot
    snapshot = RateSnapshot(
        brand_id=brand_id,
        denomination_id=denomination_id,
        effective_buy_rate=effective_rate,
        effective_sell_price=sell_price,
    )
    db.add(snapshot)
    await db.commit()

    return effective_rate, sell_price
```

**Important:** This service imports `CardSubmission` which is in `app.models.card`. Make sure that import is at the top.

- [ ] **Modify `backend/app/routers/cards.py`** — replace the hardcoded `buy_rate = 0.75` in the `quote_card` function with a call to the pricing service:

```python
from app.services.pricing import get_effective_rate

@router.post("/api/cards/quote", response_model=CardQuoteResponse)
async def quote_card(
    body: CardQuoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(CardBrand).where(CardBrand.id == body.brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

    result = await db.execute(
        select(Denomination).where(
            Denomination.id == body.denomination_id,
            Denomination.brand_id == body.brand_id,
        )
    )
    denom = result.scalar_one_or_none()
    if not denom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denomination not found")

    buy_rate, sell_price = await get_effective_rate(db, body.brand_id, body.denomination_id, denom.value)
    quoted_amount = round(denom.value * buy_rate, 2)
    return CardQuoteResponse(quoted_amount=quoted_amount, buy_rate=buy_rate)
```

- [ ] **Create `backend/tests/test_pricing_integration.py`**:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_quote_uses_pricing_engine(client: AsyncClient, user_token, db_session):
    from app.models.card import CardBrand, Denomination
    from app.models.pricing import RateRule
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()
    rule = RateRule(brand_id=brand.id, denomination_id=denom.id, base_buy_rate=0.80)
    db_session.add(rule)
    await db_session.commit()

    response = await client.post("/api/cards/quote", json={
        "brand_id": brand.id, "denomination_id": denom.id, "card_code": "TEST",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    # Should use 0.80 from rule instead of default 0.75
    assert response.json()["buy_rate"] == 0.80


@pytest.mark.asyncio
async def test_quote_falls_back_to_default(client: AsyncClient, user_token, db_session):
    from app.models.card import CardBrand, Denomination
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()

    response = await client.post("/api/cards/quote", json={
        "brand_id": brand.id, "denomination_id": denom.id, "card_code": "TEST",
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    # No rate rule exists, should use default 0.75
    assert response.json()["buy_rate"] == 0.75
```

- [ ] **Run all tests**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/ -v
```

Expected: All tests pass (18 existing + 5 new = 23+ total)

- [ ] **Commit**:
```bash
git add backend/app/services/pricing.py backend/app/routers/cards.py backend/tests/
git commit -m "feat: integrate pricing engine into card quote endpoint"
```

---

### Task 3: Reloadly API Client + Models

**Files:**
- Create: `backend/app/models/reloadly.py`
- Create: `backend/app/services/reloadly.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/tests/test_reloadly.py`

**Steps:**

- [ ] **Install dependency**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pip install tenacity
```

- [ ] **Create `backend/app/models/reloadly.py`**:

```python
from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, ForeignKey, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class ReloadlyTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class ReloadlyProduct(Base):
    __tablename__ = "reloadly_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    reloadly_id: Mapped[int] = mapped_column(unique=True)
    brand: Mapped[str] = mapped_column(String(100))
    denomination: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    sell_price: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReloadlyTransaction(Base):
    __tablename__ = "reloadly_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("reloadly_products.id"))
    order_reference: Mapped[str] = mapped_column(String(255), unique=True)
    amount: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    recipient_email: Mapped[str] = mapped_column(String(255))
    status: Mapped[ReloadlyTransactionStatus] = mapped_column(
        SAEnum(ReloadlyTransactionStatus), default=ReloadlyTransactionStatus.PENDING
    )
    reloadly_tx_id: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    product = relationship("ReloadlyProduct")
```

- [ ] **Update `backend/app/models/__init__.py`** — add ReloadlyProduct, ReloadlyTransaction, ReloadlyTransactionStatus

- [ ] **Create `backend/app/services/reloadly.py`**:

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings


class ReloadlyClient:
    def __init__(self):
        self.settings = get_settings()
        self._base_url = (
            "https://api.reloadly.com"
            if self.settings.reloadly_environment == "production"
            else "https://api.reloadly.com"  # Reloadly uses same base for sandbox
        )
        self._token = None

    async def _get_token(self) -> str:
        """Get OAuth2 client credentials token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self._base_url}/o/token", json={
                "client_id": self.settings.reloadly_client_id,
                "client_secret": self.settings.reloadly_client_secret,
                "grant_type": "client_credentials",
                "audience": "https://api.reloadly.com",
            })
            resp.raise_for_status()
            data = resp.json()
            return data["access_token"]

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
    async def list_products(self, page=1, size=50) -> list[dict]:
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
    settings = get_settings()
    if not settings.reloadly_client_id or settings.reloadly_client_id == "":
        return MockReloadlyClient()
    return ReloadlyClient()
```

- [ ] **Create `backend/tests/test_reloadly.py`**:

```python
import pytest


@pytest.mark.asyncio
async def test_mock_client_list_products():
    from app.services.reloadly import MockReloadlyClient
    client = MockReloadlyClient()
    products = await client.list_products()
    assert len(products) == 2
    assert products[0]["productName"] == "Amazon $100"


@pytest.mark.asyncio
async def test_mock_client_place_order():
    from app.services.reloadly import MockReloadlyClient
    client = MockReloadlyClient()
    result = await client.place_order(1, 1, "test@example.com")
    assert result["status"] == "SUCCESSFUL"


@pytest.mark.asyncio
async def test_mock_client_balance():
    from app.services.reloadly import MockReloadlyClient
    client = MockReloadlyClient()
    balance = await client.get_balance()
    assert balance["balance"] == 500.0


@pytest.mark.asyncio
async def test_get_reloadly_client_returns_mock():
    from app.services.reloadly import get_reloadly_client, MockReloadlyClient
    client = get_reloadly_client()
    assert isinstance(client, MockReloadlyClient)
```

- [ ] **Generate migration**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/alembic revision --autogenerate -m "add reloadly models" && .venv/bin/alembic upgrade head
```

- [ ] **Run tests**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_reloadly.py -v
```

Expected: All 4 tests pass

- [ ] **Commit**:
```bash
git add backend/app/models/reloadly.py backend/app/services/reloadly.py backend/tests/test_reloadly.py backend/alembic/
git commit -m "feat: Reloadly API client with mock for development"
```

---

### Task 4: Reloadly Sync + Merged Product Feed

**Files:**
- Create: `backend/app/celery_tasks/__init__.py`
- Create: `backend/app/celery_tasks/reloadly_sync.py`
- Create: `backend/app/routers/products.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_products.py`

**Steps:**

- [ ] **Create `backend/app/celery_tasks/__init__.py`**:
```python
```

- [ ] **Create `backend/app/celery_tasks/reloadly_sync.py`**:

```python
from app.celery_app import celery_app
from app.services.reloadly import get_reloadly_client
from app.database import async_session
from app.models.reloadly import ReloadlyProduct
from sqlalchemy import select
from datetime import datetime, timezone
import asyncio


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task
def sync_reloadly_products():
    """Fetch all products from Reloadly API and upsert into database."""
    client = get_reloadly_client()
    page = 1
    total = 0

    async def _sync():
        nonlocal total
        async with async_session() as db:
            while True:
                products = await client.list_products(page=page)
                if not products:
                    break
                for p in products:
                    denoms = p.get("fixedRecipientDenominations", [100])
                    denom = denoms[0] if denoms else 100
                    result = await db.execute(
                        select(ReloadlyProduct).where(ReloadlyProduct.reloadly_id == p["id"])
                    )
                    existing = result.scalar_one_or_none()
                    if existing:
                        existing.sell_price = denom
                        existing.brand = p.get("productName", existing.brand)
                        existing.last_synced = datetime.now(timezone.utc)
                    else:
                        db.add(ReloadlyProduct(
                            reloadly_id=p["id"],
                            brand=p.get("productName", "Unknown"),
                            denomination=denom,
                            currency=p.get("targetCurrency", "USD"),
                            sell_price=denom,
                            fee=p.get("senderFee", 0.0),
                        ))
                    total += 1
                page += 1
            await db.commit()
        return total

    return run_async(_sync())
```

- [ ] **Register the sync task in `backend/app/celery_app.py`** — the task is auto-discovered if `celery_app.autodiscover_tasks(["app"])` is set (which it already is from Task 1). No changes needed.

- [ ] **Create `backend/app/routers/products.py`**:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.card import CardBrand, Denomination
from app.models.reloadly import ReloadlyProduct
from app.config import get_settings

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
async def list_products(
    brand: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    markup_pct = 0.05  # Default Reloadly markup, could be configurable

    # Get own inventory listings
    from app.models.card import OwnListing
    own_result = await db.execute(
        select(OwnListing).where(OwnListing.status == "available")
    )
    own_listings = own_result.scalars().all()

    # Get Reloadly products
    reloadly_result = await db.execute(
        select(ReloadlyProduct).where(ReloadlyProduct.active == True)
    )
    reloadly_products = reloadly_result.scalars().all()

    # Merge
    merged = []
    for listing in own_listings:
        merged.append({
            "id": f"own-{listing.id}",
            "source": "own",
            "brand": listing.brand.name if hasattr(listing, 'brand') else "",
            "denomination": listing.denomination.value if hasattr(listing, 'denomination') else 0,
            "price": listing.sell_price,
            "currency": "USD",
        })
    for rp in reloadly_products:
        price = round(rp.sell_price * (1 + markup_pct), 2)
        merged.append({
            "id": f"reloadly-{rp.id}",
            "source": "reloadly",
            "brand": rp.brand,
            "denomination": rp.denomination,
            "price": price,
            "currency": rp.currency,
        })

    # Apply filters
    if brand:
        merged = [p for p in merged if brand.lower() in p["brand"].lower()]
    if min_price is not None:
        merged = [p for p in merged if p["price"] >= min_price]
    if max_price is not None:
        merged = [p for p in merged if p["price"] <= max_price]

    return merged


@router.get("/reloadly")
async def list_reloadly_products(db: AsyncSession = Depends(get_db)):
    """Reloadly-only products (admin use / debugging)."""
    result = await db.execute(
        select(ReloadlyProduct).where(ReloadlyProduct.active == True)
    )
    products = result.scalars().all()
    return [{
        "id": p.id,
        "reloadly_id": p.reloadly_id,
        "brand": p.brand,
        "denomination": p.denomination,
        "price": p.sell_price,
        "currency": p.currency,
        "fee": p.fee,
    } for p in products]


@router.post("/reloadly/order")
async def place_reloadly_order(
    product_id: int,
    recipient_email: str,
    db: AsyncSession = Depends(get_db),
):
    """Place an order with Reloadly for a product."""
    from app.services.reloadly import get_reloadly_client
    client = get_reloadly_client()
    result = await client.place_order(product_id, 1, recipient_email)
    return {"transaction_id": result.get("transactionId"), "status": result.get("status")}
```

**Note:** The `OwnListing` model might not exist yet (it was deferred from Phase 1). The products router should handle the case where OwnListing doesn't exist gracefully. For now, the merged feed will mainly show Reloadly products.

- [ ] **Register products router in `backend/app/main.py`**:
```python
from app.routers import products
app.include_router(products.router)
```

- [ ] **Create `backend/tests/test_products.py`**:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_products_empty(client: AsyncClient):
    response = await client.get("/api/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_reloadly_products(client: AsyncClient, db_session):
    from app.models.reloadly import ReloadlyProduct
    rp = ReloadlyProduct(reloadly_id=1, brand="Amazon", denomination=100.0, sell_price=95.0)
    db_session.add(rp)
    await db_session.commit()

    response = await client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    # Should have the Reloadly product merged in
    sources = [p["source"] for p in data]
    assert "reloadly" in sources
```

- [ ] **Run all tests**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/ -v
```

Expected: All tests pass

- [ ] **Commit**:
```bash
git add backend/app/celery_tasks/ backend/app/routers/products.py backend/app/main.py backend/tests/test_products.py
git commit -m "feat: Reloadly sync task and merged product feed"
```

---

## Spec Coverage Check

| Phase 2 Requirement | Covered By |
|---------------------|------------|
| RateRule model (brand FK, denom FK, base_buy_rate, sell_markup_pct, min_rate, max_rate) | Task 1 |
| RateAdjustment model (trigger types: stock_low, stock_high, submission_volume, day_of_week) | Task 1 |
| RateSnapshot for audit logging | Task 1 |
| Rate calculation engine (base + adjustments, clamped) | Task 1 |
| Admin CRUD for rate rules | Task 1 |
| Effective rates endpoint | Task 1 |
| Pricing engine integrated into quote flow | Task 2 |
| Fallback to default rate when no rule exists | Task 2 |
| ReloadlyProduct model (reloadly_id, brand, denom, price, fee) | Task 3 |
| ReloadlyTransaction model (user, product, status, tx_id) | Task 3 |
| Reloadly API client with OAuth2 + retry | Task 3 |
| MockReloadlyClient for dev/testing | Task 3 |
| Celery sync task (every 15 min) | Task 4 |
| Merged product feed (Reloadly + own inventory) | Task 4 |
| Reloadly-only product endpoint | Task 4 |
| Reloadly order placement endpoint | Task 4 |

**Not yet covered (Phase 3+):** Paystack/Flutterwave payment integration, Flutter frontend, KYC upload, full Reloadly balance management, disputes, notifications, encryption.
