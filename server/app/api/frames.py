from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models.user import User
from app.schemas.frame import FrameResponse, FrameList
from app.services.frame_service import FrameService

router = APIRouter()

@router.options("/{frame_id}/select")
async def options_select_frame(frame_id: int):
    """Обработка OPTIONS запросов для CORS"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

@router.options("/")
async def options_frames():
    """Обработка OPTIONS запросов для CORS"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

@router.get("/", response_model=FrameList)
async def get_frames(
    skip: int = 0,
    limit: int = 100,
    frame_type: str = None,
    is_premium: bool = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка доступных рамок с фильтрацией"""
    frame_service = FrameService(db)
    
    # Если пользователь не аутентифицирован, показываем только бесплатные рамки
    if current_user is None:
        is_premium = False
    
    frames, total = await frame_service.get_frames(
        skip=skip,
        limit=limit,
        frame_type=frame_type,
        is_premium=is_premium
    )
    
    # Исправляем расчет страниц
    page_size = limit if limit > 0 else 1
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
    current_page = (skip // page_size) + 1 if page_size > 0 else 1
    
    # Создаем ответ
    frame_responses = []
    for frame in frames:
        frame_dict = {
            "id": frame.id,
            "name": frame.name,
            "description": frame.description,
            "frame_type": frame.frame_type,
            "preview_image_url": frame.preview_image_url,
            "model_3d_url": frame.model_3d_url,
            "price": frame.price,
            "is_premium": frame.is_premium,
            "is_active": frame.is_active,
            "complexity_level": frame.complexity_level,
            "estimated_time_hours": frame.estimated_time_hours,
            "tags": frame.tags or [],
            "camera_settings": frame.camera_settings or {},
            "sort_order": frame.sort_order,
            "created_at": frame.created_at.isoformat() if frame.created_at else None,
            "updated_at": frame.updated_at.isoformat() if frame.updated_at else None,
            "price_display": f"${frame.price:.2f}" if frame.price > 0 else "Бесплатно"
        }
        frame_responses.append(FrameResponse(**frame_dict))
    
    response_data = FrameList(
        frames=frame_responses,
        total=total,
        page=current_page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    return response_data

@router.post("/{frame_id}/select")
async def select_frame(
    frame_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Выбор рамки пользователем для использования в генерации"""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация для выбора рамки"
        )
    
    frame_service = FrameService(db)
    
    frame = await frame_service.get_frame(frame_id)
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
                detail="Для доступа к премиум рамкам требуется подписка"
            )
    
    await frame_service.save_frame_selection(current_user.id, frame_id)
    
    return {
        "message": f"Рамка '{frame.name}' успешно выбрана",
        "frame_id": frame_id,
        "frame_name": frame.name
    }
