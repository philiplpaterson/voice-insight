from fastapi import APIRouter

from app.api.routes import calls
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(calls.router)