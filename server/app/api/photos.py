import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_active_user  # Добавлен импорт get_current_active_user
from app.models.user import User
from app.models.photo import Photo
from app.schemas.photo import PhotoResponse, PhotoUpload, FaceDetectionResult
from app.services.photo_service import PhotoService
from app.services.face_detection import FaceDetectionService
from app.config import settings

router = APIRouter()

@router.post("/upload", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_optional),  # Опциональная аутентификация
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузка фотографии пользователя с проверкой наличия лица
    Доступно для неавторизованных пользователей
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением"
        )

    # Читаем содержимое файла
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Размер файла не должен превышать {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
        )
    
    await file.seek(0)  # Сбрасываем позицию чтения
    
    photo_service = PhotoService(db)
    face_service = FaceDetectionService()
    
    try:
        # Сохраняем файл временно для проверки
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        user_id = current_user.id if current_user else None
        temp_path = os.path.join(temp_dir, f"temp_{user_id or 'anonymous'}_{file.filename}")
        
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Проверяем наличие лица
        face_detected = await face_service.detect_faces(temp_path)
        
        if not face_detected:
            # Удаляем временный файл
            os.remove(temp_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="На фотографии не обнаружено лицо. Пожалуйста, загрузите фото с четко видимым лицом."
            )
        
        # Если лицо обнаружено, загружаем фото
        photo = await photo_service.upload_photo(
            user_id=user_id,  # Может быть None для неавторизованных
            file=file,
            file_content=file_content,
            photo_data=PhotoUpload()  # Пустые данные, так как у нас нет формы
        )
        
        # Запускаем анализ качества в фоне только для авторизованных пользователей
        if current_user:
            background_tasks.add_task(
                analyze_face_quality_after_upload,
                photo.id,
                db
            )
        
        return PhotoResponse.from_orm(photo)
        
    except HTTPException:
        raise
    except Exception as e:
        # Очищаем временные файлы в случае ошибки
        user_id = current_user.id if current_user else None
        temp_path = os.path.join("temp_uploads", f"temp_{user_id or 'anonymous'}_{file.filename}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке фотографии: {str(e)}"
        )

async def analyze_face_quality_after_upload(photo_id: int, db: AsyncSession):
    """Фоновая задача для анализа качества загруженного фото"""
    photo_service = PhotoService(db)
    face_service = FaceDetectionService()
    
    try:
        await photo_service.analyze_photo_quality(photo_id, face_service)
    except Exception as e:
        print(f"Error analyzing photo quality {photo_id}: {str(e)}")

@router.get("/", response_model=list[PhotoResponse])
async def get_user_photos(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),  # Только для авторизованных
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка фотографий пользователя
    Только для авторизованных пользователей
    """
    photo_service = PhotoService(db)
    photos = await photo_service.get_user_photos(current_user.id, skip, limit)
    return [PhotoResponse.from_orm(photo) for photo in photos]

@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: int,
    current_user: User = Depends(get_current_active_user),  # Только для авторизованных
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о конкретной фотографии
    Только для авторизованных пользователей
    """
    photo_service = PhotoService(db)
    photo = await photo_service.get_photo(photo_id, current_user.id)
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена"
        )
    
    return PhotoResponse.from_orm(photo)

@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: int,
    current_user: User = Depends(get_current_active_user),  # Только для авторизованных
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление фотографии
    Только для авторизованных пользователей
    """
    photo_service = PhotoService(db)
    success = await photo_service.delete_photo(photo_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена или у вас нет прав для ее удаления"
        )
    
    return {"message": "Фотография успешно удалена"}

@router.post("/{photo_id}/analyze-face", response_model=FaceDetectionResult)
async def analyze_face(
    photo_id: int,
    current_user: User = Depends(get_current_active_user),  # Только для авторизованных
    db: AsyncSession = Depends(get_db)
):
    """
    Анализ лица на фотографии
    Только для авторизованных пользователей
    """
    photo_service = PhotoService(db)
    face_service = FaceDetectionService()
    
    photo = await photo_service.get_photo(photo_id, current_user.id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена"
        )
    
    result = await photo_service.analyze_photo_quality(photo_id, face_service)
    return result

@router.get("/{photo_id}/download")
async def download_photo(
    photo_id: int,
    current_user: User = Depends(get_current_active_user),  # Только для авторизованных
    db: AsyncSession = Depends(get_db)
):
    """
    Скачивание оригинальной фотографии
    Только для авторизованных пользователей
    """
    photo_service = PhotoService(db)
    photo = await photo_service.get_photo(photo_id, current_user.id)
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена"
        )
    
    file_path = photo.file_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл фотографии не найден"
        )
    
    return {"file_url": f"/static/uploaded_photos/{photo.stored_filename}"}