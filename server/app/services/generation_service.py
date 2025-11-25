import aiofiles
import os
import asyncio
import uuid
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.generated_image import GeneratedImage
from app.models.photo import Photo  # Добавьте этот импорт
from app.models.user import User
from app.models.frame import Frame
from app.models.subscription import Subscription
from app.config import settings
from app.services.stable_diffusion_service import stable_diffusion_service
from app.services.translation_service import translation_service

class GenerationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_generation_task(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        photo_id: int,
        frame_id: int,
        questionnaire_answers: Dict[str, Any], 
        generation_parameters: Dict[str, Any]
    ) -> GeneratedImage:
        """Создание задачи генерации изображения"""
        
        if not user_id and session_id:
            generation_parameters['session_id'] = session_id
        
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

    async def get_generation(self, generation_id: int, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Optional[GeneratedImage]:
        """Получение задачи генерации с явной загрузкой отношений"""
        
        query = select(GeneratedImage).where(GeneratedImage.id == generation_id)
        
        if user_id:
            query = query.where(GeneratedImage.user_id == user_id)
        else:
            query = query.where(
                GeneratedImage.user_id.is_(None),
                GeneratedImage.generation_parameters['session_id'].as_string() == session_id
            )
        
        # Явно загружаем отношения
        query = query.options(
            selectinload(GeneratedImage.frame),
            selectinload(GeneratedImage.original_photo)
        )
        
        result = await self.db.execute(query)
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

            generation.generated_image_url = f"/static/generated_images/{filename}"
            generation.preview_image_url = f"/static/generated_images/{filename}"
            print(f"✅ Saved image URLs - generated: {generation.generated_image_url}, preview: {generation.preview_image_url}")

            await self.db.commit()

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
        
    async def process_generation_with_sd(self, generation_id: int) -> None:
        generation = await self.db.get(GeneratedImage, generation_id)
        if not generation:
            return

        try:
            generation.status = "processing"
            generation.started_at = datetime.utcnow()
            await self.db.commit()

            questionnaire_answers = generation.questionnaire_answers
            additional_notes = questionnaire_answers.get('additional_notes', '')
            
            if additional_notes:
                prompt = additional_notes
                print(f"🎨 Using translated prompt from additional_notes: {prompt}")
            else:
                frame = await self.db.get(Frame, generation.frame_id)
                prompt = await self._generate_ai_prompt(questionnaire_answers, frame)
                print(f"🎨 Generated prompt: {prompt}")

            image_bytes = await stable_diffusion_service.generate_image(
                prompt=prompt,
                negative_prompt="ugly, blurry, low quality, deformed, bad anatomy, poorly drawn",
                width=512,
                height=512,
                steps=25,
                cfg_scale=7.5
            )

            if not image_bytes:
                raise Exception("Не удалось сгенерировать изображение")

            filename = f"generated_{generation_id}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(settings.GENERATED_IMAGES_DIR, filename)
            
            os.makedirs(settings.GENERATED_IMAGES_DIR, exist_ok=True)
            
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(image_bytes)

            generation.status = "completed"
            generation.completed_at = datetime.utcnow()
            generation.progress = 100
            generation.generated_image_url = f"/static/generated_images/{filename}"
            generation.preview_image_url = f"/static/generated_images/{filename}"

            generation.colors_used = ["#FF5733", "#33FF57", "#3357FF"]
            generation.complexity_score = 7
            generation.generation_time_seconds = (
                generation.completed_at - generation.started_at
            ).total_seconds()

            await self.db.commit()

        except Exception as e:
            generation.status = "failed"
            generation.error_message = f"Ошибка генерации: {str(e)}"
            await self.db.commit()
            print(f"Generation {generation_id} failed: {str(e)}")

    async def _get_ai_prompt_from_questionnaire(self, questionnaire_data: Dict[str, Any]) -> str:
        """Получение AI промпта из данных анкеты"""
        if 'translated_prompt' in questionnaire_data:
            return questionnaire_data['translated_prompt']
        
        if 'ai_prompt' in questionnaire_data:
            return questionnaire_data['ai_prompt']
        
        return None

    async def _generate_ai_prompt(self, questionnaire_data: Dict[str, Any], frame: Frame) -> str:
        """Генерация промпта для нейросети на основе анкеты и рамки"""
        
        # Базовые компоненты промпта
        setting = questionnaire_data.get('setting', 'a beautiful scene')
        clothing = questionnaire_data.get('clothing', 'elegant clothes')
        pose = questionnaire_data.get('pose', 'natural pose')
        
        # Стилевые параметры из анкеты
        style_params = questionnaire_data.get('style_parameters', {})
        artistic_style = style_params.get('artistic_style', 'realistic')
        mood = style_params.get('mood', 'neutral')
        
        # Адаптируем стиль рамки для промпта
        frame_style = self._get_frame_style_prompt(frame)
        
        # Собираем промпт
        prompt_parts = [
            f"portrait of a person in {setting}",
            f"wearing {clothing}",
            f"in a {pose}",
            f"{artistic_style} style",
            f"{mood} mood",
            frame_style,
            "high quality, detailed, masterpiece",
            "sharp focus, professional photography"
        ]
        
        # Убираем пустые части и соединяем
        prompt = ", ".join([part for part in prompt_parts if part])
        
        return prompt

    def _get_frame_style_prompt(self, frame: Frame) -> str:
        """Преобразование типа рамки в стилевой промпт"""
        frame_style_map = {
            'cowboy': 'western style, cowboy aesthetic, desert landscape',
            'pumpkin': 'halloween theme, pumpkin, spooky atmosphere',
            'christmas': 'christmas theme, holiday, festive, snow',
            'flowers': 'floral, garden, blossoms, nature',
            'sea': 'ocean, beach, marine, nautical',
            'popart': 'pop art, vibrant colors, comic book style',
            'wood': 'wooden frame, natural, rustic',
            'metal': 'metallic, industrial, modern',
            'gold': 'golden, luxurious, elegant, ornate'
        }
        
        return frame_style_map.get(frame.frame_type, 'artistic')
    
    async def check_anonymous_limits(self, session_id: str) -> Tuple[bool, str]:
        """Проверка лимитов генерации для неавторизованных пользователей"""
        # Простая реализация - разрешаем 3 генерации на session_id
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.count(GeneratedImage.id)).where(
                GeneratedImage.user_id == None,
                GeneratedImage.generation_parameters['session_id'].as_string() == session_id,
                GeneratedImage.created_at >= current_hour
            )
        )
        count = result.scalar() or 0
        
        if count >= 3:
            return False, "Лимит генераций исчерпан. Зарегистрируйтесь для большего количества генераций."
        
        return True, ""

    async def create_generation_task(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        photo_id: int,
        frame_id: int,
        questionnaire_answers: Dict[str, Any],
        generation_parameters: Dict[str, Any]
    ) -> GeneratedImage:
        """Создание задачи генерации изображения с поддержкой неавторизованных пользователей"""
        
        # Добавляем session_id в параметры генерации для неавторизованных
        if not user_id and session_id:
            generation_parameters['session_id'] = session_id
        
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

    async def process_generation_with_sd(self, generation_id: int) -> None:
        """Обработка генерации с использованием Stable Diffusion"""
        generation = await self.db.get(GeneratedImage, generation_id)
        if not generation:
            return

        try:
            generation.status = "processing"
            generation.started_at = datetime.utcnow()
            await self.db.commit()

            # Получаем связанные данные
            photo = await self.db.get(Photo, generation.original_photo_id)
            frame = await self.db.get(Frame, generation.frame_id)
            
            if not photo or not frame:
                raise ValueError("Не найдено фото или рамка")

            # Генерируем промпт
            ai_prompt = await self._generate_ai_prompt(
                generation.questionnaire_answers, 
                frame,
                generation.generation_parameters.get('theme', 'light')
            )

            # Генерируем изображение через Stable Diffusion
            image_bytes = await stable_diffusion_service.generate_image(
                prompt=ai_prompt,
                negative_prompt="ugly, blurry, low quality, deformed, bad anatomy, poorly drawn",
                width=512,
                height=512,
                steps=25,
                cfg_scale=7.5
            )

            if not image_bytes:
                raise Exception("Не удалось сгенерировать изображение")

            # Сохраняем сгенерированное изображение
            filename = f"generated_{generation_id}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(settings.GENERATED_IMAGES_DIR, filename)
            
            os.makedirs(settings.GENERATED_IMAGES_DIR, exist_ok=True)
            
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(image_bytes)

            # Обновляем запись генерации
            generation.status = "completed"
            generation.completed_at = datetime.utcnow()
            generation.progress = 100
            generation.generated_image_url = f"/static/generated_images/{filename}"
            generation.preview_image_url = f"/static/generated_images/{filename}"

            # Сохраняем метаданные
            generation.colors_used = ["#FF5733", "#33FF57", "#3357FF"]  # Пример палитры
            generation.complexity_score = 7
            generation.generation_time_seconds = (
                generation.completed_at - generation.started_at
            ).total_seconds()

            await self.db.commit()

        except Exception as e:
            generation.status = "failed"
            generation.error_message = f"Ошибка генерации: {str(e)}"
            await self.db.commit()
            print(f"Generation {generation_id} failed: {str(e)}")

    async def _generate_ai_prompt(
        self, 
        questionnaire_data: Dict[str, Any], 
        frame: Frame,
        theme: str = 'light'
    ) -> str:
        """Генерация промпта для нейросети на основе анкеты и рамки"""
        
        # Базовые компоненты промпта
        setting = questionnaire_data.get('setting', 'a beautiful scene')
        clothing = questionnaire_data.get('clothing', 'elegant clothes')
        pose = questionnaire_data.get('pose', 'natural pose')
        
        # Дополнительные заметки
        additional_notes = questionnaire_data.get('additional_notes', '')
        
        # Стилевые параметры из анкеты
        style_params = questionnaire_data.get('style_parameters', {})
        artistic_style = style_params.get('artistic_style', 'realistic')
        mood = style_params.get('mood', 'neutral')
        
        # Адаптируем стиль рамки для промпта
        frame_style = self._get_frame_style_prompt(frame)
        
        # Собираем промпт
        prompt_parts = [
            f"portrait of a person in {setting}",
            f"wearing {clothing}",
            f"in a {pose}",
            f"{artistic_style} style",
            f"{mood} mood",
            frame_style,
            "high quality, detailed, masterpiece",
            "sharp focus, professional photography"
        ]
        
        # Добавляем дополнительные заметки если есть
        if additional_notes:
            prompt_parts.append(additional_notes)
        
        # Добавляем тему (dark/light)
        if theme == 'dark':
            prompt_parts.append("dark atmosphere, dramatic lighting")
        else:
            prompt_parts.append("bright lighting, cheerful atmosphere")
        
        # Убираем пустые части и соединяем
        prompt = ", ".join([part for part in prompt_parts if part])
        
        return prompt

    def _get_frame_style_prompt(self, frame: Frame) -> str:
        """Преобразование типа рамки в стилевой промпт"""
        frame_style_map = {
            'cowboy': 'western style, cowboy aesthetic, desert landscape',
            'pumpkin': 'halloween theme, pumpkin, spooky atmosphere',
            'christmas': 'christmas theme, holiday, festive, snow',
            'flowers': 'floral, garden, blossoms, nature',
            'sea': 'ocean, beach, marine, nautical',
            'popart': 'pop art, vibrant colors, comic book style',
            'wood': 'wooden frame, natural, rustic',
            'metal': 'metallic, industrial, modern',
            'gold': 'golden, luxurious, elegant, ornate'
        }
        
        return frame_style_map.get(frame.frame_type, 'artistic')