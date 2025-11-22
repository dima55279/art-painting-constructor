from fastapi import APIRouter, HTTPException, status, Request
import uuid
from datetime import datetime, timedelta
import json
from pydantic import ValidationError

from app.schemas.questionnaire import QuestionnaireData, QuestionnaireResponse

router = APIRouter()

# Временное хранилище для анкет (в памяти)
temporary_questionnaires = {}

@router.post("/", response_model=QuestionnaireResponse)
async def submit_questionnaire_public(
    request: Request,
):
    """Публичный эндпоинт для анкеты без аутентификации"""
    print("=== PUBLIC QUESTIONNAIRE SUBMISSION ===")
    
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
        
        # Дополнительная проверка на пустые строки
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

        # Генерируем session_id
        session_id = request.cookies.get("session_id")
        if not session_id:
            session_id = f"anon_{uuid.uuid4().hex}"

        # Анализируем анкету
        analysis = await _analyze_questionnaire(questionnaire_data)
        
        # Сохраняем во временное хранилище
        questionnaire_id = len(temporary_questionnaires) + 1
        questionnaire_record = {
            "id": questionnaire_id,
            "session_id": session_id,
            "user_id": None,
            "setting": questionnaire_data.setting,
            "clothing": questionnaire_data.clothing,
            "pose": questionnaire_data.pose,
            "additional_notes": questionnaire_data.additional_notes,
            "mood": analysis["mood"],
            "style_preferences": analysis["style_preferences"],
            "color_palette": analysis["color_palette"],
            "complexity_level": analysis["complexity_level"],
            "artistic_style": analysis["artistic_style"],
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=30)
        }
        
        temporary_questionnaires[questionnaire_id] = questionnaire_record

        print(f"✅ Анкета успешно сохранена с ID: {questionnaire_id}")
        
        return QuestionnaireResponse(
            success=True,
            message="Анкета успешно сохранена",
            questionnaire_id=questionnaire_id,
            recommendations={
                "estimated_complexity": analysis["complexity_level"],
                "suggested_styles": analysis["style_preferences"],
                "color_scheme": analysis["color_palette"]
            }
        )
        
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
# Остальные вспомогательные функции остаются без изменений
async def _analyze_questionnaire(data: QuestionnaireData) -> dict:
    """Анализ анкеты для подготовки данных для нейросети"""
    
    # Анализ настроения
    mood = await _detect_mood(data)
    
    # Определение стилевых предпочтений
    style_preferences = await _extract_style_preferences(data)
    
    # Подбор цветовой палитры
    color_palette = await _generate_color_palette(data)
    
    # Определение уровня сложности
    complexity_level = await _calculate_complexity(data)
    
    # Определение художественного стиля
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

async def _prepare_for_ai_generation(questionnaire: dict) -> dict:
    """Подготовка данных анкеты для передачи в нейросети"""
    return {
        "prompt_data": {
            "setting": questionnaire["setting"],
            "clothing": questionnaire["clothing"],
            "pose": questionnaire["pose"],
            "additional_notes": questionnaire["additional_notes"]
        },
        "style_parameters": {
            "mood": questionnaire["mood"],
            "artistic_style": questionnaire["artistic_style"],
            "style_preferences": questionnaire["style_preferences"],
            "color_palette": questionnaire["color_palette"],
            "complexity_level": questionnaire["complexity_level"]
        },
        "generation_instructions": await _generate_ai_prompt(questionnaire)
    }

async def _generate_ai_prompt(questionnaire: dict) -> str:
    """Генерация промпта для нейросети"""
    prompt_parts = [
        f"Человек в обстановке: {questionnaire['setting']}",
        f"Одет в: {questionnaire['clothing']}",
        f"Поза: {questionnaire['pose']}"
    ]
    
    if questionnaire['additional_notes']:
        prompt_parts.append(f"Дополнительные пожелания: {questionnaire['additional_notes']}")
    
    prompt_parts.append(f"Художественный стиль: {questionnaire['artistic_style']}")
    prompt_parts.append(f"Настроение: {questionnaire['mood']}")
    
    return ". ".join(prompt_parts)

# Добавьте сюда вспомогательные функции (_analyze_questionnaire и т.д.)
# из questionnaire.py