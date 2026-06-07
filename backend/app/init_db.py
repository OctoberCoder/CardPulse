"""Initialize database tables (for fresh deployments)."""
import asyncio
from app.database import engine
from app.models import Base


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")


if __name__ == "__main__":
    asyncio.run(init())
