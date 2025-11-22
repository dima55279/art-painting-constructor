import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.frame import Frame
from sqlalchemy import delete

async def reset_frames():
    """Полный сброс таблицы рамок"""
    async with AsyncSessionLocal() as db:
        print("Очистка таблицы рамок...")
        
        # Удаляем все рамки
        await db.execute(delete(Frame))
        await db.commit()
        
        print("✅ Таблица рамок очищена")
        print("Запустите update_frames.py для создания новых рамок")

if __name__ == "__main__":
    asyncio.run(reset_frames())