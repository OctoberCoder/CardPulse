from pydantic import BaseModel
from typing import Optional


class ReviewSubmissionRequest(BaseModel):
    status: str  # "approved" or "rejected"
    admin_notes: str = ""
    final_amount: Optional[float] = None
