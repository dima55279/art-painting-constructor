from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, validator

class QuestionnaireData(BaseModel):
    setting: str
    clothing: str
    pose: str
    additional_notes: Optional[str] = None

class GenerationRequest(BaseModel):
    photo_id: int
    frame_id: int
    questionnaire: QuestionnaireData
    theme: str = "dark"  
    style: Optional[str] = "realistic"  
    enhance_face: bool = True

    @validator('theme')
    def theme_valid(cls, v):
        if v not in ['dark', 'light']:
            raise ValueError('Тема должна быть "dark" или "light"')
        return v

    @validator('photo_id', 'frame_id')
    def ids_positive(cls, v):
        if v <= 0:
            raise ValueError('ID должен быть положительным числом')
        return v

class GenerationStatus(BaseModel):
    generation_id: int
    status: str  
    progress: int
    estimated_time_remaining: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GenerationResponse(GenerationStatus):
    generated_image_url: Optional[str] = None
    numbered_image_url: Optional[str] = None
    preview_image_url: Optional[str] = None
    error_message: Optional[str] = None
    colors_used: Optional[List[str]] = None
    complexity_score: Optional[int] = None
    generation_time_seconds: Optional[float] = None

    class Config:
        from_attributes = True

class GeneratedImageResponse(BaseModel):
    id: int
    user_id: int
    original_photo_id: int
    frame_id: int
    generated_image_url: str
    numbered_image_url: Optional[str] = None
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

    frame: 'FrameResponse'
    original_photo: 'PhotoResponse'

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

from app.schemas.frame import FrameResponse
from app.schemas.photo import PhotoResponse

GeneratedImageResponse.update_forward_refs()