from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserProfile
from app.services.user_service import UserService

router = APIRouter()

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение полного профиля пользователя
    """
    user_service = UserService(db)
    profile_data = await user_service.get_user_profile(current_user.id)
    
    # Создаем UserProfile напрямую
    user_profile = UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        phone=current_user.phone,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
        photos_count=profile_data["photos_count"],
        orders_count=profile_data["orders_count"],
        generated_images_count=profile_data["generated_images_count"],
        active_subscription=profile_data["active_subscription"],
        recent_photos=profile_data["recent_photos"],
        recent_orders=profile_data["recent_orders"],
    )
    return user_profile

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление профиля пользователя
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user.id, user_data)
    
    # Создаем UserResponse напрямую
    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        phone=updated_user.phone,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        avatar_url=updated_user.avatar_url,
        is_active=updated_user.is_active,
        is_superuser=updated_user.is_superuser,
        email_verified=updated_user.email_verified,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        last_login=updated_user.last_login,
    )


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузка аватара пользователя
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением"
        )
    
    user_service = UserService(db)
    avatar_url = await user_service.upload_avatar(current_user.id, file)
    
    return {"avatar_url": avatar_url, "message": "Аватар успешно загружен"}

@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление аватара пользователя
    """
    user_service = UserService(db)
    await user_service.delete_avatar(current_user.id)
    
    return {"message": "Аватар успешно удален"}

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение статистики пользователя
    """
    user_service = UserService(db)
    stats = await user_service.get_user_stats(current_user.id)
    return stats

@router.post("/verify-email")
async def request_email_verification(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Запрос на верификацию email
    """
    user_service = UserService(db)
    await user_service.send_verification_email(current_user.id)
    
    return {"message": "Письмо для верификации отправлено на ваш email"}

@router.get("/verify-email/{token}")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Подтверждение email по токену
    """
    user_service = UserService(db)
    await user_service.verify_email_token(token)
    
    return {"message": "Email успешно подтвержден"}