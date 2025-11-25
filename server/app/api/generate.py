import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_active_user  # Добавляем импорт
from app.models.user import User
from app.schemas.generated_image import GenerationRequest, GenerationResponse, GenerationStatus, GeneratedImageResponse
from app.services.generation_service import GenerationService
from app.services.photo_service import PhotoService
from app.services.frame_service import FrameService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_image(
    background_tasks: BackgroundTasks,
    request: Request,
    generation_data: GenerationRequest = Body(..., embed=False),  # Ключевое изменение!
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    print("🔄 === GENERATION REQUEST STARTED ===")
    
    print(f"📧 User: {current_user.id if current_user else 'anonymous'}")
    print(f"📦 Request data: {generation_data.dict()}")
    print(f"🤖 Using additional_notes: {generation_data.questionnaire.additional_notes}")

    generation_service = GenerationService(db)
    photo_service = PhotoService(db)
    frame_service = FrameService(db)

    # Для неавторизованных пользователей используем session_id
    session_id = None
    if not current_user:
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = f"anon_{uuid.uuid4().hex}"
        print(f"🍪 Session ID: {session_id}")

    try:
        print(f"🔍 Looking for photo ID: {generation_data.photo_id}")
        
        # Получаем фото
        photo = await photo_service.get_photo(
            generation_data.photo_id,
            current_user.id if current_user else None,
            session_id
        )
        
        print(f"📸 Photo found: {photo is not None}")
        
        if not photo:
            print(f"❌ Photo not found: id={generation_data.photo_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Фотография не найдена"
            )

        print(f"✅ Photo details: {photo.original_filename}, face_detected: {photo.face_detected}")

        if not photo.face_detected:
            print("❌ No face detected in photo")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="На фотографии не обнаружено лицо"
            )

        print(f"🔍 Looking for frame ID: {generation_data.frame_id}")
        frame = await frame_service.get_frame(generation_data.frame_id)
        if not frame:
            print("❌ Frame not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Рамка не найдена"
            )

        print("✅ Frame found")

        # Для неавторизованных пользователей ограничиваем количество генераций
        if not current_user:
            print("👤 Anonymous user - checking limits")
            can_generate, message = await generation_service.check_anonymous_limits(session_id)
            if not can_generate:
                print(f"🚫 Generation limit exceeded: {message}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=message
                )

        print("🎯 Creating generation task...")
        
        # Создаем задачу генерации
        generation = await generation_service.create_generation_task(
            user_id=current_user.id if current_user else None,
            session_id=session_id,
            photo_id=generation_data.photo_id,
            frame_id=generation_data.frame_id,
            questionnaire_answers=generation_data.questionnaire.dict(),
            generation_parameters={
                "theme": generation_data.theme,
                "style": generation_data.style,
                "enhance_face": generation_data.enhance_face
            }
        )

        print(f"✅ Generation task created: {generation.id}")

        # Запускаем генерацию через Stable Diffusion
        background_tasks.add_task(
            generation_service.process_generation_with_sd,
            generation.id
        )
        
        print("🎉 Generation started successfully")
        return GenerationResponse.from_orm(generation)

    except HTTPException as he:
        print(f"🚨 HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {str(e)}"
        )

@router.get("/{generation_id}", response_model=GeneratedImageResponse)
async def get_generation_result(
    generation_id: int,
    request: Request,  # ДОБАВЬТЕ этот параметр
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение результата генерации (для авторизованных и анонимных пользователей)
    """
    generation_service = GenerationService(db)
    
    # Для анонимных пользователей ищем генерацию по session_id
    session_id = None
    if not current_user:
        session_id = request.cookies.get("session_id")  # Теперь request доступен
    
    generation = await generation_service.get_generation(generation_id, current_user.id if current_user else None, session_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача генерации не найдена"
        )
    
    return GeneratedImageResponse.from_orm(generation)

@router.get("/{generation_id}/status", response_model=GenerationStatus)
async def get_generation_status(
    generation_id: int,
    request: Request,  # ДОБАВЬТЕ этот параметр
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение статуса генерации (для авторизованных и анонимных пользователей)
    """
    generation_service = GenerationService(db)
    
    # Для анонимных пользователей ищем генерацию по session_id
    session_id = None
    if not current_user:
        session_id = request.cookies.get("session_id")  # Теперь request доступен
    
    generation = await generation_service.get_generation(generation_id, current_user.id if current_user else None, session_id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача генерации не найдена"
        )
    
    return GenerationStatus.from_orm(generation)

@router.get("/user/history", response_model=list[GeneratedImageResponse])
async def get_generation_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
    db: AsyncSession = Depends(get_db)
):
    """
    Получение истории генераций пользователя
    """
    generation_service = GenerationService(db)
    generations = await generation_service.get_user_generations(current_user.id, skip, limit)
    
    return [GeneratedImageResponse.from_orm(gen) for gen in generations]

@router.delete("/{generation_id}")
async def cancel_generation(
    generation_id: int,
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
    db: AsyncSession = Depends(get_db)
):
    """
    Отмена задачи генерации (если она еще не завершена)
    """
    generation_service = GenerationService(db)
    success = await generation_service.cancel_generation(generation_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно отменить задачу генерации"
        )
    
    return {"message": "Генерация отменена"}

@router.post("/{generation_id}/retry")
async def retry_generation(
    generation_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),  # Теперь импорт определен
    db: AsyncSession = Depends(get_db)
):
    """
    Повторная попытка генерации для неудачной задачи
    """
    generation_service = GenerationService(db)

    generation = await generation_service.get_generation(generation_id, current_user.id)
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача генерации не найдена"
        )
    
    if generation.status not in ["failed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Можно повторить только неудачные или отмененные задачи"
        )
    
    new_generation = await generation_service.retry_generation(generation_id)
    
    background_tasks.add_task(
        generation_service.process_generation_with_sd,
        new_generation.id
    )
    
    return GenerationResponse.from_orm(new_generation)

@router.options("/", include_in_schema=False)
async def options_generate():
    """Обработка OPTIONS запросов для CORS"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Allow-Credentials": "true"
        }
    )

@router.options("/{generation_id}", include_in_schema=False)
async def options_generate_detail():
    """Обработка OPTIONS запросов для CORS"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Allow-Credentials": "true"
        }
    )