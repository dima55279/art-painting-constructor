# app/services/auth_service.py
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import verify_password, get_password_hash
from app.config import settings

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.invalid_tokens = set()

    async def get_user_dict(self, user_id: int) -> dict:
        """Получение данных пользователя в виде словаря (без проблем с асинхронностью)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return {}
        
        # Используем прямой SQL запрос чтобы избежать проблем с ORM
        from sqlalchemy import text
        result = await self.db.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        user_data = result.mappings().first()
        
        if user_data:
            return dict(user_data)
        return {}

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Поиск пользователя по имени"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Поиск пользователя по email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Поиск пользователя по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        try:
            user = await self.get_user_by_username(username)
            if not user:
                return None
            
            if not verify_password(password, user.hashed_password):
                return None
            
            return user
        except Exception as e:
            print(f"Error in authenticate_user: {str(e)}")
            return None

    async def create_user(self, user_data: UserCreate) -> User:
        """Создание нового пользователя"""
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise ValueError("Пользователь с таким именем уже существует")
        
        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise ValueError("Пользователь с таким email уже существует")

        user = User(
            username=user_data.username,
            email=user_data.email,
            phone=getattr(user_data, 'phone', None),
            first_name=getattr(user_data, 'first_name', None),
            last_name=getattr(user_data, 'last_name', None),
            hashed_password=get_password_hash(user_data.password),
            email_verified=False,
            is_active=True,
            is_superuser=False,
            created_at=datetime.utcnow()
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def update_last_login(self, user_id: int) -> None:
        """Обновление времени последнего входа"""
        user = await self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.db.commit()

    async def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Смена пароля пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        if not verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def reset_password(self, email: str, new_password: str) -> bool:
        """Сброс пароля по email"""
        user = await self.get_user_by_email(email)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        return True

    async def logout_user(self, user_id: int) -> None:
        """Выход пользователя"""
        pass

    async def send_welcome_email(self, user: User) -> None:
        """Отправка приветственного email (заглушка)"""
        print(f"Sending welcome email to {user.email}")
    
    async def invalidate_token(self, token: str) -> None:
        """Добавляет токен в черный список"""
        self.invalid_tokens.add(token)
        # В реальном приложении здесь нужно использовать Redis или БД
        print(f"Token invalidated: {token[:50]}...")
    
    async def is_token_valid(self, token: str) -> bool:
        """Проверяет, не находится ли токен в черном списке"""
        return token not in self.invalid_tokens
    
    async def logout_user(self, user_id: int) -> None:
        """Выход пользователя - в текущей реализации просто логируем"""
        print(f"User {user_id} logged out")
        # В реальном приложении здесь можно инвалидировать все токены пользователя