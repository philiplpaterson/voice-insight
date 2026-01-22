"""
Core configuration settings.
"""

import secrets
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file="../.env", # to use top level .env file above ./backend/
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    PROJECT_NAME: str = "VoiceInsight"
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = ""
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
    
    LOCAL_UPLOAD_DIR: str = "./uploads"
    DOCKER_UPLOAD_DIR: str = "/app/uploads"

    @computed_field
    @property
    def UPLOAD_DIR(self) -> str:
        if self.ENVIRONMENT == "local":
            return self.LOCAL_UPLOAD_DIR
        return self.DOCKER_UPLOAD_DIR

    @computed_field  # type: ignore[prop-decorator]
    @property
    def UPLOAD_PATH(self) -> Path:
        """Get upload directory as Path, create if doesn't exist."""
        upload_path = Path(self.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:5173"]


settings = Settings()  # type: ignore
