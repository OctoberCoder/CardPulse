from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.dispute import Dispute
from app.models.order import Order
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/disputes", tags=["disputes"])


@router.post("/orders/{order_id}/dispute", status_code=status.HTTP_201_CREATED)
async def open_dispute(
    order_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.buyer_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    dispute = Dispute(order_id=order_id, user_id=current_user.id, reason=reason)
    db.add(dispute)
    await db.commit()
    await db.refresh(dispute)
    return dispute


@router.get("")
async def list_disputes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Dispute)
        .where(Dispute.user_id == current_user.id)
        .order_by(Dispute.created_at.desc())
    )
    return result.scalars().all()
