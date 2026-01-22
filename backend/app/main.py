from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.db import close_db, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup: Initialize database tables
    Shutdown: Close database connections
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Voice-First Audio Call Intelligence. Upload, transcribe, and analyze calls.",
    version="0.1.0",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs",
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
