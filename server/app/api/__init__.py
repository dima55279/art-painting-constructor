"""
API роутеры для Art Painting Constructor
"""

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.photos import router as photos_router
from app.api.frames import router as frames_router
from app.api.generate import router as generate_router
from app.api.orders import router as orders_router
from app.api.subscription import router as subscription_router
from app.api.questionnaire import router as questionnaire_router
from app.api.questionnaire_public import router as questionnaire_public_router

__all__ = [
    "auth_router",
    "users_router", 
    "photos_router",
    "frames_router",
    "generate_router",
    "orders_router",
    "subscription_router",
    "questionnaire_router",
    "questionnaire_public_router"
]