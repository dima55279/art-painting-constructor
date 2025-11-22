import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import UploadFile, HTTPException

from app.models.user import User
from app.models.photo import Photo
from app.models.order import Order
from app.models.generated_image import GeneratedImage
from app.schemas.user import UserUpdate
from app.utils.security import get_password_hash
from app.config import settings

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Обновление данных пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def upload_avatar(self, user_id: int, file: UploadFile) -> str:
        """Загрузка аватара пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        avatars_dir = os.path.join(settings.UPLOAD_DIR, "avatars")
        os.makedirs(avatars_dir, exist_ok=True)

        file_extension = os.path.splitext(file.filename)[1]
        filename = f"avatar_{user_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(avatars_dir, filename)

        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        avatar_url = f"/static/uploaded_photos/avatars/{filename}"
        user.avatar_url = avatar_url
        await self.db.commit()

        return avatar_url

    async def delete_avatar(self, user_id: int) -> bool:
        """Удаление аватара пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user or not user.avatar_url:
            return False

        filename = user.avatar_url.split("/")[-1]
        file_path = os.path.join(settings.UPLOAD_DIR, "avatars", filename)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass

        user.avatar_url = None
        await self.db.commit()
        return True

    async def get_user_profile(self, user_id: int) -> dict:
        """Получение полного профиля пользователя"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # Получаем статистику
        photos_count = await self._get_user_photos_count(user_id)
        orders_count = await self._get_user_orders_count(user_id)
        generated_images_count = await self._get_user_generated_images_count(user_id)

        # Временно возвращаем упрощенные данные
        return {
            "photos_count": photos_count,
            "orders_count": orders_count,
            "generated_images_count": generated_images_count,
            "active_subscription": None,  # Можно добавить логику позже
            "recent_photos": [],  # Можно добавить логику позже
            "recent_orders": []   # Можно добавить логику позже
        }

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики пользователя"""
        photos_count = await self._get_user_photos_count(user_id)
        orders_count = await self._get_user_orders_count(user_id)
        generated_images_count = await self._get_user_generated_images_count(user_id)

        return {
            "photos_count": photos_count,
            "orders_count": orders_count,
            "generated_images_count": generated_images_count,
            "successful_generations": await self._get_successful_generations_count(user_id)
        }

    async def _get_user_photos_count(self, user_id: int) -> int:
        """Получение количества фотографий пользователя"""
        result = await self.db.execute(
            select(func.count(Photo.id)).where(Photo.user_id == user_id)
        )
        return result.scalar() or 0

    async def _get_user_orders_count(self, user_id: int) -> int:
        """Получение количества заказов пользователя"""
        result = await self.db.execute(
            select(func.count(Order.id)).where(Order.user_id == user_id)
        )
        return result.scalar() or 0

    async def _get_user_generated_images_count(self, user_id: int) -> int:
        """Получение количества сгенерированных изображений"""
        result = await self.db.execute(
            select(func.count(GeneratedImage.id)).where(GeneratedImage.user_id == user_id)
        )
        return result.scalar() or 0

    async def _get_successful_generations_count(self, user_id: int) -> int:
        """Получение количества успешных генераций"""
        result = await self.db.execute(
            select(func.count(GeneratedImage.id)).where(
                GeneratedImage.user_id == user_id,
                GeneratedImage.status == "completed"
            )
        )
        return result.scalar() or 0

    async def send_verification_email(self, user_id: int) -> None:
        """Отправка email для верификации (заглушка)"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        # В реальном приложении здесь будет логика отправки email
        print(f"Sending verification email to {user.email}")

    async def verify_email_token(self, token: str) -> None:
        """Верификация email по токену (заглушка)"""
        # В реальном приложении здесь будет проверка токена
        # Пока просто имитируем успешную верификацию
        print(f"Verifying email token: {token}")