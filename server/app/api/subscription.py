from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionResponse, 
    SubscriptionCreate, 
    SubscriptionUpdate,
    SubscriptionUsage,
    SubscriptionPlan
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()

@router.get("/plans", response_model=list[SubscriptionPlan])
async def get_subscription_plans(
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка доступных планов подписки
    """
    subscription_service = SubscriptionService(db)
    plans = await subscription_service.get_available_plans()
    return plans

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание новой подписки
    """
    subscription_service = SubscriptionService(db)
    
    active_subscription = await subscription_service.get_active_subscription(current_user.id)
    if active_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У вас уже есть активная подписка"
        )
    
    subscription = await subscription_service.create_subscription(
        current_user.id, subscription_data
    )
    
    return SubscriptionResponse.from_orm(subscription)

@router.get("/", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о текущей подписке пользователя
    """
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.get_active_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активная подписка не найдена"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.get("/usage", response_model=SubscriptionUsage)
async def get_subscription_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации об использовании подписки
    """
    subscription_service = SubscriptionService(db)
    usage = await subscription_service.get_subscription_usage(current_user.id)
    
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Информация об использовании недоступна"
        )
    
    return usage

@router.put("/", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_update: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление настроек подписки
    """
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.update_subscription(
        current_user.id, subscription_update
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Активная подписка не найдена"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Отмена подписки (в конце текущего периода)
    """
    subscription_service = SubscriptionService(db)
    success = await subscription_service.cancel_subscription(current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно отменить подписку"
        )
    
    return {"message": "Подписка будет отменена в конце текущего периода"}

@router.post("/renew")
async def renew_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Продление подписки
    """
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.renew_subscription(current_user.id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно продлить подписку"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.get("/history", response_model=list[SubscriptionResponse])
async def get_subscription_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение истории подписок пользователя
    """
    subscription_service = SubscriptionService(db)
    subscriptions = await subscription_service.get_subscription_history(current_user.id)
    return [SubscriptionResponse.from_orm(sub) for sub in subscriptions]

@router.post("/upgrade")
async def upgrade_subscription(
    new_plan_type: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление плана подписки
    """
    subscription_service = SubscriptionService(db)
    subscription = await subscription_service.upgrade_subscription(
        current_user.id, new_plan_type
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно обновить подписку"
        )
    
    return SubscriptionResponse.from_orm(subscription)