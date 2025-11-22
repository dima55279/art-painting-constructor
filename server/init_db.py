# server/init_db.py
import asyncio
import os
import sys

# Добавляем путь к app в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import create_tables, engine
from app.config import settings

async def init_database():
    """Инициализация базы данных"""
    print("Инициализация базы данных SQLite...")
    
    # Создаем директории для файлов
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.GENERATED_IMAGES_DIR, exist_ok=True)
    os.makedirs("static/uploaded_photos/avatars", exist_ok=True)
    os.makedirs("temp_uploads", exist_ok=True)  # Добавьте эту строку
    
    print(f"Директории созданы:")
    print(f"- {settings.UPLOAD_DIR}")
    print(f"- {settings.GENERATED_IMAGES_DIR}")
    print(f"- static/uploaded_photos/avatars")
    print(f"- temp_uploads")
    
    # Создаем таблицы
    await create_tables()
    
    print(f"База данных инициализирована: {settings.DATABASE_URL}")
    print("Готово! Теперь можно запускать приложение.")

async def update_photo_table():
    """Обновление таблицы photos для поддержки nullable user_id"""
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Проверяем, существует ли таблица
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='photos'"))
        table_exists = result.scalar() is not None
        
        if table_exists:
            # Проверяем, есть ли уже столбец user_id
            result = await conn.execute(text("PRAGMA table_info(photos)"))
            columns = result.fetchall()
            user_id_column = any(col[1] == 'user_id' for col in columns)
            
            if user_id_column:
                # Меняем столбец на nullable
                await conn.execute(text("ALTER TABLE photos RENAME TO photos_old"))
                await conn.execute(text("""
                    CREATE TABLE photos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        original_filename VARCHAR(255) NOT NULL,
                        stored_filename VARCHAR(255) NOT NULL UNIQUE,
                        file_path VARCHAR(500) NOT NULL,
                        file_size INTEGER NOT NULL,
                        mime_type VARCHAR(100) NOT NULL,
                        width INTEGER,
                        height INTEGER,
                        image_metadata TEXT,
                        face_detected BOOLEAN DEFAULT 0,
                        face_quality_score INTEGER,
                        face_analysis_data TEXT,
                        is_approved BOOLEAN DEFAULT 0,
                        rejection_reason TEXT,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """))
                await conn.execute(text("""
                    INSERT INTO photos 
                    SELECT * FROM photos_old
                """))
                await conn.execute(text("DROP TABLE photos_old"))

if __name__ == "__main__":
    asyncio.run(init_database())