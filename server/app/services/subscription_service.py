from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionPlan, SubscriptionUsage

class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_plans(self) -> List[SubscriptionPlan]:
        """Получение списка доступных планов подписки"""
        return [
            SubscriptionPlan(
                plan_type="basic",
                plan_name="Базовый",
                billing_cycle="monthly",
                price_per_cycle=9.99,
                generation_limit=10,
                max_photo_size=10485760,  
                premium_frames_access=False,
                priority_processing=False,
                features=[
                    "10 генераций в месяц",
                    "Базовые рамки",
                    "Стандартная обработка",
                    "Поддержка по email"
                ]
            ),
            SubscriptionPlan(
                plan_type="premium", 
                plan_name="Премиум",
                billing_cycle="monthly",
                price_per_cycle=19.99,
                generation_limit=50,
                max_photo_size=20971520,  
                premium_frames_access=True,
                priority_processing=True,
                features=[
                    "50 генераций в месяц",
                    "Все рамки включая премиум",
                    "Приоритетная обработка",
                    "Улучшенное качество",
                    "Приоритетная поддержка"
                ]
            ),
            SubscriptionPlan(
                plan_type="enterprise",
                plan_name="Безлимитный",
                billing_cycle="monthly", 
                price_per_cycle=29.99,
                generation_limit=None,  
                max_photo_size=52428800,  
                premium_frames_access=True,
                priority_processing=True,
                features=[
                    "Неограниченные генерации",
                    "Все рамки включая премиум",
                    "Максимальный приоритет",
                    "Экспорт в высоком качестве",
                    "Персональная поддержка 24/7"
                ]
            )
        ]

    async def create_subscription(
        self, 
        user_id: int, 
        subscription_data: SubscriptionCreate
    ) -> Subscription:
        """Создание новой подписки"""
        plans = await self.get_available_plans()
        plan = next((p for p in plans if p.plan_type == subscription_data.plan_type), None)
        
        if not plan:
            raise ValueError("Выбранный план подписки не существует")

        start_date = datetime.utcnow()
        if subscription_data.billing_cycle == "monthly":
            end_date = start_date + timedelta(days=30)
        else:  
            end_date = start_date + timedelta(days=365)

        subscription = Subscription(
            user_id=user_id,
            plan_type=subscription_data.plan_type,
            plan_name=plan.plan_name,
            billing_cycle=subscription_data.billing_cycle,
            price_per_cycle=plan.price_per_cycle,
            generation_limit=plan.generation_limit,
            max_photo_size=plan.max_photo_size,
            premium_frames_access=plan.premium_frames_access,
            priority_processing=plan.priority_processing,
            status="active",
            auto_renew=subscription_data.auto_renew,
            start_date=start_date,
            end_date=end_date,
            payment_method=subscription_data.payment_method,
            last_payment_date=start_date,
            next_payment_date=end_date
        )

        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Получение активной подписки пользователя"""
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.end_date > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()

    async def get_subscription_usage(self, user_id: int) -> Optional[SubscriptionUsage]:
        """Получение информации об использовании подписки"""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return None

        from app.services.generation_service import GenerationService
        generation_service = GenerationService(self.db)
        generations_used = await generation_service._get_monthly_generation_count(user_id)

        usage_percentage = 0
        if subscription.generation_limit:
            usage_percentage = (generations_used / subscription.generation_limit) * 100

        reset_date = subscription.end_date.replace(day=1) + timedelta(days=32)
        reset_date = reset_date.replace(day=1)
        days_until_reset = (reset_date - datetime.utcnow()).days

        return SubscriptionUsage(
            plan_type=subscription.plan_type,
            generations_used=generations_used,
            generations_limit=subscription.generation_limit,
            usage_percentage=round(usage_percentage, 2),
            reset_date=reset_date,
            days_until_reset=days_until_reset
        )

    async def update_subscription(
        self, 
        user_id: int, 
        update_data: SubscriptionUpdate
    ) -> Optional[Subscription]:
        """Обновление настроек подписки"""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            if hasattr(subscription, field):
                setattr(subscription, field, value)

        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def cancel_subscription(self, user_id: int) -> bool:
        """Отмена подписки"""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return False

        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        subscription.auto_renew = False

        await self.db.commit()
        return True

    async def renew_subscription(self, user_id: int) -> Optional[Subscription]:
        """Продление подписки"""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return None

        if subscription.end_date > datetime.utcnow():
            if subscription.billing_cycle == "monthly":
                new_end_date = subscription.end_date + timedelta(days=30)
            else:
                new_end_date = subscription.end_date + timedelta(days=365)

            subscription.end_date = new_end_date
            subscription.next_payment_date = new_end_date
            subscription.renewed_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(subscription)

        return subscription

    async def get_subscription_history(self, user_id: int) -> List[Subscription]:
        """Получение истории подписок пользователя"""
        result = await self.db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        return result.scalars().all()

    async def upgrade_subscription(self, user_id: int, new_plan_type: str) -> Optional[Subscription]:
        """Обновление плана подписки"""
        subscription = await self.get_active_subscription(user_id)
        if not subscription:
            return None

        plans = await self.get_available_plans()
        new_plan = next((p for p in plans if p.plan_type == new_plan_type), None)
        
        if not new_plan:
            raise ValueError("Новый план подписки не существует")

        subscription.plan_type = new_plan.plan_type
        subscription.plan_name = new_plan.plan_name
        subscription.price_per_cycle = new_plan.price_per_cycle
        subscription.generation_limit = new_plan.generation_limit
        subscription.max_photo_size = new_plan.max_photo_size
        subscription.premium_frames_access = new_plan.premium_frames_access
        subscription.priority_processing = new_plan.priority_processing

        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def process_auto_renewals(self) -> List[Subscription]:
        """Обработка автоматического продления подписок (для cron job)"""
        renew_date = datetime.utcnow() + timedelta(days=1) 
        
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.auto_renew == True,
                Subscription.status == "active", 
                Subscription.end_date <= renew_date,
                Subscription.end_date > datetime.utcnow()
            )
        )
        subscriptions_to_renew = result.scalars().all()

        renewed_subscriptions = []
        for subscription in subscriptions_to_renew:
            try:
                renewed_subscription = await self.renew_subscription(subscription.user_id)
                if renewed_subscription:
                    renewed_subscriptions.append(renewed_subscription)
            except Exception as e:
                print(f"Error renewing subscription for user {subscription.user_id}: {str(e)}")

        return renewed_subscriptions