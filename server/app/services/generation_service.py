import aiofiles
import os
import asyncio
import uuid
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
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
from app.services.paint_by_numbers_service import paint_by_numbers_service

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
    
    async def add_watermark_to_image(self, image_bytes: bytes) -> bytes:
        """
        Добавление водяного знака на изображение (улучшенная версия)
        """
        try:
            print("🖼️ Adding watermark to image...")
            
            # Преобразуем байты в изображение PIL
            image_pil = Image.open(BytesIO(image_bytes)).convert("RGBA")
            
            # Создаем водяной знак
            watermark = await self._create_or_load_watermark()
            if watermark is None:
                print("⚠️ Could not create watermark, returning original image")
                return image_bytes
            
            # Изменяем размер водяного знака
            image_width, image_height = image_pil.size
            wm_width, wm_height = watermark.size
            
            # Рассчитываем размер водяного знака (60% от высоты изображения)
            new_wm_height = int(image_height * 0.6)
            new_wm_width = int(wm_width * (new_wm_height / wm_height))
            
            watermark = watermark.resize((new_wm_width, new_wm_height), Image.Resampling.LANCZOS)
            
            # Создаем копию изображения для наложения водяного знака
            watermarked = image_pil.copy()
            
            # Позиционируем водяной знак (в центре)
            position = (
                (image_width - new_wm_width) // 2,
                (image_height - new_wm_height) // 2
            )
            
            print(f"📏 Image: {image_width}x{image_height}")
            print(f"📏 Watermark: {new_wm_width}x{new_wm_height}")
            print(f"📍 Position: {position}")
            
            # Создаем маску для водяного знака (полупрозрачная)
            watermark_with_alpha = watermark.copy()
            # Устанавливаем прозрачность 60%
            alpha = watermark_with_alpha.split()[3]
            alpha = alpha.point(lambda p: int(p * 0.8))
            watermark_with_alpha.putalpha(alpha)
            
            # Накладываем водяной знак
            watermarked.paste(watermark_with_alpha, position, watermark_with_alpha)
            
            # Конвертируем обратно в байты
            output = BytesIO()
            watermarked.save(output, format='PNG', quality=95)
            output.seek(0)
            
            print("✅ Watermark added successfully")
            return output.getvalue()
            
        except Exception as e:
            print(f"❌ Error adding watermark: {str(e)}")
            import traceback
            traceback.print_exc()
            return image_bytes
    
    async def _create_or_load_watermark(self) -> Image.Image:
        """
        Создание или загрузка водяного знака
        """
        watermark_path = "static/watermark.png"
        
        try:
            # Пробуем загрузить существующий водяной знак
            if os.path.exists(watermark_path):
                watermark = Image.open(watermark_path).convert("RGBA")
                print(f"✅ Loaded watermark from {watermark_path}")
                return watermark
        except Exception as e:
            print(f"⚠️ Error loading watermark: {str(e)}")
        
        # Создаем новый водяной знак
        print("🖌️ Creating new watermark...")
        return await self._create_default_watermark(watermark_path)
    
    async def _create_default_watermark(self, path: str) -> Image.Image:
        """
        Создание водяного знака по умолчанию с использованием PIL
        """
        # Создаем изображение 400x100 с прозрачным фоном
        watermark = Image.new('RGBA', (400, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Пробуем использовать различные шрифты
        font_paths = [
            "arial.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc"
        ]
        
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 40)
                break
            except:
                continue
        
        if font is None:
            # Используем стандартный шрифт
            font = ImageFont.load_default()
            print("⚠️ Using default font for watermark")
        
        # Добавляем текст водяного знака
        text = "Art Painting"
        
        # Вычисляем размер текста
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Если не можем вычислить, используем приблизительные значения
            text_width = 200
            text_height = 50
        
        # Позиционируем по центру
        x = (400 - text_width) // 2
        y = (100 - text_height) // 2
        
        # Добавляем тень для лучшей видимости
        shadow_color = (0, 0, 0, 100)  # Черный с прозрачностью
        text_color = (255, 255, 255, 180)  # Белый с прозрачностью
        
        # Рисуем тень
        draw.text((x + 2, y + 2), text, fill=shadow_color, font=font)
        # Рисуем основной текст
        draw.text((x, y), text, fill=text_color, font=font)
        
        # Сохраняем водяной знак
        os.makedirs(os.path.dirname(path), exist_ok=True)
        watermark.save(path, 'PNG')
        print(f"✅ Created watermark at {path}")
        
        return watermark
        
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
            
            if not photo:
                raise ValueError("Не найдено фото")

            # Получаем рамку только если она указана
            frame = None
            if generation.frame_id:
                frame = await self.db.get(Frame, generation.frame_id)

            # Генерируем промпт без учета рамки
            ai_prompt = await self._generate_ai_prompt(
                generation.questionnaire_answers,
                frame,  # Передаем, но не используем в промпте
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

            # СОХРАНЯЕМ ОРИГИНАЛЬНОЕ ИЗОБРАЖЕНИЕ
            original_filename = f"original_{uuid.uuid4().hex[:8]}.png"
            original_filepath = os.path.join(settings.GENERATED_IMAGES_DIR, original_filename)
            
            async with aiofiles.open(original_filepath, 'wb') as f:
                await f.write(image_bytes)
            
            # ДОБАВЛЯЕМ ВОДЯНОЙ ЗНАК НА ОРИГИНАЛ
            watermarked_bytes = await self.add_watermark_to_image(image_bytes)
            
            # Сохраняем изображение с водяным знаком
            watermarked_filename = f"watermarked_{uuid.uuid4().hex[:8]}.png"
            watermarked_filepath = os.path.join(settings.GENERATED_IMAGES_DIR, watermarked_filename)
            
            async with aiofiles.open(watermarked_filepath, 'wb') as f:
                await f.write(watermarked_bytes)
            
            # СОЗДАЕМ ИЗОБРАЖЕНИЕ, РАЗБИТОЕ ПО НОМЕРАМ
            print("🎨 Создаем изображение по номерам...")
            numbered_bytes, colors_used = await paint_by_numbers_service.create_numbered_image(
                image_bytes,
                add_watermark=False
            )
            
            if numbered_bytes:
                # ДОБАВЛЯЕМ ВОДЯНОЙ ЗНАК НА ИЗОБРАЖЕНИЕ ПО НОМЕРАМ
                numbered_watermarked_bytes = await self.add_watermark_to_image(numbered_bytes)
                
                # Сохраняем изображение по номерам с водяным знаком
                numbered_filename = f"numbered_{uuid.uuid4().hex[:8]}.png"
                numbered_filepath = os.path.join(settings.GENERATED_IMAGES_DIR, numbered_filename)
                
                async with aiofiles.open(numbered_filepath, 'wb') as f:
                    await f.write(numbered_watermarked_bytes)
                
                print(f"✅ Создано изображение по номерам: {numbered_filepath}")
                print(f"🎨 Использовано цветов: {len(colors_used)}")
                
                # Обновляем базу данных с URL изображения по номерам
                generation.numbered_image_url = f"/static/generated_images/{numbered_filename}"
                generation.colors_used = colors_used
                generation.complexity_score = len(colors_used)
            else:
                print("⚠️ Не удалось создать изображение по номерам")
                generation.colors_used = []
                generation.complexity_score = 0
            
            print(f"✅ Сохранены изображения:")
            print(f"   Оригинал: {original_filepath}")
            print(f"   С водяным знаком: {watermarked_filepath}")
            print(f"   По номерам: {numbered_filepath if numbered_bytes else 'НЕТ'}")

            # ОБНОВЛЯЕМ БАЗУ ДАННЫХ
            generation.status = "completed"
            generation.completed_at = datetime.utcnow()
            generation.progress = 100
            
            # Сохраняем URL водяного знака для отображения
            generation.generated_image_url = f"/static/generated_images/{watermarked_filename}"
            generation.preview_image_url = f"/static/generated_images/{watermarked_filename}"
            
            # Сохраняем URL оригинального изображения в метаданных
            if generation.generation_parameters is None:
                generation.generation_parameters = {}
            
            generation.generation_parameters['original_image_url'] = f"/static/generated_images/{original_filename}"
            
            # Время генерации
            generation.generation_time_seconds = (
                generation.completed_at - generation.started_at
            ).total_seconds()

            print(f"✅ Установлен URL с водяным знаком: {generation.generated_image_url}")
            print(f"✅ Установлен URL по номерам: {generation.numbered_image_url}")
            
            await self.db.commit()
            await self.db.refresh(generation)
            
            print(f"✅ Генерация {generation_id} завершена успешно")

        except Exception as e:
            print(f"❌ Генерация {generation_id} не удалась: {str(e)}")
            import traceback
            traceback.print_exc()
            
            generation.status = "failed"
            generation.error_message = f"Ошибка генерации: {str(e)}"
            await self.db.commit()

    async def _get_ai_prompt_from_questionnaire(self, questionnaire_data: Dict[str, Any]) -> str:
        """Получение AI промпта из данных анкеты"""
        if 'translated_prompt' in questionnaire_data:
            return questionnaire_data['translated_prompt']
        
        if 'ai_prompt' in questionnaire_data:
            return questionnaire_data['ai_prompt']
        
        return None

    async def _generate_ai_prompt(
        self, 
        questionnaire_data: Dict[str, Any], 
        frame: Optional[Frame] = None,  # Делаем параметр опциональным
        theme: str = 'light'
    ) -> str:
        """Генерация промпта для нейросети на основе анкеты (без учета рамки)"""
        
        # Базовые компоненты промпта
        setting = questionnaire_data.get('setting', 'a beautiful scene')
        clothing = questionnaire_data.get('clothing', 'elegant clothes')
        pose = questionnaire_data.get('pose', 'natural pose')
        
        # Дополнительные заметки
        additional_notes = questionnaire_data.get('additional_notes', '')
        
        # Собираем промпт без учета рамки
        prompt_parts = [
            f"portrait of a person in {setting}",
            f"wearing {clothing}",
            f"in a {pose}",
            f"realistic style",
            f"high quality, detailed, masterpiece",
            f"sharp focus, professional photography"
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
            
            if not photo:
                raise ValueError("Не найдено фото")

            # Получаем рамку только если она указана
            frame = None
            if generation.frame_id:
                frame = await self.db.get(Frame, generation.frame_id)

            # Генерируем промпт без учета рамки
            ai_prompt = await self._generate_ai_prompt(
                generation.questionnaire_answers,
                frame,  # Передаем, но не используем в промпте
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

            # СОХРАНЯЕМ ОРИГИНАЛЬНОЕ ИЗОБРАЖЕНИЕ
            original_filename = f"original_{uuid.uuid4().hex[:8]}.png"
            original_filepath = os.path.join(settings.GENERATED_IMAGES_DIR, original_filename)
            
            async with aiofiles.open(original_filepath, 'wb') as f:
                await f.write(image_bytes)
            
            # ДОБАВЛЯЕМ ВОДЯНОЙ ЗНАК НА ОРИГИНАЛ
            watermarked_bytes = await self.add_watermark_to_image(image_bytes)
            
            # Сохраняем изображение с водяным знаком
            watermarked_filename = f"watermarked_{uuid.uuid4().hex[:8]}.png"
            watermarked_filepath = os.path.join(settings.GENERATED_IMAGES_DIR, watermarked_filename)
            
            async with aiofiles.open(watermarked_filepath, 'wb') as f:
                await f.write(watermarked_bytes)
            
            # СОЗДАЕМ ИЗОБРАЖЕНИЕ, РАЗБИТОЕ ПО НОМЕРАМ
            print("🎨 Создаем изображение по номерам...")
            numbered_bytes, colors_used = await paint_by_numbers_service.create_numbered_image(
                image_bytes,
                add_watermark=False
            )
            
            if numbered_bytes:
                # ДОБАВЛЯЕМ ВОДЯНОЙ ЗНАК НА ИЗОБРАЖЕНИЕ ПО НОМЕРАМ
                numbered_watermarked_bytes = await self.add_watermark_to_image(numbered_bytes)
                
                # Сохраняем изображение по номерам с водяным знаком
                numbered_filename = f"numbered_{uuid.uuid4().hex[:8]}.png"
                numbered_filepath = os.path.join(settings.GENERATED_IMAGES_DIR, numbered_filename)
                
                async with aiofiles.open(numbered_filepath, 'wb') as f:
                    await f.write(numbered_watermarked_bytes)
                
                print(f"✅ Создано изображение по номерам: {numbered_filepath}")
                print(f"🎨 Использовано цветов: {len(colors_used)}")
                
                # Обновляем базу данных с URL изображения по номерам
                generation.numbered_image_url = f"/static/generated_images/{numbered_filename}"
                generation.colors_used = colors_used
                generation.complexity_score = len(colors_used)
            else:
                print("⚠️ Не удалось создать изображение по номерам")
                generation.colors_used = []
                generation.complexity_score = 0
            
            print(f"✅ Сохранены изображения:")
            print(f"   Оригинал: {original_filepath}")
            print(f"   С водяным знаком: {watermarked_filepath}")
            print(f"   По номерам: {numbered_filepath if numbered_bytes else 'НЕТ'}")

            # ОБНОВЛЯЕМ БАЗУ ДАННЫХ
            generation.status = "completed"
            generation.completed_at = datetime.utcnow()
            generation.progress = 100
            
            # Сохраняем URL водяного знака для отображения
            generation.generated_image_url = f"/static/generated_images/{watermarked_filename}"
            generation.preview_image_url = f"/static/generated_images/{watermarked_filename}"
            
            # Сохраняем URL оригинального изображения в метаданных
            if generation.generation_parameters is None:
                generation.generation_parameters = {}
            
            generation.generation_parameters['original_image_url'] = f"/static/generated_images/{original_filename}"
            
            # Время генерации
            generation.generation_time_seconds = (
                generation.completed_at - generation.started_at
            ).total_seconds()

            print(f"✅ Установлен URL с водяным знаком: {generation.generated_image_url}")
            print(f"✅ Установлен URL по номерам: {generation.numbered_image_url}")
            
            await self.db.commit()
            await self.db.refresh(generation)
            
            print(f"✅ Генерация {generation_id} завершена успешно")

        except Exception as e:
            print(f"❌ Генерация {generation_id} не удалась: {str(e)}")
            import traceback
            traceback.print_exc()
            
            generation.status = "failed"
            generation.error_message = f"Ошибка генерации: {str(e)}"
            await self.db.commit()

    async def _generate_ai_prompt(
        self, 
        questionnaire_data: Dict[str, Any], 
        frame: Optional[Frame] = None,  # Делаем параметр опциональным
        theme: str = 'light'
    ) -> str:
        """Генерация промпта для нейросети на основе анкеты (без учета рамки)"""
        
        # Базовые компоненты промпта
        setting = questionnaire_data.get('setting', 'a beautiful scene')
        clothing = questionnaire_data.get('clothing', 'elegant clothes')
        pose = questionnaire_data.get('pose', 'natural pose')
        
        # Дополнительные заметки
        additional_notes = questionnaire_data.get('additional_notes', '')
        
        # Собираем промпт без учета рамки
        prompt_parts = [
            f"portrait of a person in {setting}",
            f"wearing {clothing}",
            f"in a {pose}",
            f"realistic style",
            f"high quality, detailed, masterpiece",
            f"sharp focus, professional photography"
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