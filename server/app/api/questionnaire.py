from fastapi import APIRouter, HTTPException, status, Request
import uuid
from datetime import datetime, timedelta
import json
from pydantic import ValidationError

from app.schemas.questionnaire import QuestionnaireData, QuestionnaireResponse, TranslatedQuestionnaireData
from app.services.translation_service import translation_service

router = APIRouter()

# Временное хранилище для анкет (в памяти)
temporary_questionnaires = {}

@router.post("/", response_model=QuestionnaireResponse)
async def submit_questionnaire(
    request: Request,
):
    """Отправка анкеты с автоматическим переводом для нейросети"""
    print("=== QUESTIONNAIRE SUBMISSION WITH TRANSLATION ===")
    
    try:
        body_bytes = await request.body()
        
        if not body_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Пустое тело запроса"
            )
        
        try:
            raw_data = json.loads(body_bytes)
            print(f"Получены данные: {raw_data}")
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Неверный формат JSON: {str(e)}"
            )
        
        try:
            questionnaire_data = QuestionnaireData(**raw_data)
            print(f"✅ Данные прошли валидацию")
        except ValidationError as e:
            print(f"❌ Ошибка валидации: {e}")
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error['loc'])
                error_details.append(f"{field}: {error['msg']}")
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Ошибка валидации данных: {', '.join(error_details)}"
            )
        
        # Проверка на пустые строки
        if not questionnaire_data.setting.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Поле 'setting' не может быть пустым"
            )
        
        if not questionnaire_data.clothing.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Поле 'clothing' не может быть пустым"
            )
        
        if not questionnaire_data.pose.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Поле 'pose' не может быть пустым"
            )

        # Шаг 1: Анализ анкеты (определение стиля, настроения и т.д.)
        analysis = await _analyze_questionnaire(questionnaire_data)
        
        # Шаг 2: Перевод данных анкеты на английский
        print("🔄 Перевод данных анкеты на английский...")
        data_for_translation = questionnaire_data.dict()
        data_for_translation['style_parameters'] = analysis
        
        translated_data = await translation_service.translate_questionnaire_data(data_for_translation)
        
        # Шаг 3: Генерация промпта для нейросети на английском
        ai_prompt = translation_service.generate_ai_prompt(translated_data)
        print(f"🤖 Сгенерирован промпт для нейросети: {ai_prompt}")
        
        # Шаг 4: Сохранение анкеты
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = f"anon_{uuid.uuid4().hex}"

        questionnaire_id = len(temporary_questionnaires) + 1
        questionnaire_record = {
            "id": questionnaire_id,
            "session_id": session_id,
            "user_id": None,
            # Оригинальные данные
            "setting": questionnaire_data.setting,
            "clothing": questionnaire_data.clothing,
            "pose": questionnaire_data.pose,
            "additional_notes": questionnaire_data.additional_notes,
            # Переведенные данные
            "setting_en": translated_data.get('setting_en'),
            "clothing_en": translated_data.get('clothing_en'),
            "pose_en": translated_data.get('pose_en'),
            "additional_notes_en": translated_data.get('additional_notes_en'),
            # Анализ стиля
            "mood": analysis["mood"],
            "style_preferences": analysis["style_preferences"],
            "color_palette": analysis["color_palette"],
            "complexity_level": analysis["complexity_level"],
            "artistic_style": analysis["artistic_style"],
            # Промпт для нейросети
            "ai_prompt": ai_prompt,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=30)
        }
        
        temporary_questionnaires[questionnaire_id] = questionnaire_record

        print(f"✅ Анкета успешно сохранена с ID: {questionnaire_id}")
        
        # Убедимся, что возвращаем translated_prompt
        response_data = QuestionnaireResponse(
            success=True,
            message="Анкета успешно сохранена и переведена",
            questionnaire_id=questionnaire_id,
            recommendations={
                "estimated_complexity": analysis["complexity_level"],
                "suggested_styles": analysis["style_preferences"],
                "color_scheme": analysis["color_palette"]
            },
            translated_prompt=ai_prompt  # Это должно быть здесь!
        )
        
        print(f"📤 Отправляем ответ с translated_prompt: {ai_prompt}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера"
        )

