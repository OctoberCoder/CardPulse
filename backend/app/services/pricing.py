from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pricing import RateRule, RateSnapshot
from app.models.card import CardSubmission, CardSubmissionStatus


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

    listing_count = await db.execute(
        select(func.count()).select_from(CardSubmission)
        .where(
            CardSubmission.brand_id == brand_id,
            CardSubmission.denomination_id == denomination_id,
            CardSubmission.status.in_([CardSubmissionStatus.APPROVED, CardSubmissionStatus.PAID]),
        )
    )
    active_listings = listing_count.scalar() or 0

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    sub_count = await db.execute(
        select(func.count()).select_from(CardSubmission)
        .where(
            CardSubmission.brand_id == brand_id,
            CardSubmission.submitted_at >= since,
        )
    )
    daily_submissions = sub_count.scalar() or 0

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

        if triggered:
            if adj.operator == "add":
                rate += adj.adjustment_pct
            elif adj.operator == "subtract":
                rate -= adj.adjustment_pct

    rate = max(rule.min_rate, min(rule.max_rate, rate))
    sell_price = round(value * (1 + rule.sell_markup_pct), 2)
    rate = round(rate, 4)

    snapshot = RateSnapshot(
        brand_id=brand_id,
        denomination_id=denomination_id,
        effective_buy_rate=rate,
        effective_sell_price=sell_price,
    )
    db.add(snapshot)
    await db.commit()

    return rate, sell_price
