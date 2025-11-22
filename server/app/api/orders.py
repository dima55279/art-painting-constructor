from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse, OrderList, OrderUpdate
from app.services.order_service import OrderService
from app.services.generation_service import GenerationService

router = APIRouter()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового заказа
    """
    order_service = OrderService(db)
    generation_service = GenerationService(db)

    generation = await generation_service.get_generation(
        order_data.generated_image_id, 
        current_user.id
    )
    
    if not generation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сгенерированное изображение не найдено"
        )
    
    if generation.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Генерация изображения еще не завершена"
        )

    order = await order_service.create_order(current_user.id, order_data)
    return OrderResponse.from_orm(order)

@router.get("/", response_model=OrderList)
async def get_user_orders(
    skip: int = 0,
    limit: int = 20,
    status_filter: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка заказов пользователя
    """
    order_service = OrderService(db)
    orders, total = await order_service.get_user_orders(
        current_user.id, skip, limit, status_filter
    )
    
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    
    return OrderList(
        orders=[OrderResponse.from_orm(order) for order in orders],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        total_pages=total_pages
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации о конкретном заказе
    """
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, current_user.id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    return OrderResponse.from_orm(order)

@router.put("/{order_id}")
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление информации о заказе
    """
    order_service = OrderService(db)
    order = await order_service.update_order(order_id, current_user.id, order_update)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    return OrderResponse.from_orm(order)

@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Отмена заказа
    """
    order_service = OrderService(db)
    success = await order_service.cancel_order(order_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно отменить заказ"
        )
    
    return {"message": "Заказ успешно отменен"}

@router.get("/{order_id}/tracking")
async def get_order_tracking(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение информации об отслеживании заказа
    """
    order_service = OrderService(db)
    order = await order_service.get_order(order_id, current_user.id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    if not order.tracking_number:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Информация об отслеживании недоступна"
        )
    
    tracking_info = await order_service.get_tracking_info(order.tracking_number)
    return tracking_info

@router.post("/{order_id}/confirm-delivery")
async def confirm_delivery(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Подтверждение получения заказа
    """
    order_service = OrderService(db)
    success = await order_service.confirm_delivery(order_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно подтвердить получение заказа"
        )
    
    return {"message": "Получение заказа подтверждено"}