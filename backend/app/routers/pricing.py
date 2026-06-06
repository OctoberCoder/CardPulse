from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.pricing import RateRule, RateAdjustment
from app.models.user import User
from app.schemas.pricing import RateRuleCreate, RateRuleResponse, EffectiveRateResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/admin/rates", tags=["pricing"])


async def require_staff(user: User = Depends(get_current_user)) -> User:
    if not user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


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
        from datetime import datetime
        rate = rule.base_buy_rate
        for adj in sorted(rule.adjustments, key=lambda a: a.priority):
            if not adj.active:
                continue
            triggered = False
            if adj.trigger_type == "day_of_week":
                triggered = datetime.now().strftime("%A") == adj.value
            if triggered:
                rate += adj.adjustment_pct if adj.operator == "add" else -adj.adjustment_pct
        rate = max(rule.min_rate, min(rule.max_rate, rate))
        sell_price = round(rule.denomination.value * (1 + rule.sell_markup_pct), 2)
        responses.append(EffectiveRateResponse(
            brand_id=rule.brand_id,
            denomination_id=rule.denomination_id,
            base_buy_rate=rule.base_buy_rate,
            effective_buy_rate=round(rate, 4),
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
