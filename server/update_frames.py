import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.frame import Frame
from sqlalchemy import select

async def update_frames():
    """Обновление рамок в базе данных"""
    async with AsyncSessionLocal() as db:
        print("Обновление рамок в базе данных...")
        
        # Данные для обновления рамок
        frames_data = [
            {
                "name": "Вестерн",
                "description": "Рамка в стиле дикого запада",
                "frame_type": "cowboy",
                "preview_image_url": "/static/frames/cowboy.png",
                "model_3d_url": "/static/frames/cowboy.glb", 
                "price": 0.0,
                "is_premium": False,
                "complexity_level": 2,
                "estimated_time_hours": 2.0,
                "tags": ["вестерн", "ковбой", "дерево"],
                "sort_order": 1
            },
            {
                "name": "Хэллоуин",
                "description": "Тематическая рамка для Хэллоуина",
                "frame_type": "pumpkin",
                "preview_image_url": "/static/frames/pumpkin.png", 
                "model_3d_url": "/static/frames/pumpkin.glb",
                "price": 0.0,
                "is_premium": False,
                "complexity_level": 2,
                "estimated_time_hours": 2.0,
                "tags": ["хэллоуин", "праздник", "оранжевый"],
                "sort_order": 2
            },
            {
                "name": "Цветочная",
                "description": "Нежная рамка с цветочными мотивами",
                "frame_type": "flowers",
                "preview_image_url": "/static/frames/flowers.png",
                "model_3d_url": "/static/frames/flowers.glb",
                "price": 0.0, 
                "is_premium": False,
                "complexity_level": 2,
                "estimated_time_hours": 2.5,
                "tags": ["цветы", "нежность", "розовый"],
                "sort_order": 3
            },
            {
                "name": "Новогодняя",
                "description": "Праздничная новогодняя рамка",
                "frame_type": "christmas", 
                "preview_image_url": "/static/frames/christmas.png",
                "model_3d_url": "/static/frames/christmas.glb",
                "price": 0.0,
                "is_premium": False,
                "complexity_level": 2,
                "estimated_time_hours": 2.0,
                "tags": ["новый год", "праздник", "зеленый"],
                "sort_order": 4
            },
            {
                "name": "Морская", 
                "description": "Рамка в морском стиле с элементами волн",
                "frame_type": "sea",
                "preview_image_url": "/static/frames/sea.png",
                "model_3d_url": "/static/frames/sea.glb",
                "price": 0.0,
                "is_premium": False,
                "complexity_level": 2,
                "estimated_time_hours": 2.5,
                "tags": ["море", "волны", "синий"],
                "sort_order": 5
            },
            {
                "name": "Хогвартс", 
                "description": "Рамка в стиле факультетов Хогвартса",
                "frame_type": "harry",
                "preview_image_url": "/static/frames/harry.png",
                "model_3d_url": "/static/frames/harry.glb",
                "price": 0.0,
                "is_premium": False,
                "complexity_level": 2,
                "estimated_time_hours": 2.5,
                "tags": ["море", "волны", "синий"],
                "sort_order": 6
            },
        ]

        # Получаем существующие рамки
        result = await db.execute(select(Frame))
        existing_frames = result.scalars().all()
        
        existing_frame_names = {frame.name for frame in existing_frames}
        updated_count = 0
        created_count = 0

        for frame_data in frames_data:
            # Проверяем, существует ли рамка с таким именем
            existing_frame = next((f for f in existing_frames if f.name == frame_data["name"]), None)
            
            if existing_frame:
                # Обновляем существующую рамку
                for key, value in frame_data.items():
                    if hasattr(existing_frame, key):
                        setattr(existing_frame, key, value)
                updated_count += 1
                print(f"✓ Обновлена рамка: {frame_data['name']}")
            else:
                # Создаем новую рамку
                frame = Frame(**frame_data)
                db.add(frame)
                created_count += 1
                print(f"+ Создана рамка: {frame_data['name']}")

        await db.commit()
        print(f"\n✅ Обновление завершено!")
        print(f"Обновлено рамок: {updated_count}")
        print(f"Создано новых рамок: {created_count}")
        print(f"Всего рамок в базе: {len(existing_frames) + created_count}")

if __name__ == "__main__":
    asyncio.run(update_frames())