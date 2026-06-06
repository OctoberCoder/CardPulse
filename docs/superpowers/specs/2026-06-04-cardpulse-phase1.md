# CardPulse Phase 1: Project Scaffolding + Auth + Card Buying Flow

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational CardPulse backend with user auth, card brand management, and the card buying flow (users submit cards → get quoted → admin approves → wallet credited).

**Architecture:** FastAPI async backend with SQLAlchemy ORM, PostgreSQL via Supabase, Celery for background tasks, Redis for caching/rate limiting. SQLAdmin for initial admin panel. Tests with pytest + httpx.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Celery, Redis, SQLAdmin, pytest, httpx, slowapi, PyJWT, passlib[bcrypt]

---

### Task 1: Project Scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config/__init__.py`
- Create: `backend/app/config/settings.py`
- Create: `backend/docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `backend/.gitignore`

- [ ] **Step 1: Create project config**

Create `backend/pyproject.toml`:

```toml
[project]
name = "cardpulse"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.13.0",
    "psycopg2-binary>=2.9.0",
    "celery[redis]>=5.4.0",
    "redis>=5.0.0",
    "sqladmin>=0.20.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",
    "slowapi>=0.1.9",
    "httpx>=0.27.0",
    "cryptography>=43.0.0",
    "sentry-sdk[fastapi]>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "factory-boy>=3.3.0",
    "coverage[toml]>=7.0.0",
]

