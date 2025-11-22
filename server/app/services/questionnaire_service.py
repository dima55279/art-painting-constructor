import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.questionnaire import Questionnaire
from app.models.user import User
from app.schemas.questionnaire import QuestionnaireData, QuestionnaireAnalysis

class QuestionnaireService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_questionnaire(
        self, 
        questionnaire_data: QuestionnaireData,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Questionnaire:
        """Создание новой анкеты"""
        
        # Генерируем session_id для неавторизованных пользователей
        if not session_id and not user_id:
            session_id = f"anon_{uuid.uuid4().hex}"
        
        # Анализируем анкету для нейросети
        analysis = await self._analyze_questionnaire(questionnaire_data)
        
        # Создаем анкету
        questionnaire = Questionnaire(
            session_id=session_id,
            user_id=user_id,
            setting=questionnaire_data.setting,
            clothing=questionnaire_data.clothing,
            pose=questionnaire_data.pose,
            additional_notes=questionnaire_data.additional_notes,
            mood=analysis.mood,
            style_preferences=analysis.style_preferences,
            color_palette=analysis.color_palette,
            complexity_level=analysis.complexity_level,
            artistic_style=analysis.artistic_style,
            expires_at=datetime.utcnow() + timedelta(days=30) if not user_id else None
        )
        
        self.db.add(questionnaire)
        await self.db.commit()
        await self.db.refresh(questionnaire)
        
        return questionnaire

    async def _analyze_questionnaire(self, data: QuestionnaireData) -> QuestionnaireAnalysis:
        """Анализ анкеты для подготовки данных для нейросети"""
        
        # Анализ настроения на основе введенных данных
        mood = await self._detect_mood(data)
        
        # Определение стилевых предпочтений
        style_preferences = await self._extract_style_preferences(data)
        
        # Подбор цветовой палитры
        color_palette = await self._generate_color_palette(data)
        
        # Определение уровня сложности
        complexity_level = await self._calculate_complexity(data)
        
        # Определение художественного стиля
        artistic_style = await self._determine_artistic_style(data)
        
        return QuestionnaireAnalysis(
            mood=mood,
            style_preferences=style_preferences,
            color_palette=color_palette,
            complexity_level=complexity_level,
            artistic_style=artistic_style
        )

    async def _detect_mood(self, data: QuestionnaireData) -> str:
        """Определение настроения на основе анкеты"""
        mood_keywords = {
            'романтический': 'romantic',
            'веселый': 'joyful', 
            'драматический': 'dramatic',
            'спокойный': 'calm',
            'эпический': 'epic',
            'таинственный': 'mysterious'
        }
        
        text = f"{data.setting} {data.clothing} {data.pose} {data.additional_notes or ''}".lower()
        
        for keyword, mood in mood_keywords.items():
            if keyword in text:
                return mood
        
        return 'neutral'

    async def _extract_style_preferences(self, data: QuestionnaireData) -> list:
        """Извлечение стилевых предпочтений"""
        styles = []
        
        text = f"{data.setting} {data.clothing} {data.pose}".lower()
        
        style_mapping = {
            'фэнтези': 'fantasy',
            'сказка': 'fairy_tale',
            'исторический': 'historical',
            'современный': 'modern',
            'футуристический': 'futuristic',
            'реалистичный': 'realistic',
            'аниме': 'anime',
            'мультяшный': 'cartoon'
        }
        
        for ru_style, en_style in style_mapping.items():
            if ru_style in text:
                styles.append(en_style)
        
        return styles if styles else ['realistic']

    async def _generate_color_palette(self, data: QuestionnaireData) -> list:
        """Генерация цветовой палитры на основе анкеты"""
        # Базовая палитра
        base_palettes = {
            'romantic': ['#FFB6C1', '#FF69B4', '#DB7093', '#FFF0F5'],
            'joyful': ['#FFD700', '#FFA500', '#32CD32', '#87CEEB'],
            'dramatic': ['#2F4F4F', '#696969', '#800000', '#4B0082'],
            'calm': ['#87CEEB', '#98FB98', '#F0E68C', '#DDA0DD'],
            'epic': ['#8B4513', '#2F4F4F', '#8B0000', '#FFD700'],
            'mysterious': ['#4B0082', '#2F4F4F', '#191970', '#8B008B'],
            'neutral': ['#708090', '#A9A9A9', '#696969', '#2F4F4F']
        }
        
        mood = await self._detect_mood(data)
        return base_palettes.get(mood, base_palettes['neutral'])

    async def _calculate_complexity(self, data: QuestionnaireData) -> int:
        """Расчет уровня сложности"""
        complexity = 1
        
        # Увеличиваем сложность при детальном описании
        details_count = sum([
            len(data.setting.split()),
            len(data.clothing.split()), 
            len(data.pose.split()),
            len(data.additional_notes.split()) if data.additional_notes else 0
        ])
        
        if details_count > 20:
            complexity = 3
        elif details_count > 10:
            complexity = 2
        
        return complexity

    async def _determine_artistic_style(self, data: QuestionnaireData) -> str:
        """Определение художественного стиля"""
        text = f"{data.setting} {data.clothing} {data.pose}".lower()
        
        if any(word in text for word in ['фэнтези', 'дракон', 'волшеб']):
            return 'fantasy_art'
        elif any(word in text for word in ['космос', 'футуро', 'робот']):
            return 'sci_fi'
        elif any(word in text for word in ['исторический', 'рыцарь', 'замок']):
            return 'historical'
        elif any(word in text for word in ['аниме', 'мульт']):
            return 'anime'
        else:
            return 'realistic'

    async def get_questionnaire(self, questionnaire_id: int, user_id: Optional[int] = None, session_id: Optional[str] = None) -> Optional[Questionnaire]:
        """Получение анкеты по ID"""
        query = select(Questionnaire).where(Questionnaire.id == questionnaire_id)
        
        if user_id:
            query = query.where(Questionnaire.user_id == user_id)
        elif session_id:
            query = query.where(Questionnaire.session_id == session_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def prepare_for_ai_generation(self, questionnaire_id: int) -> Dict[str, Any]:
        """Подготовка данных анкеты для передачи в нейросеть"""
        questionnaire = await self.db.get(Questionnaire, questionnaire_id)
        if not questionnaire:
            raise ValueError("Анкета не найдена")
        
        return {
            "prompt_data": {
                "setting": questionnaire.setting,
                "clothing": questionnaire.clothing,
                "pose": questionnaire.pose,
                "additional_notes": questionnaire.additional_notes
            },
            "style_parameters": {
                "mood": questionnaire.mood,
                "artistic_style": questionnaire.artistic_style,
                "style_preferences": questionnaire.style_preferences,
                "color_palette": questionnaire.color_palette,
                "complexity_level": questionnaire.complexity_level
            },
            "generation_instructions": await self._generate_ai_prompt(questionnaire)
        }

    async def _generate_ai_prompt(self, questionnaire: Questionnaire) -> str:
        """Генерация промпта для нейросети"""
        prompt_parts = [
            f"Человек в обстановке: {questionnaire.setting}",
            f"Одет в: {questionnaire.clothing}",
            f"Поза: {questionnaire.pose}"
        ]
        
        if questionnaire.additional_notes:
            prompt_parts.append(f"Дополнительные пожелания: {questionnaire.additional_notes}")
        
        prompt_parts.append(f"Художественный стиль: {questionnaire.artistic_style}")
        prompt_parts.append(f"Настроение: {questionnaire.mood}")
        
        return ". ".join(prompt_parts)