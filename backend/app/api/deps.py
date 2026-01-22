from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.

    Yields an async database session for use in route handlers.
    Session is automatically closed after the request completes.
    """
    async with async_session_maker() as session:
        yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_db)]