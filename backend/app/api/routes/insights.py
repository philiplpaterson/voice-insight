from fastapi import APIRouter, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import AsyncSessionDep
from app.crud import insight_crud
from app.models import InsightRead, InsightType

router = APIRouter()


@router.get("/", response_model=list[InsightRead])
async def list_insights_by_type(
    *,
    session: AsyncSessionDep,
    insight_type: InsightType = Query(..., description="Type of insight to retrieve"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[InsightRead]:
    """
    Get all insights of a specific type across all calls.
    """
    insights = await insight_crud.get_by_type(
        session,
        insight_type=insight_type,
        skip=skip,
        limit=limit,
    )
    return [InsightRead.model_validate(i) for i in insights]


@router.get("/call/{call_id}", response_model=list[InsightRead])
async def list_insights_for_call(
    *,
    call_id: int,
    session: AsyncSessionDep,
    insight_type: InsightType | None = Query(None, description="Filter by type"),
) -> list[InsightRead]:
    """
    Get all insights for a specific call, optionally filtered by type.
    """
    insights = await insight_crud.get_by_call(
        session,
        call_id=call_id,
        insight_type=insight_type,
    )
    return [InsightRead.model_validate(i) for i in insights]
