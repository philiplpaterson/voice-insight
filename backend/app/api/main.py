from fastapi import APIRouter

from app.api.routes import calls, insights

api_router = APIRouter()
api_router.include_router(calls.router)
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])