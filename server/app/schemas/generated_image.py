from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, validator

class QuestionnaireData(BaseModel):
    setting: str
    clothing: str
    pose: str
    additional_notes: Optional[str] = ""

class GenerationRequest(BaseModel):
    photo_id: int
    frame_id: Optional[int] = None  # Сделаем frame_id опциональным
    questionnaire: QuestionnaireData
    theme: str
    style: str
    enhance_face: bool

class GenerationResponse(BaseModel):
    id: int
    status: str
    progress: int
    estimated_time_remaining: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    generated_image_url: Optional[str] = None  # С водяным знаком
    numbered_image_url: Optional[str] = None   # Разбитое по номерам с водяным знаком
    preview_image_url: Optional[str] = None
    error_message: Optional[str] = None
    colors_used: Optional[List[str]] = None    # Используемые цвета
    complexity_score: Optional[int] = None     # Сложность (количество цветов)
    generation_time_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class GeneratedImageResponse(BaseModel):
    id: int
    user_id: Optional[int]
    original_photo_id: int
    frame_id: Optional[int] = None  # Сделаем frame_id опциональным
    generated_image_url: Optional[str] = None  # URL с водяным знаком
    numbered_image_url: Optional[str] = None   # URL разбитого по номерам с водяным знаком
    preview_image_url: Optional[str] = None
    status: str
    progress: int
    generation_parameters: Optional[Dict[str, Any]] = None
    questionnaire_answers: Optional[Dict[str, Any]] = None
    colors_used: Optional[List[str]] = None
    complexity_score: Optional[int] = None
    generation_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
    @validator('generated_image_url', 'numbered_image_url', pre=True, always=True)
    def ensure_absolute_url(cls, v, values):
        """Обеспечиваем абсолютные URL для изображений"""
        if v and not v.startswith('http') and not v.startswith('/'):
            return f"/static/generated_images/{v}"
        return v


class GenerationStatus(BaseModel):
    id: int
    status: str  
    progress: int
    estimated_time_remaining: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GenerationUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    generated_image_url: Optional[str] = None
    numbered_image_url: Optional[str] = None
    error_message: Optional[str] = None
    colors_used: Optional[List[str]] = None
    complexity_score: Optional[int] = None
    generation_time_seconds: Optional[float] = None

    @validator('progress')
    def progress_range(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Прогресс должен быть от 0 до 100')
        return v