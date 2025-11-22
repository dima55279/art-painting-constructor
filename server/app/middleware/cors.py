from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.config import settings

def setup_cors(app: FastAPI) -> None:
    """
    Настройка CORS middleware
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def get_cors_config(environment: str = "development") -> dict:
    """
    Получение конфигурации CORS в зависимости от окружения
    """
    base_config = {
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-CSRF-Token",
        ],
    }
    
    if environment == "development":
        base_config["allow_origins"] = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]
    elif environment == "staging":
        base_config["allow_origins"] = [
            "https://staging.art-painting.com",
            "https://staging-api.art-painting.com",
        ]
    elif environment == "production":
        base_config["allow_origins"] = [
            "https://art-painting.com",
            "https://www.art-painting.com",
        ]
    else:
        base_config["allow_origins"] = ["*"]
    
    return base_config