[build-system]
requires = ["setuptools>=75.0.0"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: Create settings module**

Create `backend/app/config/settings.py`:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "CardPulse"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cardpulse"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/cardpulse"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    encryption_key: str = "change-me-in-production-32bytes!"

    rate_limit_auth: str = "5/minute"
    rate_limit_general: str = "30/minute"
    rate_limit_browse: str = "100/minute"

    sentry_dsn: str = ""
    logtail_token: str = ""

    reloadly_client_id: str = ""
    reloadly_client_secret: str = ""
    reloadly_environment: str = "sandbox"

    paystack_secret_key: str = ""
    flutterwave_secret_key: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `backend/app/config/__init__.py`:
```python
from .settings import get_settings, Settings

__all__ = ["get_settings", "Settings"]
```

- [ ] **Step 3: Create FastAPI app entry point**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.state.limiter = None  # Will be set in middleware setup
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 4: Create Docker Compose**

Create `backend/docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: cardpulse
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/cardpulse
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/cardpulse
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - .:/app

volumes:
  pgdata:
```

- [ ] **Step 5: Create Dockerfile and .gitignore**

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e ".[dev]"
COPY . .
```

Create `backend/.gitignore`:

```
__pycache__/
*.pyc
.env
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
```

- [ ] **Step 6: Create __init__.py**

Create `backend/app/__init__.py`:
```python
```

- [ ] **Step 7: Bootstrap project and run it**

Run:
```bash
cd backend && pip install -e ".[dev]" && docker compose up -d db redis
```

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: initial project scaffolding with FastAPI, Docker Compose, Redis"
```

---

### Task 2: Database Setup (SQLAlchemy + Alembic)

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/.gitkeep`

- [ ] **Step 1: Create database module**

Create `backend/app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **Step 2: Create base model**

Create `backend/app/models/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass
```

Create `backend/app/models/__init__.py`:
```python
from .base import Base

__all__ = ["Base"]
```

- [ ] **Step 3: Initialize Alembic**

Run:
```bash
cd backend && alembic init alembic
```

- [ ] **Step 4: Configure Alembic for async**

Edit `backend/alembic/env.py`:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import get_settings
from app.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    connectable = create_async_engine(get_settings().database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: Generate initial migration**

Run:
```bash
cd backend && alembic revision --autogenerate -m "initial"
```

Expected: Creates migration file with empty schema (no models yet).

- [ ] **Step 6: Commit**

```bash
git add backend/alembic/ backend/app/database.py backend/app/models/
git commit -m "feat: database setup with SQLAlchemy and Alembic"
```

---

### Task 3: User Model + Auth (Register, Login, JWT)

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/auth.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Write the failing auth test**

Create `backend/tests/conftest.py`:

```python
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db
from app.models import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        await session.close()
    await engine.dispose()


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

Create `backend/tests/test_auth.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    response = await client.post("/api/auth/register", json={
        "email": "dup@example.com",
        "password": "SecurePass123!",
        "phone": "+2348098765432",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "login@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    response = await client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "SecurePass123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/auth/register", json={
        "email": "wrong@example.com",
        "password": "SecurePass123!",
        "phone": "+2348012345678",
    })
    response = await client.post("/api/auth/login", json={
        "email": "wrong@example.com",
        "password": "WrongPass123!",
    })
    assert response.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_auth.py -v`
Expected: FAIL with ImportError (models/schemas not defined yet)

- [ ] **Step 3: Create User model**

Create `backend/app/models/user.py`:

```python
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .base import Base


class UserTier(str, enum.Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    PREMIUM = "premium"


class KYCStatus(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    tier: Mapped[UserTier] = mapped_column(SAEnum(UserTier), default=UserTier.UNVERIFIED)
    kyc_status: Mapped[KYCStatus] = mapped_column(SAEnum(KYCStatus), default=KYCStatus.NONE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

Update `backend/app/models/__init__.py`:

```python
from .base import Base
from .user import User, UserTier, KYCStatus

__all__ = ["Base", "User", "UserTier", "KYCStatus"]
```

- [ ] **Step 4: Create auth schemas**

Create `backend/app/schemas/auth.py`:

```python
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    phone: str = Field(min_length=10)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    phone: str
    tier: str
    kyc_status: str
    is_active: bool

    class Config:
        from_attributes = True
```

- [ ] **Step 5: Create auth service**

Create `backend/app/services/auth.py`:

```python
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings, Settings
from app.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, settings: Settings | None = None) -> str:
    if settings is None:
        settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int, settings: Settings | None = None) -> str:
    if settings is None:
        settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user
```

- [ ] **Step 6: Create auth router**

Create `backend/app/routers/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        phone=body.phone,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 7: Register router with app**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.routers import auth

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.state.limiter = None
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

Create `backend/app/routers/__init__.py`:
```python
```

Create `backend/app/services/__init__.py`:
```python
```

Create `backend/app/schemas/__init__.py`:
```python
```

Create `backend/tests/__init__.py`:
```python
```

- [ ] **Step 8: Install test dependency and run tests**

Run:
```bash
cd backend && pip install aiosqlite && pytest tests/test_auth.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 9: Generate migration and commit**

Run:
```bash
cd backend && alembic revision --autogenerate -m "add users table" && alembic upgrade head
```

Commit:
```bash
git add backend/app/models/user.py backend/app/schemas/ backend/app/services/ backend/app/routers/ backend/tests/
git commit -m "feat: user auth with register, login, JWT"
```

---

### Task 4: Rate Limiting + Brute Force Protection

**Files:**
- Modify: `backend/app/main.py`
- Create: `backend/app/middleware/__init__.py`
- Create: `backend/app/middleware/rate_limit.py`

- [ ] **Step 1: Write rate limit test**

Add to `backend/tests/test_auth.py`:

```python
@pytest.mark.asyncio
async def test_rate_limit_exceeded(client: AsyncClient):
    for _ in range(5):
        await client.post("/api/auth/login", json={"email": "x@y.com", "password": "x"})
    response = await client.post("/api/auth/login", json={"email": "x@y.com", "password": "x"})
    assert response.status_code == 429
```

- [ ] **Step 2: Integrate slowapi**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.routers import auth

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 3: Apply rate limit to auth routes**

Modify `backend/app/routers/auth.py`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import APIRouter, Depends, HTTPException, Request, status

limiter = Limiter(key_func=get_remote_address)

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    ...

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    ...
```

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/test_auth.py -v`
Expected: All tests PASS (rate limit test might need tuning for test context)

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/routers/auth.py
git commit -m "feat: rate limiting with slowapi on auth endpoints"
```

---

### Task 5: CardBrand + Denomination Models and API

**Files:**
- Create: `backend/app/models/card.py`
- Create: `backend/app/schemas/card.py`
- Create: `backend/app/routers/cards.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_cards.py`

- [ ] **Step 1: Write failing tests for brands API**

Create `backend/tests/test_cards.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_brands_empty(client: AsyncClient):
    response = await client.get("/api/brands")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_brand_as_admin(client: AsyncClient, admin_token):
    response = await client.post("/api/admin/brands", json={
        "name": "Amazon",
        "slug": "amazon",
        "description": "Amazon gift cards",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    assert response.json()["name"] == "Amazon"


@pytest.mark.asyncio
async def test_list_brands_with_data(client: AsyncClient, admin_token):
    await client.post("/api/admin/brands", json={
        "name": "Amazon", "slug": "amazon",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    response = await client.get("/api/brands")
    assert response.status_code == 200
    assert len(response.json()) == 1
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd backend && pytest tests/test_cards.py -v`
Expected: FAIL — models not imported, admin_token fixture missing

- [ ] **Step 3: Create Card models**

Create `backend/app/models/card.py`:

```python
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Float, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class CardSubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class CardBrand(Base):
    __tablename__ = "card_brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    icon: Mapped[str] = mapped_column(String(255), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    denominations: Mapped[list["Denomination"]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class Denomination(Base):
    __tablename__ = "denominations"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    value: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brand: Mapped["CardBrand"] = relationship(back_populates="denominations")


class CardSubmission(Base):
    __tablename__ = "card_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    brand_id: Mapped[int] = mapped_column(ForeignKey("card_brands.id"))
    denomination_id: Mapped[int] = mapped_column(ForeignKey("denominations.id"))
    card_code_encrypted: Mapped[str] = mapped_column(Text)
    card_image_url: Mapped[str] = mapped_column(String(500), default="")
    quoted_amount: Mapped[float] = mapped_column(Float)
    final_amount: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[CardSubmissionStatus] = mapped_column(
        SAEnum(CardSubmissionStatus), default=CardSubmissionStatus.PENDING
    )
    reviewed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    admin_notes: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    brand = relationship("CardBrand")
    denomination = relationship("Denomination")
```

Update `backend/app/models/__init__.py`:

```python
from .base import Base
from .user import User, UserTier, KYCStatus
from .card import CardBrand, Denomination, CardSubmission, CardSubmissionStatus

__all__ = ["Base", "User", "UserTier", "KYCStatus", "CardBrand", "Denomination", "CardSubmission", "CardSubmissionStatus"]
```

- [ ] **Step 4: Create card schemas**

Create `backend/app/schemas/card.py`:

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DenominationResponse(BaseModel):
    id: int
    value: float
    currency: str
    active: bool

    class Config:
        from_attributes = True


class CardBrandResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    icon: str
    active: bool
    denominations: list[DenominationResponse] = []

    class Config:
        from_attributes = True


class CardBrandCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    icon: str = ""


class CardSubmissionResponse(BaseModel):
    id: int
    brand_id: int
    denomination_id: int
    quoted_amount: float
    final_amount: Optional[float] = None
    status: str
    admin_notes: str
    submitted_at: datetime

    class Config:
        from_attributes = True


class CardQuoteRequest(BaseModel):
    brand_id: int
    denomination_id: int
    card_code: str


class CardQuoteResponse(BaseModel):
    quoted_amount: float
    buy_rate: float


class CardSubmitRequest(BaseModel):
    brand_id: int
    denomination_id: int
    card_code: str
    quoted_amount: float
    card_image_url: str = ""
```

- [ ] **Step 5: Create cards router**

Create `backend/app/routers/cards.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.card import CardBrand, CardSubmission, CardSubmissionStatus
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
    result = await db.execute(select(CardBrand).where(CardBrand.slug == slug))
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
    await db.refresh(brand)
    return brand


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
    buy_rate = 0.75  # Placeholder — pricing engine in Phase 2
    denom_result = await db.execute(
        select(Denomination).where(Denomination.id == body.denomination_id, Denomination.brand_id == body.brand_id)
    )
    denom = denom_result.scalar_one_or_none()
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
        card_code_encrypted=body.card_code,  # TODO: Encrypt in Phase 2
        card_image_url=body.card_image_url,
        quoted_amount=body.quoted_amount,
        status=CardSubmissionStatus.PENDING,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission
```

- [ ] **Step 6: Add admin_token fixture to conftest**

Update `backend/tests/conftest.py`:

```python
@pytest.fixture
async def admin_token(client: AsyncClient, db_session):
    from app.models.user import User
    from app.services.auth import hash_password
    admin = User(
        email="admin@test.com",
        password_hash=hash_password("AdminPass123!"),
        phone="+2348000000000",
        is_staff=True,
    )
    db_session.add(admin)
    await db_session.commit()
    from app.services.auth import create_access_token
    return create_access_token(admin.id)
```

- [ ] **Step 7: Register cards router and run tests**

Modify `backend/app/main.py`:

```python
app.include_router(auth.router)
app.include_router(cards.router)
```

Run: `cd backend && pytest tests/test_cards.py -v`
Expected: All 3 tests PASS

- [ ] **Step 8: Generate migration and commit**

```bash
cd backend && alembic revision --autogenerate -m "add card brands, denominations, submissions" && alembic upgrade head
git add . && git commit -m "feat: card brands, denominations API and card submission flow"
```

---

### Task 6: Admin Review Flow (Approve/Reject Submissions)

**Files:**
- Create: `backend/app/routers/admin.py`
- Create: `backend/app/schemas/admin.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_admin.py`

- [ ] **Step 1: Write failing admin tests**

Create `backend/tests/test_admin.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_list_submissions(client: AsyncClient, admin_token, pending_submission):
    response = await client.get(
        "/api/admin/cards/submissions",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_admin_approve_submission(client: AsyncClient, admin_token, pending_submission):
    response = await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "approved", "admin_notes": "Code verified"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_admin_reject_submission(client: AsyncClient, admin_token, pending_submission):
    response = await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "rejected", "admin_notes": "Invalid code"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_non_admin_cannot_review(client: AsyncClient, user_token, pending_submission):
    response = await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "approved", "admin_notes": ""},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
```

- [ ] **Step 2: Add fixtures to conftest**

Add to `backend/tests/conftest.py`:

```python
@pytest.fixture
async def user_token(client: AsyncClient, db_session):
    from app.models.user import User
    from app.services.auth import hash_password
    user = User(
        email="user@test.com",
        password_hash=hash_password("UserPass123!"),
        phone="+2348011111111",
    )
    db_session.add(user)
    await db_session.commit()
    from app.services.auth import create_access_token
    return create_access_token(user.id)


@pytest.fixture
async def pending_submission(client: AsyncClient, db_session, admin_token):
    from app.models.card import CardBrand, Denomination, CardSubmission, CardSubmissionStatus
    brand = CardBrand(name="Test Brand", slug="test-brand")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()
    sub = CardSubmission(
        user_id=1, brand_id=brand.id, denomination_id=denom.id,
        card_code_encrypted="test-code", quoted_amount=75.0,
        status=CardSubmissionStatus.PENDING,
    )
    db_session.add(sub)
    await db_session.commit()
    return sub.id
```

- [ ] **Step 3: Run to verify they fail**

Run: `cd backend && pytest tests/test_admin.py -v`
Expected: FAIL — admin router not defined

- [ ] **Step 4: Create admin schemas**

Create `backend/app/schemas/admin.py`:

```python
from pydantic import BaseModel
from typing import Optional


class ReviewSubmissionRequest(BaseModel):
    status: str  # "approved" or "rejected"
    admin_notes: str = ""
    final_amount: Optional[float] = None
```

- [ ] **Step 5: Create admin router**

Create `backend/app/routers/admin.py`:

```python
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
    result = await db.execute(select(CardSubmission).where(CardSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    new_status = CardSubmissionStatus(body.status)
    if new_status not in (CardSubmissionStatus.APPROVED, CardSubmissionStatus.REJECTED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    submission.status = new_status
    submission.reviewed_by = admin.id
    submission.admin_notes = body.admin_notes
    submission.reviewed_at = datetime.now(timezone.utc)
    if body.final_amount is not None:
        submission.final_amount = body.final_amount
    else:
        submission.final_amount = submission.quoted_amount

    await db.commit()
    await db.refresh(submission)
    return submission
```

- [ ] **Step 6: Register admin router in main.py**

Modify `backend/app/main.py`:

```python
from app.routers import auth, cards, admin
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(admin.router)
```

- [ ] **Step 7: Run tests**

Run: `cd backend && pytest tests/test_admin.py -v`
Expected: All 4 tests PASS

- [ ] **Step 8: Commit**

```bash
git add . && git commit -m "feat: admin review flow for card submissions"
```

---

### Task 7: Wallet Model + Credit on Approval

**Files:**
- Create: `backend/app/models/wallet.py`
- Create: `backend/app/schemas/wallet.py`
- Create: `backend/app/routers/wallet.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/routers/admin.py`
- Create: `backend/tests/test_wallet.py`

- [ ] **Step 1: Write wallet tests**

Create `backend/tests/test_wallet.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_wallet_zero(client: AsyncClient, user_token):
    response = await client.get(
        "/api/wallet",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["balance"] == 0.0


@pytest.mark.asyncio
async def test_wallet_credited_on_approval(client: AsyncClient, admin_token, pending_submission):
    await client.patch(
        f"/api/admin/cards/submissions/{pending_submission}/review",
        json={"status": "approved", "admin_notes": "OK"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = await client.get(
        "/api/wallet",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.json()["balance"] > 0
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd backend && pytest tests/test_wallet.py -v`
Expected: FAIL — wallet model not defined

- [ ] **Step 3: Create wallet model**

Create `backend/app/models/wallet.py`:

```python
from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    locked_amount: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"))
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType))
    amount: Mapped[float] = mapped_column(Float)
    reference: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship("Wallet")
```

Update `backend/app/models/__init__.py`:

```python
from .wallet import Wallet, WalletTransaction, TransactionType
```

- [ ] **Step 4: Create wallet schemas**

Create `backend/app/schemas/wallet.py`:

```python
from pydantic import BaseModel
from datetime import datetime


class WalletResponse(BaseModel):
    balance: float
    currency: str
    locked_amount: float

    class Config:
        from_attributes = True


class WalletTransactionResponse(BaseModel):
    id: int
    type: str
    amount: float
    reference: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 5: Create wallet service**

Create `backend/app/services/wallet.py`:

```python
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


async def credit_wallet(db: AsyncSession, user_id: int, amount: float, reference: str, description: str = "") -> WalletTransaction:
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
```

- [ ] **Step 6: Create wallet router**

Create `backend/app/routers/wallet.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet, WalletTransaction
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
```

- [ ] **Step 7: Integrate wallet credit into admin review**

Modify the review endpoint in `backend/app/routers/admin.py`:

```python
from app.services.wallet import credit_wallet

@router.patch("/cards/submissions/{submission_id}/review", response_model=CardSubmissionResponse)
async def review_submission(
    submission_id: int,
    body: ReviewSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_staff),
):
    result = await db.execute(select(CardSubmission).where(CardSubmission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    new_status = CardSubmissionStatus(body.status)
    if new_status not in (CardSubmissionStatus.APPROVED, CardSubmissionStatus.REJECTED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

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
            description=f"Card sale approved: {submission.brand.name if hasattr(submission, 'brand') else ''}",
        )

    await db.commit()
    await db.refresh(submission)
    return submission
```

- [ ] **Step 8: Register wallet router in main.py**

Modify `backend/app/main.py`:

```python
from app.routers import auth, cards, admin, wallet
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(wallet.router)
```

- [ ] **Step 9: Generate migration and run tests**

```bash
cd backend && alembic revision --autogenerate -m "add wallet and transactions" && alembic upgrade head
pytest tests/test_wallet.py -v
```

Expected: Both wallet tests PASS

- [ ] **Step 10: Commit**

```bash
git add . && git commit -m "feat: wallet with auto-credit on submission approval"
```

---

### Task 8: SQLAdmin Setup

**Files:**
- Create: `backend/app/admin_setup.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Install SQLAdmin**

```bash
cd backend && pip install sqladmin
```

- [ ] **Step 2: Create SQLAdmin admin setup**

Create `backend/app/admin_setup.py`:

```python
from sqladmin import Admin, ModelView
from app.database import engine
from app.models.user import User
from app.models.card import CardBrand, Denomination, CardSubmission
from app.models.wallet import Wallet, WalletTransaction


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.phone, User.tier, User.kyc_status, User.is_active, User.is_staff, User.created_at]
    column_searchable_list = [User.email, User.phone]
    column_sortable_list = [User.id, User.created_at]
    form_excluded_columns = [User.password_hash]


class CardBrandAdmin(ModelView, model=CardBrand):
    column_list = [CardBrand.id, CardBrand.name, CardBrand.slug, CardBrand.active, CardBrand.created_at]
    column_searchable_list = [CardBrand.name]


class DenominationAdmin(ModelView, model=Denomination):
    column_list = [Denomination.id, Denomination.brand, Denomination.value, Denomination.currency, Denomination.active]
    form_excluded_columns = []


class CardSubmissionAdmin(ModelView, model=CardSubmission):
    column_list = [
        CardSubmission.id, CardSubmission.user, CardSubmission.brand, CardSubmission.denomination,
        CardSubmission.quoted_amount, CardSubmission.final_amount, CardSubmission.status,
        CardSubmission.submitted_at,
    ]
    column_searchable_list = [CardSubmission.admin_notes]
    form_excluded_columns = [CardSubmission.card_code_encrypted]


class WalletAdmin(ModelView, model=Wallet):
    column_list = [Wallet.id, Wallet.user, Wallet.balance, Wallet.currency, Wallet.locked_amount]


class WalletTransactionAdmin(ModelView, model=WalletTransaction):
    column_list = [WalletTransaction.id, WalletTransaction.wallet, WalletTransaction.type, WalletTransaction.amount, WalletTransaction.reference, WalletTransaction.created_at]


def setup_admin(app):
    admin = Admin(app, engine)
    admin.add_view(UserAdmin)
    admin.add_view(CardBrandAdmin)
    admin.add_view(DenominationAdmin)
    admin.add_view(CardSubmissionAdmin)
    admin.add_view(WalletAdmin)
    admin.add_view(WalletTransactionAdmin)
    return admin
```

- [ ] **Step 3: Wire up SQLAdmin in main.py**

Modify `backend/app/main.py`:

```python
from app.admin_setup import setup_admin
setup_admin(app)
```

- [ ] **Step 4: Test it starts**

Run:
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
curl http://localhost:8000/admin/
kill %1
```

Expected: Returns admin HTML page (200 OK)

- [ ] **Step 5: Commit**

```bash
git add . && git commit -m "feat: SQLAdmin setup for all core models"
```

---

## Spec Coverage Check

| Spec Requirement | Covered By |
|-----------------|------------|
| User registration + login | Task 3 |
| JWT with access + refresh tokens | Task 3 |
| Rate limiting (slowapi) | Task 4 |
| Card brands CRUD | Task 5 |
| Card submission (quote → submit) | Task 5 |
| Admin review (approve/reject) | Task 6 |
| Wallet automatic credit on approval | Task 7 |
| Wallet balance + transactions query | Task 7 |
| SQLAdmin admin panel | Task 8 |
| User model with tier + KYC status | Task 3 |
| CardSubmission with status tracking | Task 5 |
| Denomination model | Task 5 |

**Not yet covered (Phase 2+):** Pricing engine, Reloadly integration, Paystack/Flutterwave, Flutter frontend, KYC upload, disputes, notifications, encryption, audit logging, fraud rules, CSSE, admin custom Flutter screens, payout processing, Liquidity Management.
