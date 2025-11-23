import aiohttp
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.base_url = "https://translate.googleapis.com/translate_a/single"
    
    async def translate_text(self, text: str, target_lang: str = 'en') -> str:
        """
        Перевод текста на указанный язык с помощью Google Translate API
        """
        if not text or not text.strip():
            return text
            
        try:
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': target_lang,
                'dt': 't',
                'q': text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Извлекаем переведенный текст из сложной структуры ответа
                        translated_text = data[0][0][0] if data and data[0] else text
                        logger.info(f"Translated: '{text}' -> '{translated_text}'")
                        return translated_text
                    else:
                        logger.warning(f"Translation failed for: {text}. Status: {response.status}")
                        return text
                        
        except Exception as e:
            logger.error(f"Translation error for '{text}': {str(e)}")
            return text
    
    async def translate_questionnaire_data(self, questionnaire_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Перевод всех текстовых полей анкеты на английский
        """
        translated_data = questionnaire_data.copy()
        
        # Поля для перевода
        fields_to_translate = [
            'setting', 'clothing', 'pose'
        ]
        
        # Асинхронно переводим все поля
        translation_tasks = []
        for field in fields_to_translate:
            if field in translated_data and translated_data[field]:
                translation_tasks.append(
                    self.translate_text(translated_data[field])
                )
            else:
                translation_tasks.append(None)
        
        # Ждем завершения всех переводов
        translated_results = []
        for task in translation_tasks:
            if task:
                translated_results.append(await task)
            else:
                translated_results.append(None)
        
        # Обновляем данные переведенными версиями
        for i, field in enumerate(fields_to_translate):
            if translated_results[i] is not None:
                translated_data[f"{field}_en"] = translated_results[i]
        
        return translated_data
    
    def generate_ai_prompt(self, translated_data: Dict[str, Any]) -> str:
        """
        Генерация промпта для нейросети на английском языке
        на основе переведенных данных анкеты
        """
        prompt_parts = []
        
        # Основные поля анкеты
        setting = translated_data.get('setting_en', translated_data.get('setting', 'Not specified'))
        clothing = translated_data.get('clothing_en', translated_data.get('clothing', 'Not specified'))
        pose = translated_data.get('pose_en', translated_data.get('pose', 'Not specified'))
        
        prompt_parts.append(f"In the setting of {setting}, picture a person")
        prompt_parts.append(f"wearing {clothing}")
        prompt_parts.append(f"in a {pose} pose")
        
        # Стилевые параметры (уже на английском из анализа)
        style_params = translated_data.get('style_parameters', {})
        if style_params.get('artistic_style'):
            prompt_parts.append(f"Artistic style: {style_params['artistic_style']}")
        if style_params.get('mood'):
            prompt_parts.append(f"Mood: {style_params['mood']}")
        
        return ". ".join(prompt_parts) + "."

# Глобальный экземпляр сервиса перевода
translation_service = TranslationService()