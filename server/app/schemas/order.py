from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, validator
from app.schemas.generated_image import GeneratedImageResponse

class ShippingAddress(BaseModel):
    full_name: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    phone: str
    email: str
    instructions: Optional[str] = None

class OrderCreate(BaseModel):
    generated_image_id: int
    painting_size: str  
    materials_included: bool = True
    shipping_address: ShippingAddress
    shipping_method: str = "standard"  
    promo_code: Optional[str] = None

    @validator('painting_size')
    def validate_size(cls, v):
        valid_sizes = ["30x40", "40x50", "50x70", "60x80"]
        if v not in valid_sizes:
            raise ValueError(f'Размер должен быть одним из: {", ".join(valid_sizes)}')
        return v

    @validator('shipping_method')
    def validate_shipping(cls, v):
        if v not in ["standard", "express"]:
            raise ValueError('Метод доставки должен быть "standard" или "express"')
        return v

class OrderResponse(BaseModel):
    id: int
    order_number: str
    user_id: int
    generated_image_id: int
    painting_name: str
    painting_size: str
    materials_included: bool
    shipping_address: Dict[str, Any]
    shipping_method: str
    tracking_number: Optional[str] = None
    status: str
    payment_status: str
    base_price: float
    frame_price: float
    shipping_price: float
    discount_amount: float
    total_price: float
    promo_code: Optional[str] = None
    discount_reason: Optional[str] = None
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    generated_image: GeneratedImageResponse

    can_be_cancelled: bool
    estimated_delivery_date: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        result = super().from_orm(obj)
        result.can_be_cancelled = obj.status in ["pending", "confirmed"]
        return result

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    tracking_number: Optional[str] = None
    shipping_method: Optional[str] = None

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Статус должен быть одним из: {", ".join(valid_statuses)}')
        return v

class OrderSummary(BaseModel):
    id: int
    order_number: str
    painting_name: str
    status: str
    total_price: float
    created_at: datetime
    preview_image_url: Optional[str] = None

    class Config:
        from_attributes = True

class OrderList(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

from app.schemas.generated_image import GeneratedImageResponse

OrderResponse.update_forward_refs()