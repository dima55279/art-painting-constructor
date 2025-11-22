import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.generated_image import (
    GenerationRequest, 
    GenerationResponse, 
    GenerationStatus,
    GeneratedImageResponse
)
from app.services.generation_service import GenerationService
from app.services.photo_service import PhotoService
from app.services.frame_service import FrameService

router = APIRouter()

@router.post("/", response_model=GenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_image(
    generation_data: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Запуск процесса генерации изображения
    """
    generation_service = GenerationService(db)
    photo_service = PhotoService(db)
    frame_service = FrameService(db)

    photo = await photo_service.get_photo(generation_data.photo_id, current_user.id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фотография не найдена"
        )

    if not photo.face_detected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="На фотографии не обнаружено лицо. Пожалуйста, загрузите фото с четко видимым лицом"
        )

    frame = await frame_service.get_frame(generation_data.frame_id)
    if not frame:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рамка не найдена"
        )

    if frame.is_premium:
        has_premium_access = await frame_service.check_premium_access(current_user.id)
        if not has_premium_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Для использования премиум рамок требуется подписка"
            )

    can_generate, message = await generation_service.check_generation_limits(current_user.id)
    if not can_generate:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message
        )

    generation = await generation_service.create_generation_task(
        user_id=current_user.id,
        photo_id=generation_data.photo_id,
        frame_id=generation_data.frame_id,
        questionnaire_answers=generation_data.questionnaire.dict(),
        generation_parameters={
            "theme": generation_data.theme,
            "style": generation_data.style,
            "enhance_face": generation_data.enhance_face
        }
    )

    background_tasks.add_task(
        generation_service.process_generation,
        generation.id
    )
    
    return GenerationResponse.from_orm(generation)

@router.get("/{generation_id}", response_model=GeneratedImageResponse)
async def get_generation_result(
    generation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение результата генерации
    """
    generation_service = GenerationService(db)
    generation = await generation_service.get_generation(generation_id, current_user.id)
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача генерации не найдена"
        )
    
    return GeneratedImageResponse.from_orm(generation)

@router.get("/{generation_id}/status", response_model=GenerationStatus)
async def get_generation_status(
    generation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение статуса генерации
    """
    generation_service = GenerationService(db)
    generation = await generation_service.get_generation(generation_id, current_user.id)
    
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
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
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
        generation_service.process_generation,
        new_generation.id
    )
    
    return GenerationResponse.from_orm(new_generation)