# CardPulse Phase 5: Security, Notifications, KYC, Admin UI, Disputes

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**Goal:** Production-hardening — encrypt card codes, detect fraud, send notifications, handle KYC, build admin screens, and resolve disputes.

---

### Task 1: Card Code Encryption + Decryption Service

**Files:**
- Create: `backend/app/services/encryption.py`
- Create: `backend/tests/test_encryption.py`

**Steps:**

- [ ] **Create `backend/app/services/encryption.py`**:

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import get_settings
import os


def _get_key() -> bytes:
    key = get_settings().encryption_key
    # Pad or truncate to 32 bytes for AES-256
    return key.encode().ljust(32, b'\0')[:32]


def encrypt(plaintext: str) -> str:
    import base64
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt(encoded: str) -> str:
    import base64
    key = _get_key()
    data = base64.urlsafe_b64decode(encoded)
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()
```

- [ ] **Create `backend/tests/test_encryption.py`**:

```python
import pytest
from app.services.encryption import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    original = "AMZ-1234-5678-ABCD"
    encoded = encrypt(original)
    assert encoded != original
    decoded = decrypt(encoded)
    assert decoded == original


def test_encryption_produces_different_outputs():
    code = "TEST-CODE"
    e1 = encrypt(code)
    e2 = encrypt(code)
    assert e1 != e2  # Different nonce each time


def test_decrypt_invalid_data():
    with pytest.raises(Exception):
        decrypt("not-valid-base64!!")
```

- [ ] **Update card submission to use encryption**: modify `backend/app/routers/cards.py` — import `encrypt` and use it in `submit_card`:
```python
from app.services.encryption import encrypt
...
submission = CardSubmission(
    ...
    card_code=encrypt(body.card_code),
    ...
)
```

- [ ] **Run tests**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_encryption.py -v
```

- [ ] **Commit**:
```bash
git add . && git commit -m "feat: AES-256-GCM card code encryption"
```

---

### Task 2: Fraud Detection

**Files:**
- Create: `backend/app/models/fraud.py`
- Create: `backend/app/services/fraud.py`
- Modify: `backend/app/services/__init__.py`
- Create: `backend/tests/test_fraud.py`

**Steps:**

- [ ] **Create `backend/app/models/fraud.py`**:

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .base import Base


class FraudSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FraudAlertStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATED = "investigated"
    RESOLVED = "resolved"


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    triggered_by_rule: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    submission_id: Mapped[int] = mapped_column(ForeignKey("card_submissions.id"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[FraudSeverity] = mapped_column(SAEnum(FraudSeverity))
    status: Mapped[FraudAlertStatus] = mapped_column(SAEnum(FraudAlertStatus), default=FraudAlertStatus.OPEN)
    resolved_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Create `backend/app/services/fraud.py`**:

```python
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fraud import FraudAlert, FraudSeverity
from app.models.card import CardSubmission, CardSubmissionStatus


async def check_card_submission(
    db: AsyncSession,
    user_id: int,
    card_code: str,
    brand_id: int,
) -> list[FraudAlert]:
    """Run fraud checks on a card submission. Returns any triggered alerts."""
    alerts: list[FraudAlert] = []
    code_hash = hashlib.sha256(card_code.encode()).hexdigest()

    # Rule 1: Duplicate card code
    result = await db.execute(
        select(CardSubmission).where(CardSubmission.card_code == card_code)
    )
    existing = result.scalars().all()
    if len(existing) > 1 or (len(existing) == 1 and existing[0].user_id != user_id):
        alert = FraudAlert(
            triggered_by_rule="duplicate_code",
            user_id=user_id, submission_id=None,
            description=f"Duplicate card code detected across accounts",
            severity=FraudSeverity.HIGH,
        )
        db.add(alert)
        alerts.append(alert)

    # Rule 2: Velocity check — more than 5 submissions in 1 hour
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    count = await db.execute(
        select(func.count()).select_from(CardSubmission)
        .where(CardSubmission.user_id == user_id, CardSubmission.submitted_at >= since)
    )
    if (count.scalar() or 0) >= 5:
        alert = FraudAlert(
            triggered_by_rule="velocity_high",
            user_id=user_id, submission_id=None,
            description="More than 5 submissions in 1 hour",
            severity=FraudSeverity.MEDIUM,
        )
        db.add(alert)
        alerts.append(alert)

    if alerts:
        await db.commit()
    return alerts
```

- [ ] **Create `backend/tests/test_fraud.py`**:

```python
import pytest
from app.services.fraud import check_card_submission


@pytest.mark.asyncio
async def test_no_fraud_for_normal_submission(db_session):
    from app.models.card import CardBrand, Denomination
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
```

- [ ] **Run tests**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_fraud.py -v
```

- [ ] **Commit**:
```bash
git add . && git commit -m "feat: fraud detection with duplicate code and velocity checks"
```

---

### Task 3: Notifications (Email + In-App)

**Files:**
- Create: `backend/app/models/notification.py`
- Create: `backend/app/services/notifications.py`
- Create: `backend/app/routers/notifications.py`
- Create: `backend/tests/test_notifications.py`

**Steps:**

- [ ] **Create `backend/app/models/notification.py`**:

```python
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .base import Base


class NotificationType(str, enum.Enum):
    SUBMISSION_APPROVED = "submission_approved"
    SUBMISSION_REJECTED = "submission_rejected"
    ORDER_COMPLETED = "order_completed"
    PAYOUT_PROCESSED = "payout_processed"
    DISPUTE_RESOLVED = "dispute_resolved"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Create `backend/app/services/notifications.py`**:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type_: NotificationType,
    title: str,
    message: str,
) -> Notification:
    notif = Notification(
        user_id=user_id, type=type_, title=title, message=message,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return notif


async def notify_submission_approved(db: AsyncSession, user_id: int, amount: float):
    await create_notification(
        db, user_id, NotificationType.SUBMISSION_APPROVED,
        "Card Sale Approved",
        f"Your gift card was approved! \${amount:.2f} added to your wallet.",
    )


async def notify_submission_rejected(db: AsyncSession, user_id: int, reason: str):
    await create_notification(
        db, user_id, NotificationType.SUBMISSION_REJECTED,
        "Card Sale Rejected",
        f"Your gift card submission was rejected: {reason}",
    )
```

- [ ] **Create `backend/app/routers/notifications.py`**:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.patch("/{notif_id}/read")
async def mark_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notif_id, Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif:
        notif.read = True
        await db.commit()
    return {"status": "ok"}
```

- [ ] **Create `backend/tests/test_notifications.py`**:

```python
import pytest
from app.services.notifications import create_notification, notify_submission_approved
from app.models.notification import NotificationType


@pytest.mark.asyncio
async def test_create_notification(db_session):
    notif = await create_notification(
        db_session, user_id=1, type_=NotificationType.SUBMISSION_APPROVED,
        title="Test", message="Hello",
    )
    assert notif.title == "Test"
    assert notif.read is False


@pytest.mark.asyncio
async def test_notify_approved(db_session):
    await notify_submission_approved(db_session, user_id=1, amount=75.0)
    from sqlalchemy import select
    from app.models.notification import Notification
    result = await db_session.execute(select(Notification))
    notifs = result.scalars().all()
    assert len(notifs) == 1
    assert "$75" in notifs[0].message
```

- [ ] **Run tests and commit**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_notifications.py -v
git add . && git commit -m "feat: notifications with in-app alerts"
```

---

### Task 4: KYC Document Upload + Verification

**Files:**
- Create: `backend/app/routers/kyc.py`
- Create: `backend/tests/test_kyc.py`
- Modify: `backend/app/main.py`

**Steps:**

- [ ] **Create `backend/app/routers/kyc.py`**:

```python
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

    # Validate file type
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
```

- [ ] **Register KYC router in `backend/app/main.py`**:
```python
from app.routers import kyc
app.include_router(kyc.router)
```

- [ ] **Create `backend/tests/test_kyc.py`**:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_kyc(client: AsyncClient, user_token):
    response = await client.post(
        "/api/kyc/upload",
        files={"file": ("id.jpg", b"fake-image-data", "image/jpeg")},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_kyc_status(client: AsyncClient, user_token):
    response = await client.get("/api/kyc/status", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert "kyc_status" in response.json()
```

- [ ] **Run tests and commit**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_kyc.py -v
git add . && git commit -m "feat: KYC document upload and status"
```

---

### Task 5: Admin Flutter Screens (Card Review + Payouts)

**Files:**
- Create: `frontend/lib/screens/admin_submissions_screen.dart`
- Create: `frontend/lib/api/admin_api.dart`
- Modify: `frontend/lib/screens/dashboard_screen.dart`
- Modify: `frontend/lib/main.dart`

**Steps:**

- [ ] **Create `frontend/lib/api/admin_api.dart`**:

```dart
import 'package:cardpulse/api/client.dart';

class AdminApi {
  final ApiClient _client;
  AdminApi(this._client);

  Future<List<Map<String, dynamic>>> getSubmissions({String? statusFilter}) async {
    final params = statusFilter != null ? {'status_filter': statusFilter} : null;
    final data = await _client.get('/admin/cards/submissions', params: params);
    return (data as List).cast<Map<String, dynamic>>();
  }

  Future<void> reviewSubmission(int id, String status, {String notes = '', double? finalAmount}) async {
    await _client.patch('/admin/cards/submissions/$id/review', body: {
      'status': status, 'admin_notes': notes,
      if (finalAmount != null) 'final_amount': finalAmount,
    });
  }
}
```

- [ ] **Create `frontend/lib/screens/admin_submissions_screen.dart`**:

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cardpulse/api/client.dart';
import 'package:cardpulse/api/admin_api.dart';
import 'package:cardpulse/providers/auth_provider.dart';

class AdminSubmissionsScreen extends ConsumerStatefulWidget {
  const AdminSubmissionsScreen({super.key});
  @override
  ConsumerState<AdminSubmissionsScreen> createState() => _AdminSubmissionsScreenState();
}

class _AdminSubmissionsScreenState extends ConsumerState<AdminSubmissionsScreen> {
  List<Map<String, dynamic>> _submissions = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() async {
    setState(() => _loading = true);
    try {
      final client = ref.read(apiClientProvider);
      final api = AdminApi(client);
      final subs = await api.getSubmissions(statusFilter: 'pending');
      if (mounted) setState(() => _submissions = subs);
    } catch (_) {}
    if (mounted) setState(() => _loading = false);
  }

  void _approve(int id) async {
    final client = ref.read(apiClientProvider);
    final api = AdminApi(client);
    await api.reviewSubmission(id, 'approved', notes: 'Verified');
    _load();
  }

  void _reject(int id) async {
    final client = ref.read(apiClientProvider);
    final api = AdminApi(client);
    await api.reviewSubmission(id, 'rejected', notes: 'Invalid code');
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Admin - Pending Submissions')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _submissions.isEmpty
              ? const Center(child: Text('No pending submissions'))
              : ListView.builder(
                  itemCount: _submissions.length,
                  itemBuilder: (_, i) {
                    final s = _submissions[i];
                    return Card(child: ListTile(
                      title: Text('Submission #${s['id']}'),
                      subtitle: Text('\$${s['quoted_amount']} - ${s['status']}'),
                      trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                        IconButton(icon: const Icon(Icons.check, color: Colors.green), onPressed: () => _approve(s['id'])),
                        IconButton(icon: const Icon(Icons.close, color: Colors.red), onPressed: () => _reject(s['id'])),
                      ]),
                    ));
                  },
                ),
    );
  }
}
```

- [ ] **Run Flutter analyze and commit**:
```bash
cd /Users/igeorge/CardPulse/frontend && flutter analyze 2>&1 | tail -3
cd /Users/igeorge/CardPulse && git add . && git commit -m "feat(flutter): admin submissions screen"
```

---

### Task 6: Disputes API

**Files:**
- Create: `backend/app/models/dispute.py`
- Create: `backend/app/routers/disputes.py`
- Create: `backend/tests/test_disputes.py`

**Steps:**

- [ ] **Create `backend/app/models/dispute.py`**:

```python
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .base import Base


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"


class DisputeResolution(str, enum.Enum):
    REFUND = "refund"
    REJECT = "reject"


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    evidence_urls: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[DisputeStatus] = mapped_column(SAEnum(DisputeStatus), default=DisputeStatus.OPEN)
    resolution: Mapped[DisputeResolution] = mapped_column(nullable=True)
    admin_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Create `backend/app/routers/disputes.py`**:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.dispute import Dispute, DisputeStatus
from app.models.order import Order
from app.models.user import User
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/disputes", tags=["disputes"])


@router.post("/orders/{order_id}/dispute")
async def open_dispute(
    order_id: int, reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.buyer_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    dispute = Dispute(order_id=order_id, user_id=current_user.id, reason=reason)
    db.add(dispute)
    await db.commit()
    await db.refresh(dispute)
    return dispute


@router.get("")
async def list_disputes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Dispute).where(Dispute.user_id == current_user.id).order_by(Dispute.created_at.desc())
    )
    return result.scalars().all()
```

- [ ] **Create `backend/tests/test_disputes.py`**:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_open_dispute_no_order(client: AsyncClient, user_token):
    response = await client.post("/api/disputes/orders/999/dispute?reason=broken",
                                  headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 404
```

- [ ] **Run tests and commit**:
```bash
cd /Users/igeorge/CardPulse/backend && .venv/bin/pytest tests/test_disputes.py -v
git add . && git commit -m "feat: disputes API"
```
