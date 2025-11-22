#!/usr/bin/env python3
"""
Скрипт для управления миграциями базы данных
"""

import asyncio
import os
import sys
from alembic.config import Config
from alembic import command

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import create_tables, drop_tables

def run_migrations():
    """Запуск миграций"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

def create_migration(message: str):
    """Создание новой миграции"""
    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, message=message, autogenerate=True)

def show_migration_history():
    """Показать историю миграций"""
    alembic_cfg = Config("alembic.ini")
    command.history(alembic_cfg)

def show_current_revision():
    """Показать текущую ревизию"""
    alembic_cfg = Config("alembic.ini")
    command.current(alembic_cfg)

async def reset_database():
    """Сброс базы данных (только для разработки!)"""
    print("⚠️  ВНИМАНИЕ: Это удалит все данные из базы данных!")
    confirm = input("Продолжить? (y/N): ")
    
    if confirm.lower() != 'y':
        print("Отменено.")
        return
    
    print("Удаление таблиц...")
    await drop_tables()
    
    print("Создание таблиц...")
    await create_tables()
    
    print("✅ База данных сброшена!")

def main():
    """Основная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python manage_migrations.py migrate        # Применить миграции")
        print("  python manage_migrations.py create <msg>   # Создать миграцию")
        print("  python manage_migrations.py history        # Показать историю")
        print("  python manage_migrations.py current        # Текущая ревизия")
        print("  python manage_migrations.py reset          # Сброс БД (dev)")
        return
    
    command = sys.argv[1]
    
    if command == "migrate":
        run_migrations()
        print("✅ Миграции применены!")
    
    elif command == "create":
        if len(sys.argv) < 3:
            print("Укажите сообщение для миграции")
            return
        message = sys.argv[2]
        create_migration(message)
        print(f"✅ Миграция создана: {message}")
    
    elif command == "history":
        show_migration_history()
    
    elif command == "current":
        show_current_revision()
    
    elif command == "reset":
        asyncio.run(reset_database())
    
    else:
        print(f"Неизвестная команда: {command}")

if __name__ == "__main__":
    main()