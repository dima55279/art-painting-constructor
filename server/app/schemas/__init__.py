"""
Pydantic схемы для валидации и сериализации данных
"""

from app.schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse,
    UserLogin,
    UserProfile,
    UserInDB
)
from app.schemas.photo import (
    PhotoUpload,
    PhotoResponse,
    PhotoUpdate,
    PhotoInDB
)
from app.schemas.frame import (
    FrameCreate,
    FrameResponse,
    FrameUpdate,
    FrameSelection
)
from app.schemas.generated_image import (
    GenerationRequest,
    GenerationResponse,
    GenerationStatus,
    GeneratedImageResponse
)
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
    OrderSummary
)
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
    SubscriptionPlan
)

from app.schemas.questionnaire import (  # Добавляем анкету
    QuestionnaireData,
    QuestionnaireResponse,
    QuestionnaireAnalysis
)

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse", "UserLogin", "UserProfile", "UserInDB",

    "PhotoUpload", "PhotoResponse", "PhotoUpdate", "PhotoInDB",

    "FrameCreate", "FrameResponse", "FrameUpdate", "FrameSelection",

    "GenerationRequest", "GenerationResponse", "GenerationStatus", "GeneratedImageResponse",

    "OrderCreate", "OrderResponse", "OrderUpdate", "OrderSummary",

    "SubscriptionCreate", "SubscriptionResponse", "SubscriptionUpdate", "SubscriptionPlan",
    
    "QuestionnaireData", "QuestionnaireResponse", "QuestionnaireAnalysis"  # Добавляем в экспорт
]