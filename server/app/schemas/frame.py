from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, validator

class FrameBase(BaseModel):
    name: str
    description: Optional[str] = None
    frame_type: str
    preview_image_url: str
    model_3d_url: Optional[str] = None

    class Config:
        protected_namespaces = ()

class FrameCreate(FrameBase):
    price: float = 0.0
    is_premium: bool = False
    complexity_level: int = 1
    estimated_time_hours: float = 2.0
    tags: Optional[List[str]] = None
    camera_settings: Optional[Dict[str, Any]] = None
    sort_order: int = 0

    @validator('complexity_level')
    def complexity_in_range(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Сложность должна быть от 1 до 5')
        return v

    @validator('price')
    def price_non_negative(cls, v):
        if v < 0:
            raise ValueError('Цена не может быть отрицательной')
        return v

class FrameResponse(FrameBase):
    id: int
    price: float
    is_premium: bool
    is_active: bool
    complexity_level: int
    estimated_time_hours: float
    tags: Optional[List[str]] = None
    camera_settings: Optional[Dict[str, Any]] = None
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    price_display: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        result = super().from_orm(obj)
        result.price_display = f"${obj.price:.2f}" if obj.price > 0 else "Бесплатно"
        return result

class FrameUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    complexity_level: Optional[int] = None
    tags: Optional[List[str]] = None
    sort_order: Optional[int] = None

class FrameSelection(BaseModel):
    frame_id: int

    @validator('frame_id')
    def frame_id_positive(cls, v):
        if v <= 0:
            raise ValueError('ID рамки должен быть положительным числом')
        return v

class FrameList(BaseModel):
    frames: List[FrameResponse]
    total: int
    page: int
    page_size: int
    total_pages: int