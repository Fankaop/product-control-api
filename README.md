# Production Control API

Система контроля заданий на выпуск продукции. REST API на FastAPI с асинхронной обработкой задач через Celery.

## Стек технологий

- **API**: FastAPI + Uvicorn
- **БД**: PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic
- **Очередь задач**: Celery 5 + RabbitMQ (broker) + Redis (result backend)
- **Мониторинг задач**: Flower
- **Кэш**: Redis
- **Хранилище файлов**: MinIO (S3-совместимое)
- **Аутентификация**: JWT (python-jose)
- **Вебхуки**: HMAC-SHA256 подпись
- **Отчёты**: Excel (openpyxl) + PDF (fpdf2)

## Быстрый старт

### Требования

- Docker + Docker Compose
- Python 3.11+ и [uv](https://docs.astral.sh/uv/) (для локальной разработки)

### Запуск через Docker

```bash
# 1. Скопируй конфиг
cp .env.example .env

# 2. Сгенерируй секретный ключ и вставь в .env
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Запусти все сервисы
docker compose up --build -d
```

После запуска доступно:
| Сервис | URL |
|--------|-----|
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Flower (мониторинг Celery) | http://localhost:5555 |
| RabbitMQ Management | http://localhost:15672 (guest / guest) |
| MinIO Console | http://localhost:9001 (minioadmin / minioadmin) |

### Локальная разработка

```bash
# Установить зависимости
uv sync

# Запустить инфраструктуру (PostgreSQL, Redis, RabbitMQ, MinIO)
docker compose up postgres redis rabbitmq minio -d

# Применить миграции
uv run alembic upgrade head

# Запустить API
uv run uvicorn src.main:app --reload --port 8000

# В отдельном терминале — Celery worker
uv run celery -A src.celery_app worker --loglevel=info

# В отдельном терминале — Celery beat (планировщик)
uv run celery -A src.celery_app beat --loglevel=info
```

## Переменные окружения

Скопируй `.env.example` в `.env` и заполни:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `JWT_SECRET_KEY` | Секретный ключ для JWT | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | Алгоритм подписи | `HS256` |
| `JWT_EXPIRE_MINUTES` | Время жизни токена (мин) | `60` |
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql+asyncpg://...` |
| `REDIS_URL` | URL Redis | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | URL RabbitMQ | `amqp://guest:guest@localhost:5672//` |
| `CELERY_RESULT_BACKEND` | Backend для результатов Celery | `redis://localhost:6379/1` |
| `MINIO_ENDPOINT` | Адрес MinIO | `localhost:9000` |
| `MINIO_ACCESS_KEY` | Логин MinIO | `minioadmin` |
| `MINIO_SECRET_KEY` | Пароль MinIO | `minioadmin` |

## API Reference

Все эндпоинты (кроме `/health`, `/auth/register`, `/auth/login`) требуют заголовок:
```
Authorization: Bearer <token>
```

### Аутентификация — `/api/v1/auth`

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/register` | Регистрация пользователя |
| `POST` | `/login` | Вход, возвращает JWT токен |
| `GET` | `/me` | Данные текущего пользователя |

### Задания на выпуск — `/api/v1/batches`

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/batches` | Создать одно или несколько заданий |
| `GET` | `/batches` | Список заданий с фильтрами (`is_closed`, `batch_number`, `batch_date`, `work_center_id`, `shift`, `limit`, `offset`) |
| `GET` | `/batches/{id}` | Получить задание с продуктами |
| `PATCH` | `/batches/{id}` | Обновить / закрыть задание |
| `GET` | `/batches/{id}/statistics` | Статистика по заданию |
| `POST` | `/batches/{id}/aggregate-async` | Агрегировать продукты асинхронно (Celery) |
| `POST` | `/batches/{id}/reports` | Сгенерировать отчёт (Excel / PDF) |
| `POST` | `/batches/export` | Экспорт заданий в файл (Celery) |
| `POST` | `/batches/import` | Импорт заданий из Excel-файла (Celery) |

### Продукты — `/api/v1`

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/products` | Добавить продукт |
| `POST` | `/batches/{id}/aggregate` | Агрегировать продукт по уникальному коду |

### Аналитика — `/api/v1/analytics`

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/analytics/dashboard` | Общая статистика по всем заданиям |
| `GET` | `/analytics/batches/{id}` | Статистика конкретного задания |
| `GET` | `/analytics/work-centers/{id}` | Статистика по рабочему центру |
| `POST` | `/analytics/compare-batches` | Сравнение нескольких заданий |

### Вебхуки — `/api/v1/webhooks`

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/webhooks` | Создать подписку |
| `GET` | `/webhooks` | Список подписок |
| `PATCH` | `/webhooks/{id}` | Обновить подписку (активировать/деактивировать) |
| `DELETE` | `/webhooks/{id}` | Удалить подписку |
| `GET` | `/webhooks/{id}/deliveries` | История доставок |

**Поддерживаемые события:**

| Событие | Когда срабатывает |
|---------|-------------------|
| `batch_created` | Создано новое задание |
| `batch_updated` | Задание изменено |
| `batch_closed` | Задание закрыто |
| `product_aggregated` | Продукт агрегирован |
| `report_generated` | Отчёт сформирован |
| `import_completed` | Импорт завершён |

Каждый запрос подписывается HMAC-SHA256. Проверка подписи на стороне получателя:
```python
import hmac, hashlib

def verify(secret: str, body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Задачи — `/api/v1/tasks`

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/tasks/{task_id}` | Статус Celery задачи |

### Health check

```
GET /api/v1/health
→ {"status": "ok", "database": "ok"}
```

## Celery задачи

| Задача | Тип | Описание |
|--------|-----|----------|
| `aggregate_products_batch` | По запросу | Массовая агрегация продуктов |
| `generate_batch_report` | По запросу | Генерация Excel / PDF отчёта |
| `export_batches_to_file` | По запросу | Экспорт заданий |
| `import_batches_from_file` | По запросу | Импорт из Excel |
| `send_webhook_delivery` | По запросу | Доставка вебхука с ретраями |
| `auto_close_batches` | Каждые 5 мин | Автозакрытие просроченных заданий |

## Тесты

```bash
# Создать тестовую БД (один раз)
PGPASSWORD=postgres psql -U postgres -h localhost -c "CREATE DATABASE product_control_test;"

# Запустить все тесты
uv run pytest -v
```

**35 тестов**: 12 юнит (HMAC, JWT, пароли) + 23 интеграционных (auth, batches, products, webhooks).

## Структура проекта

```
src/
├── api/v1/
│   ├── routers/       # FastAPI роутеры
│   └── schemas/       # Pydantic схемы
├── core/
│   ├── config.py      # Настройки (pydantic-settings)
│   ├── database.py    # SQLAlchemy engine + session
│   ├── dependencies.py# FastAPI Depends
│   └── exceptions.py  # Обработчики ошибок
├── data/
│   ├── models/        # SQLAlchemy модели
│   └── repositories/  # Слой доступа к данным
├── domain/
│   ├── services/      # Бизнес-логика
│   └── exceptions/    # Доменные исключения
├── tasks/             # Celery задачи
├── storage/           # MinIO клиент
└── utils/             # HMAC, JWT, PDF, Excel утилиты
```
