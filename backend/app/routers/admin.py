from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.card import CardSubmission, CardSubmissionStatus
from app.models.user import User
from app.schemas.card import CardSubmissionResponse
from app.schemas.admin import ReviewSubmissionRequest
from app.services.auth import get_current_user
from app.services.wallet import credit_wallet
from app.services.notifications import notify_submission_approved, notify_submission_rejected

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_staff(user: User = Depends(get_current_user)) -> User:
    if not user.is_staff:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.get("/cards/submissions", response_model=list[CardSubmissionResponse])
async def list_submissions(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    query = select(CardSubmission).options(
        selectinload(CardSubmission.brand),
        selectinload(CardSubmission.denomination),
    ).order_by(CardSubmission.submitted_at.desc())
    if status_filter:
        query = query.where(CardSubmission.status == CardSubmissionStatus(status_filter))
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/cards/submissions/{submission_id}/review", response_model=CardSubmissionResponse)
async def review_submission(
    submission_id: int,
    body: ReviewSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    result = await db.execute(
        select(CardSubmission)
        .options(selectinload(CardSubmission.brand), selectinload(CardSubmission.denomination))
        .where(CardSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    new_status = CardSubmissionStatus(body.status)
    if new_status not in (CardSubmissionStatus.APPROVED, CardSubmissionStatus.REJECTED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status. Use 'approved' or 'rejected'.")

    submission.status = new_status
    submission.reviewed_by = admin.id
    submission.admin_notes = body.admin_notes
    submission.reviewed_at = datetime.now(timezone.utc)
    if body.final_amount is not None:
        submission.final_amount = body.final_amount
    else:
        submission.final_amount = submission.quoted_amount

    if new_status == CardSubmissionStatus.APPROVED:
        await credit_wallet(
            db,
            user_id=submission.user_id,
            amount=submission.final_amount,
            reference=f"submission-{submission.id}",
            description=f"Card sale approved",
        )

    await db.commit()
    await db.refresh(submission)

    if new_status == CardSubmissionStatus.APPROVED:
        await notify_submission_approved(db, submission)
    elif new_status == CardSubmissionStatus.REJECTED:
        await notify_submission_rejected(db, submission)

    return submission
