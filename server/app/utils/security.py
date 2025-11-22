# app/utils/security.py
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any, Union
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.config import settings

# Простое хеширование для разработки
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Простая проверка пароля для разработки"""
    try:
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Простое хеширование пароля для разработки"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Создание JWT токена доступа"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Union[dict, None]:
    """Верификация JWT токена"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

# Остальные функции можно временно закомментировать или упростить
def generate_api_key() -> str:
    """Генерация API ключа"""
    import secrets
    return f"apk_{secrets.token_urlsafe(32)}"

def generate_secret_key() -> str:
    """Генерация секретного ключа"""
    import secrets
    return secrets.token_urlsafe(64)

def validate_password_strength(password: str) -> dict:
    """Проверка сложности пароля (упрощенная)"""
    issues = []
    
    if len(password) < 6:
        issues.append("Пароль должен содержать минимум 6 символов")
    
    return {
        "is_strong": len(issues) == 0,
        "issues": issues,
        "score": max(0, 5 - len(issues)) 
    }

def decode_access_token(token: str):
    """
    Декодирование JWT токена
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )