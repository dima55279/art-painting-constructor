# Руководство по миграциям базы данных

## Инициализация миграций

При первом запуске выполните:

```bash
# Применить начальные миграции
alembic upgrade head

# Или используйте скрипт
python migrations/manage_migrations.py migrate