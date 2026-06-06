import pytest
from app.services.fraud import check_card_submission


@pytest.mark.asyncio
async def test_no_fraud_for_normal_submission(db_session):
    from app.models.card import CardBrand
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()

    alerts = await check_card_submission(db_session, user_id=1, card_code="NEW-CODE", brand_id=brand.id)
    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_duplicate_code_flagged(db_session):
    from app.models.card import CardBrand, CardSubmission, CardSubmissionStatus
    brand = CardBrand(name="Amazon", slug="amazon")
    db_session.add(brand)
    await db_session.commit()
    db_session.add(CardSubmission(
        user_id=2, brand_id=brand.id, denomination_id=1,
        card_code="DUP-CODE", quoted_amount=50.0, status=CardSubmissionStatus.PENDING,
    ))
    await db_session.commit()

    alerts = await check_card_submission(db_session, user_id=1, card_code="DUP-CODE", brand_id=brand.id)
    assert len(alerts) >= 1
    assert alerts[0].triggered_by_rule == "duplicate_code"
