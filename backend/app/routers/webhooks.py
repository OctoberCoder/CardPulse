from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.services.payments import get_payment_client
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/paystack")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    signature = request.headers.get("x-paystack-signature", "")
    body = await request.body()

    client = get_payment_client("paystack")
    if not client.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = json.loads(body)
    event = payload.get("event", "")

    if event == "charge.success":
        reference = payload.get("data", {}).get("reference", "")
        result = await db.execute(select(Order).where(Order.payment_reference == reference))
        order = result.scalar_one_or_none()
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.COMPLETED
            order.delivered_at = datetime.now(timezone.utc)
            await db.commit()

    return {"status": "ok"}


@router.post("/flutterwave")
async def flutterwave_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    signature = request.headers.get("verif-hash", "")
    body = await request.body()

    client = get_payment_client("flutterwave")
    if not client.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = json.loads(body)
    event = payload.get("event", "")

    if "completed" in event.lower():
        reference = payload.get("data", {}).get("tx_ref", "")
        result = await db.execute(select(Order).where(Order.payment_reference == reference))
        order = result.scalar_one_or_none()
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.COMPLETED
            order.delivered_at = datetime.now(timezone.utc)
            await db.commit()

    return {"status": "ok"}
