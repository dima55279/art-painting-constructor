import asyncio
import uuid
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.generated_image import GeneratedImage
from app.models.user import User
from app.models.subscription import Subscription
from app.config import settings

class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_generation_task(
        self,
        user_id: int,
        photo_id: int,
        frame_id: int,
        questionnaire_answers: Dict[str, Any],
        generation_parameters: Dict[str, Any]
    ) -> GeneratedImage:
        """Создание задачи генерации изображения"""
        generation = GeneratedImage(
            user_id=user_id,
            original_photo_id=photo_id,
            frame_id=frame_id,
            status="pending",
            progress=0,
            questionnaire_answers=questionnaire_answers,
            generation_parameters=generation_parameters,
            created_at=datetime.utcnow()
        )

        self.db.add(generation)
        await self.db.commit()
        await self.db.refresh(generation)

        return generation

    async def get_generation(self, generation_id: int, user_id: int) -> Optional[GeneratedImage]:
        """Получение задачи генерации с проверкой владельца"""
        result = await self.db.execute(
            select(GeneratedImage).where(
                GeneratedImage.id == generation_id,
                GeneratedImage.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_generations(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[GeneratedImage]:
        """Получение истории генераций пользователя"""
        result = await self.db.execute(
            select(GeneratedImage)
            .where(GeneratedImage.user_id == user_id)
            .order_by(GeneratedImage.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def process_generation(self, generation_id: int) -> None:
        """Обработка задачи генерации (запускается в фоне)"""
        generation = await self.db.get(GeneratedImage, generation_id)
        if not generation:
            return

        try:
            generation.status = "processing"
            generation.started_at = datetime.utcnow()
            await self.db.commit()

            for progress in range(0, 101, 10):
                await asyncio.sleep(2)  
                
                generation.progress = progress
                await self.db.commit()

            generation.status = "completed"
            generation.completed_at = datetime.utcnow()
            generation.progress = 100

            generation.generated_image_url = f"/static/generated_images/{uuid.uuid4()}.jpg"
            generation.preview_image_url = f"/static/generated_images/preview_{uuid.uuid4()}.jpg"

            generation.colors_used = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"]
            generation.complexity_score = 7
            generation.generation_time_seconds = 20.0

            await self.db.commit()

        except Exception as e:
            generation.status = "failed"
            generation.error_message = str(e)
            await self.db.commit()

    async def check_generation_limits(self, user_id: int) -> Tuple[bool, str]:
        """Проверка лимитов генерации для пользователя"""
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            monthly_count = await self._get_monthly_generation_count(user_id)
            if monthly_count >= 3:
                return False, "Лимит генераций исчерпан. Оформите подписку для неограниченного доступа."
        else:
            if subscription.generation_limit:
                monthly_count = await self._get_monthly_generation_count(user_id)
                if monthly_count >= subscription.generation_limit:
                    return False, f"Лимит генераций вашего плана исчерпан ({subscription.generation_limit} в месяц)"

        return True, ""

    async def _get_monthly_generation_count(self, user_id: int) -> int:
        """Получение количества генераций за текущий месяц"""
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.count(GeneratedImage.id)).where(
                GeneratedImage.user_id == user_id,
                GeneratedImage.created_at >= current_month,
                GeneratedImage.status == "completed"
            )
        )
        return result.scalar() or 0

    async def cancel_generation(self, generation_id: int, user_id: int) -> bool:
        """Отмена задачи генерации"""
        generation = await self.get_generation(generation_id, user_id)
        if not generation:
            return False

        if generation.status not in ["pending", "processing"]:
            return False

        generation.status = "cancelled"
        await self.db.commit()
        return True

    async def retry_generation(self, generation_id: int) -> GeneratedImage:
        """Повторная попытка генерации"""
        generation = await self.db.get(GeneratedImage, generation_id)
        if not generation:
            raise ValueError("Задача генерации не найдена")

        new_generation = GeneratedImage(
            user_id=generation.user_id,
            original_photo_id=generation.original_photo_id,
            frame_id=generation.frame_id,
            status="pending",
            progress=0,
            questionnaire_answers=generation.questionnaire_answers,
            generation_parameters=generation.generation_parameters,
            created_at=datetime.utcnow()
        )

        self.db.add(new_generation)
        await self.db.commit()
        await self.db.refresh(new_generation)

        return new_generation

    async def get_generation_stats(self, user_id: int) -> Dict[str, Any]:
        """Статистика по генерациям пользователя"""
        total_result = await self.db.execute(
            select(func.count(GeneratedImage.id)).where(
                GeneratedImage.user_id == user_id
            )
        )
        total_generations = total_result.scalar()

        completed_result = await self.db.execute(
            select(func.count(GeneratedImage.id)).where(
                GeneratedImage.user_id == user_id,
                GeneratedImage.status == "completed"
            )
        )
        completed_generations = completed_result.scalar()

        time_result = await self.db.execute(
            select(func.avg(GeneratedImage.generation_time_seconds)).where(
                GeneratedImage.user_id == user_id,
                GeneratedImage.status == "completed",
                GeneratedImage.generation_time_seconds.isnot(None)
            )
        )
        avg_generation_time = time_result.scalar() or 0

        return {
            "total_generations": total_generations,
            "completed_generations": completed_generations,
            "success_rate": completed_generations / total_generations if total_generations > 0 else 0,
            "avg_generation_time": round(avg_generation_time, 2),
            "monthly_usage": await self._get_monthly_generation_count(user_id)
        }
        # Добавляем в существующий класс GenerationService

    async def process_generation(self, generation_id: int) -> None:
        """Обработка задачи генерации с использованием данных анкеты"""
        generation = await self.db.get(GeneratedImage, generation_id)
        if not generation:
            return

        try:
            generation.status = "processing"
            generation.started_at = datetime.utcnow()
            await self.db.commit()

            # Получаем данные анкеты для нейросети
            questionnaire_service = QuestionnaireService(self.db)
            ai_prompt_data = await questionnaire_service.prepare_for_ai_generation(
                generation.questionnaire_answers.get("questionnaire_id")
            )

            # Имитация вызова нейросети с данными анкеты
            for progress in range(0, 101, 10):
                await asyncio.sleep(2)  
                
                # Логируем данные анкеты (в реальности передаем в нейросеть)
                if progress == 50:
                    print(f"Передача данных в нейросеть: {ai_prompt_data}")
                
                generation.progress = progress
                await self.db.commit()

            # Сохраняем результат
            generation.status = "completed"
            generation.completed_at = datetime.utcnow()
            generation.progress = 100

            # Генерируем URL изображений (в реальности получаем от нейросети)
            generation.generated_image_url = f"/static/generated_images/{uuid.uuid4()}.jpg"
            generation.preview_image_url = f"/static/generated_images/preview_{uuid.uuid4()}.jpg"

            # Сохраняем метаданные из анкеты
            generation.colors_used = ai_prompt_data["style_parameters"]["color_palette"]
            generation.complexity_score = ai_prompt_data["style_parameters"]["complexity_level"]
            generation.generation_time_seconds = 20.0

            await self.db.commit()

        except Exception as e:
            generation.status = "failed"
            generation.error_message = str(e)
            await self.db.commit()