from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet, WalletTransaction, TransactionType


async def ensure_wallet(db: AsyncSession, user_id: int) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = Wallet(user_id=user_id)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


async def credit_wallet(
    db: AsyncSession,
    user_id: int,
    amount: float,
    reference: str,
    description: str = "",
) -> WalletTransaction:
    wallet = await ensure_wallet(db, user_id)
    wallet.balance += amount
    txn = WalletTransaction(
        wallet_id=wallet.id,
        type=TransactionType.CREDIT,
        amount=amount,
        reference=reference,
        description=description,
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn
