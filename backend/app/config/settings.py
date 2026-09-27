import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AeroCPI"
    VERSION: str = "0.1.0-milestone1"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "aerocpi"
    POSTGRES_PASSWORD: str = "aerocpi_secret_password"
    POSTGRES_DB: str = "aerocpi_db"
    POSTGRES_PORT: int = 5432
    
    DATABASE_URL: Optional[str] = None

    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.POSTGRES_SERVER and self.POSTGRES_SERVER != "localhost":
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
        import pathlib
        backend_dir = pathlib.Path(__file__).resolve().parents[3]
        db_file = backend_dir / "aerocpi_dev.db"
        return f"sqlite:///{db_file}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
