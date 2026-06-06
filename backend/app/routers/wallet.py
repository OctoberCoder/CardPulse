from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.wallet import WalletResponse, WalletTransactionResponse
from app.services.auth import get_current_user
from app.services.wallet import ensure_wallet

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.get("", response_model=WalletResponse)
async def get_wallet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = await ensure_wallet(db, current_user.id)
    return wallet


@router.get("/transactions", response_model=list[WalletTransactionResponse])
async def get_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = await ensure_wallet(db, current_user.id)
    result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()
