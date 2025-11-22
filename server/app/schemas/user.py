from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator, constr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: constr(min_length=6, max_length=100)
    password_confirm: str

    @validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Имя пользователя должно содержать только буквы, цифры и подчеркивания')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    email_verified: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    hashed_password: str

    class Config:
        from_attributes = True

class UserProfile(UserResponse):
    photos_count: int = 0
    orders_count: int = 0
    generated_images_count: int = 0
    active_subscription: Optional[dict] = None
    recent_photos: List[dict] = []
    recent_orders: List[dict] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None