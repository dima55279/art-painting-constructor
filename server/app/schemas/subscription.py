from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator

class SubscriptionPlan(BaseModel):
    plan_type: str 
    plan_name: str
    billing_cycle: str  
    price_per_cycle: float
    generation_limit: Optional[int] = None
    max_photo_size: int = 10485760  
    premium_frames_access: bool = False
    priority_processing: bool = False
    features: List[str] = []

    @validator('billing_cycle')
    def validate_billing_cycle(cls, v):
        if v not in ["monthly", "yearly"]:
            raise ValueError('Цикл оплаты должен быть "monthly" или "yearly"')
        return v

    @validator('plan_type')
    def validate_plan_type(cls, v):
        if v not in ["basic", "premium", "enterprise"]:
            raise ValueError('Тип плана должен быть "basic", "premium" или "enterprise"')
        return v

class SubscriptionCreate(BaseModel):
    plan_type: str
    billing_cycle: str = "monthly"
    payment_method: str
    auto_renew: bool = True

    @validator('payment_method')
    def validate_payment_method(cls, v):
        valid_methods = ["credit_card", "paypal", "bank_transfer"]
        if v not in valid_methods:
            raise ValueError(f'Метод оплаты должен быть одним из: {", ".join(valid_methods)}')
        return v

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan_type: str
    plan_name: str
    billing_cycle: str
    price_per_cycle: float
    generation_limit: Optional[int] = None
    max_photo_size: int
    premium_frames_access: bool
    priority_processing: bool
    status: str
    auto_renew: bool
    start_date: datetime
    end_date: datetime
    cancelled_at: Optional[datetime] = None
    renewed_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    last_payment_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None

    is_active: bool
    days_remaining: int
    features: List[str] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        result = super().from_orm(obj)
        result.is_active = obj.status == "active" and obj.end_date.replace(tzinfo=None) > datetime.utcnow()

        if obj.end_date:
            remaining = obj.end_date.replace(tzinfo=None) - datetime.utcnow()
            result.days_remaining = max(0, remaining.days)
        else:
            result.days_remaining = 0
            
        if obj.plan_type == "basic":
            result.features = ["5 генераций в месяц", "Базовые рамки", "Стандартная обработка"]
        elif obj.plan_type == "premium":
            result.features = ["Неограниченные генерации", "Все рамки", "Приоритетная обработка", "Улучшенное качество"]
        elif obj.plan_type == "enterprise":
            result.features = ["Неограниченные генерации", "Все рамки", "Максимальный приоритет", "Экспорт в высоком качестве", "Персональная поддержка"]
            
        return result

class SubscriptionUpdate(BaseModel):
    auto_renew: Optional[bool] = None
    payment_method: Optional[str] = None

class SubscriptionCancel(BaseModel):
    reason: Optional[str] = None
    feedback: Optional[str] = None

class SubscriptionUsage(BaseModel):
    plan_type: str
    generations_used: int
    generations_limit: Optional[int] = None
    usage_percentage: float
    reset_date: datetime  
    days_until_reset: int

    class Config:
        from_attributes = True