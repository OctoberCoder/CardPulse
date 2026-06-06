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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.idempotency_key:
        result = await db.execute(
            select(Order).where(Order.idempotency_key == body.idempotency_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

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
        payment_reference=f"cp-{uuid.uuid4().hex[:12]}",
        idempotency_key=body.idempotency_key or f"auto-{uuid.uuid4().hex[:16]}",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    client = get_payment_client(body.payment_method)
    payment = await client.initialize_payment(
        email=current_user.email,
        amount=order.amount_paid,
        reference=order.payment_reference,
    )

    result_data = OrderResponse.model_validate(order).model_dump()
    result_data["payment_url"] = payment.get("data", {}).get("authorization_url")
    return result_data


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