# Вспомогательные функции анализа (оставляем без изменений)
async def _analyze_questionnaire(data: QuestionnaireData) -> dict:
    """Анализ анкеты для подготовки данных для нейросети"""
    
    mood = await _detect_mood(data)
    style_preferences = await _extract_style_preferences(data)
    color_palette = await _generate_color_palette(data)
    complexity_level = await _calculate_complexity(data)
    artistic_style = await _determine_artistic_style(data)
    
    return {
        "mood": mood,
        "style_preferences": style_preferences,
        "color_palette": color_palette,
        "complexity_level": complexity_level,
        "artistic_style": artistic_style
    }

async def _detect_mood(data: QuestionnaireData) -> str:
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

async def _extract_style_preferences(data: QuestionnaireData) -> list:
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

async def _generate_color_palette(data: QuestionnaireData) -> list:
    """Генерация цветовой палитры на основе анкеты"""
    base_palettes = {
        'romantic': ['#FFB6C1', '#FF69B4', '#DB7093', '#FFF0F5'],
        'joyful': ['#FFD700', '#FFA500', '#32CD32', '#87CEEB'],
        'dramatic': ['#2F4F4F', '#696969', '#800000', '#4B0082'],
        'calm': ['#87CEEB', '#98FB98', '#F0E68C', '#DDA0DD'],
        'epic': ['#8B4513', '#2F4F4F', '#8B0000', '#FFD700'],
        'mysterious': ['#4B0082', '#2F4F4F', '#191970', '#8B008B'],
        'neutral': ['#708090', '#A9A9A9', '#696969', '#2F4F4F']
    }
    
    mood = await _detect_mood(data)
    return base_palettes.get(mood, base_palettes['neutral'])

async def _calculate_complexity(data: QuestionnaireData) -> int:
    """Расчет уровня сложности"""
    complexity = 1
    
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

async def _determine_artistic_style(data: QuestionnaireData) -> str:
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

@router.get("/{questionnaire_id}")
async def get_questionnaire(
    questionnaire_id: int,
    request: Request,
):
    """Получение анкеты по ID"""
    questionnaire = temporary_questionnaires.get(questionnaire_id)
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Анкета не найдена"
        )
    
    return questionnaire

@router.get("/{questionnaire_id}/ai-prompt")
async def get_ai_prompt(
    questionnaire_id: int,
    request: Request,
):
    """Получение данных анкеты в формате для нейросети (на английском)"""
    questionnaire = temporary_questionnaires.get(questionnaire_id)
    
    if not questionnaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Анкета не найдена"
        )
    
    # Возвращаем готовый промпт для нейросети
    return {
        "questionnaire_id": questionnaire_id,
        "ai_prompt": questionnaire.get("ai_prompt", "Prompt not available"),
        "style_parameters": {
            "mood": questionnaire["mood"],
            "artistic_style": questionnaire["artistic_style"],
            "style_preferences": questionnaire["style_preferences"],
            "color_palette": questionnaire["color_palette"],
            "complexity_level": questionnaire["complexity_level"]
        },
        "translated_data": {
            "setting": questionnaire.get("setting_en", questionnaire["setting"]),
            "clothing": questionnaire.get("clothing_en", questionnaire["clothing"]),
            "pose": questionnaire.get("pose_en", questionnaire["pose"]),
            "additional_notes": questionnaire.get("additional_notes_en", questionnaire["additional_notes"])
        },
        "original_data": {
            "setting": questionnaire["setting"],
            "clothing": questionnaire["clothing"],
            "pose": questionnaire["pose"],
            "additional_notes": questionnaire["additional_notes"]
        }
    }