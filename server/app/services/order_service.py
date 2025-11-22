import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.order import Order
from app.models.generated_image import GeneratedImage
from app.schemas.order import OrderCreate, OrderUpdate
from app.config import settings

class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, user_id: int, order_data: OrderCreate) -> Order:
        """Создание нового заказа"""
        result = await self.db.execute(
            select(GeneratedImage).where(
                GeneratedImage.id == order_data.generated_image_id,
                GeneratedImage.user_id == user_id,
                GeneratedImage.status == "completed"
            )
        )
        generated_image = result.scalar_one_or_none()

        if not generated_image:
            raise ValueError("Сгенерированное изображение не найдено или не готово")

        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        base_price = self._calculate_base_price(order_data.painting_size)
        frame_price = generated_image.frame.price if generated_image.frame else 0
        shipping_price = self._calculate_shipping_price(order_data.shipping_method)

        discount_amount = await self._apply_promo_code(
            order_data.promo_code, base_price + frame_price
        )

        total_price = base_price + frame_price + shipping_price - discount_amount

        order = Order(
            order_number=order_number,
            user_id=user_id,
            generated_image_id=order_data.generated_image_id,
            painting_name=f"Картина по номерам - {generated_image.frame.name}",
            painting_size=order_data.painting_size,
            materials_included=order_data.materials_included,
            shipping_address=order_data.shipping_address.dict(),
            shipping_method=order_data.shipping_method,
            status="pending",
            payment_status="pending",
            base_price=base_price,
            frame_price=frame_price,
            shipping_price=shipping_price,
            discount_amount=discount_amount,
            total_price=total_price,
            promo_code=order_data.promo_code,
            created_at=datetime.utcnow()
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        return order

    def _calculate_base_price(self, painting_size: str) -> float:
        """Расчет базовой цены в зависимости от размера"""
        size_prices = {
            "30x40": 29.99,
            "40x50": 39.99,
            "50x70": 49.99,
            "60x80": 59.99
        }
        return size_prices.get(painting_size, 29.99)

    def _calculate_shipping_price(self, shipping_method: str) -> float:
        """Расчет стоимости доставки"""
        shipping_prices = {
            "standard": 4.99,
            "express": 9.99
        }
        return shipping_prices.get(shipping_method, 4.99)

    async def _apply_promo_code(self, promo_code: Optional[str], base_amount: float) -> float:
        """Применение промокода (заглушка)"""
        if not promo_code:
            return 0.0

        # В реальном приложении здесь будет проверка промокода в БД
        promo_codes = {
            "WELCOME10": 0.10, 
            "FIRSTORDER": 5.00,  
            "SUMMER25": 0.25   
        }

        discount_rate = promo_codes.get(promo_code.upper(), 0)
        if discount_rate < 1:  
            return base_amount * discount_rate
        else:  
            return min(discount_rate, base_amount * 0.5)  

    async def get_order(self, order_id: int, user_id: int) -> Optional[Order]:
        """Получение заказа по ID с проверкой владельца"""
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_orders(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Order], int]:
        """Получение списка заказов пользователя"""
        query = select(Order).where(Order.user_id == user_id)
        
        if status_filter:
            query = query.where(Order.status == status_filter)

        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar()
        
        orders_result = await self.db.execute(
            query.order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        orders = orders_result.scalars().all()
        
        return orders, total

    async def update_order(
        self, 
        order_id: int, 
        user_id: int, 
        update_data: OrderUpdate
    ) -> Optional[Order]:
        """Обновление информации о заказе"""
        order = await self.get_order(order_id, user_id)
        if not order:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            if hasattr(order, field):
                setattr(order, field, value)

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def cancel_order(self, order_id: int, user_id: int) -> bool:
        """Отмена заказа"""
        order = await self.get_order(order_id, user_id)
        if not order:
            return False

        if order.status not in ["pending", "confirmed"]:
            return False

        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def confirm_payment(self, order_id: int, payment_data: Dict[str, Any]) -> bool:
        """Подтверждение оплаты заказа"""
        order = await self.db.get(Order, order_id)
        if not order:
            return False

        order.payment_status = "paid"
        order.paid_at = datetime.utcnow()
        order.status = "confirmed"

        order.payment_data = payment_data

        await self.db.commit()
        return True

    async def update_order_status(self, order_id: int, new_status: str) -> bool:
        """Обновление статуса заказа (для администраторов)"""
        order = await self.db.get(Order, order_id)
        if not order:
            return False

        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        if new_status not in valid_statuses:
            return False

        order.status = new_status

        if new_status == "confirmed" and not order.confirmed_at:
            order.confirmed_at = datetime.utcnow()
        elif new_status == "shipped" and not order.shipped_at:
            order.shipped_at = datetime.utcnow()
        elif new_status == "delivered" and not order.delivered_at:
            order.delivered_at = datetime.utcnow()

        await self.db.commit()
        return True

    async def get_tracking_info(self, tracking_number: str) -> Dict[str, Any]:
        """Получение информации об отслеживании заказа (заглушка)"""
        # В реальном приложении здесь будет интеграция с сервисом отслеживания
        return {
            "tracking_number": tracking_number,
            "status": "in_transit",
            "estimated_delivery": (datetime.utcnow() + timedelta(days=3)).isoformat(),
            "events": [
                {
                    "date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "location": "Distribution Center",
                    "description": "Package in transit"
                },
                {
                    "date": datetime.utcnow().isoformat(),
                    "location": "Local Facility", 
                    "description": "Out for delivery"
                }
            ]
        }

    async def confirm_delivery(self, order_id: int, user_id: int) -> bool:
        """Подтверждение получения заказа"""
        order = await self.get_order(order_id, user_id)
        if not order:
            return False

        if order.status != "shipped":
            return False

        order.status = "delivered"
        order.delivered_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def get_order_stats(self, user_id: int) -> Dict[str, Any]:
        """Статистика по заказам пользователя"""
        total_result = await self.db.execute(
            select(func.count(Order.id)).where(Order.user_id == user_id)
        )
        total_orders = total_result.scalar()

        status_result = await self.db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.user_id == user_id)
            .group_by(Order.status)
        )
        status_counts = dict(status_result.all())

        total_amount_result = await self.db.execute(
            select(func.sum(Order.total_price)).where(
                Order.user_id == user_id,
                Order.payment_status == "paid"
            )
        )
        total_amount = total_amount_result.scalar() or 0

        return {
            "total_orders": total_orders,
            "status_breakdown": status_counts,
            "total_amount": round(total_amount, 2),
            "avg_order_value": round(total_amount / total_orders, 2) if total_orders > 0 else 0
        }