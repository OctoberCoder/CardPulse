from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, KYCStatus
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/kyc", tags=["kyc"])


@router.post("/upload")
async def upload_kyc(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.kyc_status == KYCStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="KYC already approved")

    allowed = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Use JPEG, PNG, or PDF")

    current_user.kyc_status = KYCStatus.PENDING
    await db.commit()
    return {"status": "pending", "message": "KYC documents submitted for review"}


@router.get("/status")
async def get_kyc_status(
    current_user: User = Depends(get_current_user),
):
    return {"tier": current_user.tier, "kyc_status": current_user.kyc_status}
