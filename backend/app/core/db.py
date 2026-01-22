"""
Referenced https://github.com/fastapi/full-stack-fastapi-template/blob/master/backend/app/core/db.py
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

# Create async engine
# echo=True logs SQL queries (useful for debug)
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=settings.DEBUG,
    future=True,
)

# Session factory for creating database sessions
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keep objects usable after commit
    autoflush=False,
)


async def init_db() -> None:
    """
    Initialize database tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    """
    await engine.dispose()
