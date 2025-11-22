from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.frame import Frame
from app.models.subscription import Subscription
from app.models.user import User

class FrameService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_frames(
        self, 
        skip: int = 0, 
        limit: int = 100,
        frame_type: Optional[str] = None,
        is_premium: Optional[bool] = None
    ) -> Tuple[List[Frame], int]:
        """Получение списка рамок с фильтрацией"""
        try:
            # Базовый запрос
            query = select(Frame).where(Frame.is_active == True)
            
            # Применяем фильтры
            if frame_type:
                query = query.where(Frame.frame_type == frame_type)
            
            if is_premium is not None:
                query = query.where(Frame.is_premium == is_premium)
            
            # Получаем общее количество
            count_query = select(func.count(Frame.id)).where(Frame.is_active == True)
            if frame_type:
                count_query = count_query.where(Frame.frame_type == frame_type)
            if is_premium is not None:
                count_query = count_query.where(Frame.is_premium == is_premium)
                
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Получаем рамки
            frames_result = await self.db.execute(
                query.order_by(Frame.sort_order.asc(), Frame.name.asc())
                .offset(skip)
                .limit(limit)
            )
            frames = frames_result.scalars().all()
            
            return frames, total
            
        except Exception as e:
            print(f"Error getting frames: {str(e)}")
            return [], 0

    async def get_frame(self, frame_id: int) -> Optional[Frame]:
        """Получение рамки по ID"""
        try:
            result = await self.db.execute(
                select(Frame).where(Frame.id == frame_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            print(f"Error getting frame {frame_id}: {str(e)}")
            return None

    async def check_premium_access(self, user_id: int) -> bool:
        """Проверка доступа пользователя к премиум рамкам"""
        try:
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id,
                    Subscription.status == "active",
                    Subscription.end_date > func.now()
                )
            )
            subscription = result.scalar_one_or_none()
            
            return subscription is not None
        except Exception as e:
            print(f"Error checking premium access: {str(e)}")
            return False

    async def save_frame_selection(self, user_id: int, frame_id: int) -> None:
        """Сохранение выбора рамки пользователем"""
        # В этой реализации мы просто проверяем существование рамки
        # В более сложной системе можно сохранять выбор в отдельную таблицу
        frame = await self.get_frame(frame_id)
        if not frame:
            raise ValueError("Рамка не найдена")

    async def get_user_selected_frame(self, user_id: int) -> Optional[Frame]:
        """Получение текущей выбранной рамки пользователя"""
        # В этой реализации возвращаем первую доступную рамку
        # В реальном приложении здесь будет логика получения сохраненного выбора
        result = await self.db.execute(
            select(Frame)
            .where(Frame.is_active == True)
            .order_by(Frame.sort_order.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_frame_categories(self) -> List[Dict[str, Any]]:
        """Получение списка категорий рамок"""
        result = await self.db.execute(
            select(Frame.frame_type, func.count(Frame.id))
            .where(Frame.is_active == True)
            .group_by(Frame.frame_type)
        )
        
        categories = []
        for frame_type, count in result.all():
            categories.append({
                "type": frame_type,
                "name": self._get_frame_type_display_name(frame_type),
                "count": count
            })
        
        return categories

    def _get_frame_type_display_name(self, frame_type: str) -> str:
        """Получение отображаемого имени для типа рамки"""
        type_names = {
            "cowboy": "Вестерн",
            "pumpkin": "Хэллоуин", 
            "christmas": "Новогодняя",
            "flowers": "Цветы",
            "sea": "Море",
            "popart": "Поп-арт",
            "wood": "Дерево",
            "metal": "Металл",
            "gold": "Золото"
        }
        return type_names.get(frame_type, frame_type)

    async def get_recommended_frames(
        self, 
        user_id: int, 
        limit: int = 5
    ) -> List[Frame]:
        """Получение рекомендованных рамок для пользователя"""
        has_premium = await self.check_premium_access(user_id)
        
        query = select(Frame).where(Frame.is_active == True)
        
        if not has_premium:
            query = query.where(Frame.is_premium == False)
        
        result = await self.db.execute(
            query.order_by(Frame.sort_order.asc())
            .limit(limit)
        )
        
        return result.scalars().all()

    async def create_frame(self, frame_data: Dict[str, Any]) -> Frame:
        """Создание новой рамки"""
        frame = Frame(**frame_data)
        self.db.add(frame)
        await self.db.commit()
        await self.db.refresh(frame)
        return frame

    async def update_frame(self, frame_id: int, update_data: Dict[str, Any]) -> Optional[Frame]:
        """Обновление информации о рамке"""
        frame = await self.get_frame(frame_id)
        if not frame:
            return None
        
        for field, value in update_data.items():
            if hasattr(frame, field) and field != 'id':
                setattr(frame, field, value)
        
        await self.db.commit()
        await self.db.refresh(frame)
        return frame

    async def delete_frame(self, frame_id: int) -> bool:
        """Удаление рамки (деактивация)"""
        frame = await self.get_frame(frame_id)
        if not frame:
            return False
        
        frame.is_active = False
        await self.db.commit()
        return True