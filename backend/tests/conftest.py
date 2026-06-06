import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db
from app.models import Base, User


@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def client(db_session):
    from app.main import limiter as main_limiter
    from app.routers.auth import limiter as auth_limiter

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    main_limiter.reset()
    auth_limiter.reset()


@pytest.fixture
async def admin_token(db_session):
    from app.services.auth import create_access_token, hash_password
    result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email="admin@test.com",
            password_hash=hash_password("testpass"),
            phone="+0000000000",
            is_staff=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
    return create_access_token(user.id)


@pytest.fixture
async def user_token(db_session):
    from app.services.auth import create_access_token, hash_password
    result = await db_session.execute(select(User).where(User.email == "user@test.com"))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email="user@test.com",
            password_hash=hash_password("UserPass123!"),
            phone="+2348011111111",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
    return create_access_token(user.id)


@pytest.fixture
async def pending_submission(db_session, admin_token):
    from app.models.card import CardBrand, Denomination, CardSubmission, CardSubmissionStatus
    from app.models.user import User
    from app.services.auth import create_access_token
    result = await db_session.execute(select(User).where(User.email == "admin@test.com"))
    admin_user = result.scalar_one()
    brand = CardBrand(name="Test Brand", slug="test-brand")
    db_session.add(brand)
    await db_session.commit()
    denom = Denomination(brand_id=brand.id, value=100.0)
    db_session.add(denom)
    await db_session.commit()
    sub = CardSubmission(
        user_id=admin_user.id, brand_id=brand.id, denomination_id=denom.id,
        card_code="test-code", quoted_amount=75.0,
        status=CardSubmissionStatus.PENDING,
    )
    db_session.add(sub)
    await db_session.commit()
    return sub.id
