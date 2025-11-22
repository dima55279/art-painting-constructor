from typing import Optional, Dict, Any
from pydantic import BaseModel, validator

class QuestionnaireData(BaseModel):
    """Данные анкеты для генерации изображения"""
    setting: str
    clothing: str
    pose: str
    additional_notes: Optional[str] = None
    
    @validator('setting', 'clothing', 'pose')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Поле не может быть пустым')
        return v.strip()

class QuestionnaireResponse(BaseModel):
    """Ответ после обработки анкеты"""
    success: bool
    message: str
    questionnaire_id: Optional[int] = None
    recommendations: Optional[Dict[str, Any]] = None

class QuestionnaireAnalysis(BaseModel):
    """Анализ анкеты для нейросети"""
    mood: str
    style_preferences: list
    color_palette: list
    complexity_level: int
    artistic_style: str