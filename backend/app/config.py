"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./waste.db"
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    DEMO_MODE: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
