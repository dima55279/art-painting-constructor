import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import UploadFile, HTTPException

from app.models.photo import Photo
from app.models.user import User
from app.schemas.photo import PhotoUpload, FaceDetectionResult
from app.services.face_detection import FaceDetectionService
from app.config import settings

class PhotoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_photo(
        self, 
        user_id: Optional[int],  # Может быть None для неавторизованных
        file: UploadFile, 
        file_content: bytes,
        photo_data: PhotoUpload
    ) -> Photo:
        """Загрузка и сохранение фотографии пользователя"""
        file_extension = os.path.splitext(file.filename)[1]
        stored_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        photo = Photo(
            user_id=user_id,  # Может быть None
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size=len(file_content),
            mime_type=file.content_type,
            uploaded_at=datetime.utcnow(),
            face_detected=True,  # Уже проверили перед загрузкой
            is_approved=True     # Одобряем, так как лицо найдено
        )

        self.db.add(photo)
        await self.db.commit()
        await self.db.refresh(photo)

        return photo

    async def get_photo(self, photo_id: int, user_id: Optional[int] = None) -> Optional[Photo]:
        """Получение фотографии по ID с проверкой владельца (если user_id указан)"""
        if user_id is not None:
            result = await self.db.execute(
                select(Photo).where(
                    Photo.id == photo_id,
                    Photo.user_id == user_id
                )
            )
        else:
            result = await self.db.execute(
                select(Photo).where(Photo.id == photo_id)
            )
        return result.scalar_one_or_none()

    async def get_user_photos(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Photo]:
        """Получение списка фотографий пользователя"""
        result = await self.db.execute(
            select(Photo)
            .where(Photo.user_id == user_id)
            .order_by(Photo.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_photo(self, photo_id: int, user_id: int) -> bool:
        """Удаление фотографии"""
        photo = await self.get_photo(photo_id, user_id)
        if not photo:
            return False

        try:
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
        except OSError:
            print(f"Error deleting file: {photo.file_path}")

        await self.db.delete(photo)
        await self.db.commit()
        return True

    async def analyze_photo_quality(self, photo_id: int, face_service: FaceDetectionService) -> FaceDetectionResult:
        """Анализ качества лица на фотографии"""
        photo = await self.db.get(Photo, photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Фотография не найдена")

        try:
            # Анализируем качество лица
            quality_result = await face_service.validate_face_quality(photo.file_path)
            
            # Обновляем информацию о фото
            photo.face_quality_score = quality_result.get("quality_score")
            photo.face_analysis_data = quality_result
            photo.processed_at = datetime.utcnow()

            # Если качество недостаточное, помечаем как неодобренное
            if not quality_result.get("is_acceptable", False):
                photo.is_approved = False

            await self.db.commit()

            return FaceDetectionResult(
                face_detected=True,
                faces_count=quality_result.get("faces_count", 1),
                quality_score=photo.face_quality_score,
                message="Анализ качества завершен",
                issues=quality_result.get("issues", [])
            )

        except Exception as e:
            photo.processed_at = datetime.utcnow()
            await self.db.commit()
            
            raise HTTPException(
                status_code=500, 
                detail=f"Ошибка при анализе качества фотографии: {str(e)}"
            )

    async def approve_photo(self, photo_id: int, user_id: int) -> bool:
        """Ручное одобрение фотографии"""
        photo = await self.get_photo(photo_id, user_id)
        if not photo:
            return False

        photo.is_approved = True
        photo.rejection_reason = None
        await self.db.commit()
        return True

    async def reject_photo(self, photo_id: int, user_id: int, reason: str) -> bool:
        """Отклонение фотографии с указанием причины"""
        photo = await self.get_photo(photo_id, user_id)
        if not photo:
            return False

        photo.is_approved = False
        photo.rejection_reason = reason
        await self.db.commit()
        return True

    async def get_photo_stats(self, user_id: int) -> Dict[str, Any]:
        """Статистика по фотографиям пользователя"""
        total_result = await self.db.execute(
            select(func.count(Photo.id)).where(Photo.user_id == user_id)
        )
        total_photos = total_result.scalar()

        with_faces_result = await self.db.execute(
            select(func.count(Photo.id)).where(
                Photo.user_id == user_id,
                Photo.face_detected == True
            )
        )
        photos_with_faces = with_faces_result.scalar()

        approved_result = await self.db.execute(
            select(func.count(Photo.id)).where(
                Photo.user_id == user_id,
                Photo.is_approved == True
            )
        )
        approved_photos = approved_result.scalar()

        return {
            "total_photos": total_photos,
            "photos_with_faces": photos_with_faces,
            "approved_photos": approved_photos,
            "approval_rate": approved_photos / total_photos if total_photos > 0 else 0
        }