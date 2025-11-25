import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_active_user  # Добавляем импорт
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
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    print(f"👤 Upload photo - User: {current_user.id if current_user else 'anonymous'}")
    
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
    
    photo_service = PhotoService(db)
    face_service = FaceDetectionService()
    
    # Определяем session_id или user_id
    session_id = None
    user_id = None
    
    if current_user:
        user_id = current_user.id
        print(f"✅ Авторизованный пользователь: {user_id}")
    else:
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = f"anon_{uuid.uuid4().hex}"
        print(f"👤 Анонимный пользователь, session_id: {session_id}")

    try:
        # Сохраняем файл временно для проверки
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Проверяем наличие лица
        face_detected = await face_service.detect_faces(temp_path)
        
        # Удаляем временный файл после проверки
        try:
            os.remove(temp_path)
        except OSError:
            pass
        
        if not face_detected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="На фотографии не обнаружено лицо. Пожалуйста, загрузите фото с четко видимым лицом."
            )
        
        # Если лицо обнаружено, загружаем фото
        if current_user:
            photo = await photo_service.upload_photo(
                user_id=user_id,
                file=file,
                file_content=file_content,
                photo_data=PhotoUpload()
            )
        else:
            photo = await photo_service.upload_photo_for_anonymous(
                file=file,
                file_content=file_content,
                session_id=session_id
            )
        
        return PhotoResponse.from_orm(photo)
        
    except HTTPException:
        raise
    except Exception as e:
        # Очищаем временные файлы в случае ошибки
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
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
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
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
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
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
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
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
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
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
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
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