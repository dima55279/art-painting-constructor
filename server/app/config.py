# app/config.py
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Настройки приложения через переменные окружения"""

    # Принудительно используем SQLite для разработки
    DATABASE_URL: str = "sqlite+aiosqlite:///./art_painting.db"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    APP_NAME: str = "Art Painting Constructor API"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "static/uploaded_photos")
    GENERATED_IMAGES_DIR: str = os.getenv("GENERATED_IMAGES_DIR", "static/generated_images")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    AI_GENERATION_SERVICE_URL: Optional[str] = os.getenv("AI_GENERATION_SERVICE_URL")
    AI_API_KEY: Optional[str] = os.getenv("AI_API_KEY")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_cors_origins(self) -> list:
        """Получить список разрешенных CORS origins"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()