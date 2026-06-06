from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.card import CardBrand, Denomination, CardSubmission, CardSubmissionStatus
from app.models.user import User
from app.schemas.card import (
    CardBrandResponse, CardBrandCreate, CardSubmissionResponse,
    CardQuoteRequest, CardQuoteResponse, CardSubmitRequest,
)
from app.services.auth import get_current_user

router = APIRouter(tags=["cards"])


@router.get("/api/brands", response_model=list[CardBrandResponse])
async def list_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CardBrand)
        .where(CardBrand.active == True)
        .options(selectinload(CardBrand.denominations))
        .order_by(CardBrand.name)
    )
    return result.scalars().all()


@router.get("/api/brands/{slug}/denominations")
async def get_brand_denominations(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CardBrand).where(CardBrand.slug == slug).options(selectinload(CardBrand.denominations))
    )
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return [{"id": d.id, "value": d.value, "currency": d.currency} for d in brand.denominations if d.active]


@router.post("/api/admin/brands", status_code=status.HTTP_201_CREATED, response_model=CardBrandResponse)
async def create_brand(
    body: CardBrandCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    result = await db.execute(select(CardBrand).where(CardBrand.slug == body.slug))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Brand already exists")
    brand = CardBrand(**body.model_dump())
    db.add(brand)
    await db.commit()
    result = await db.execute(
        select(CardBrand).where(CardBrand.id == brand.id).options(selectinload(CardBrand.denominations))
    )
    return result.scalar_one()


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
    buy_rate = 0.75
    result = await db.execute(
        select(Denomination).where(
            Denomination.id == body.denomination_id,
            Denomination.brand_id == body.brand_id,
        )
    )
    denom = result.scalar_one_or_none()
    if not denom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denomination not found")
    quoted_amount = round(denom.value * buy_rate, 2)
    return CardQuoteResponse(quoted_amount=quoted_amount, buy_rate=buy_rate)


@router.post("/api/cards/submit", status_code=status.HTTP_201_CREATED, response_model=CardSubmissionResponse)
async def submit_card(
    body: CardSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    submission = CardSubmission(
        user_id=current_user.id,
        brand_id=body.brand_id,
        denomination_id=body.denomination_id,
        card_code=body.card_code,
        card_image_url=body.card_image_url,
        quoted_amount=body.quoted_amount,
        status=CardSubmissionStatus.PENDING,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission
