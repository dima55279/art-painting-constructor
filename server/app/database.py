# app/database.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

# Создаем директорию для базы данных если её нет
os.makedirs(os.path.dirname("./art_painting.db"), exist_ok=True)

# Создаем асинхронный движок для SQLite
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()

# Импортируем модели после создания Base
from app.models.user import User
from app.models.photo import Photo
from app.models.frame import Frame
from app.models.generated_image import GeneratedImage
from app.models.order import Order
from app.models.subscription import Subscription
from app.models.questionnaire import Questionnaire

async def get_db() -> AsyncSession:
    """
    Dependency для получения асинхронной сессии БД
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_tables():
    """Создание всех таблиц в БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Все таблицы успешно созданы!")

async def drop_tables():
    """Удаление всех таблиц (для тестов)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)