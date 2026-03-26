"""# 🚗 Avto Search Bot

AI-powered чатбот для поиска автомобильных объявлений с использованием RAG (Retrieval-Augmented Generation).

## 📋 Описание

Сервис позволяет искать автомобили на естественном языке. Пользователь пишет запрос в чат («найди Toyota Camry до миллиона»), а система:
1. Проверяет релевантность запроса (moderation)
2. Ищет подходящие объявления через векторный и SQL поиск
3. Формирует человекочитаемый ответ
4. Реализован простой сервис на FastApi

## 🏗️ Архитектура
```
src/
├── api/                         FastAPI: роутеры, схемы, зависимости
│   ├── routers/
│   │   ├── chat.py              POST /api/v1/chat — основной эндпоинт
│   │   ├── avto.py              GET /api/v1/avto — список объявлений
│   │   └── health.py            GET /health, /health/db — мониторинг
│   └── schemas.py               Pydantic модели запросов/ответов
├── application/
│   ├── agents/                  LangGraph агенты
│   │   ├── query_agent.py       Переформулирует вопрос пользователя
│   │   ├── reranker_agent.py    Проверяет релевантность ответа
│   │   ├── moderation_agent.py  Проверяет релевантность запроса
│   │   ├── rag_agent.py         Векторный + SQL поиск
│   │   ├── sql_agent.py         Генерация SQL запросов
│   │   └── writer_agent.py      Формирует финальный ответ
│   ├── tools/
│   │   ├── vector_search.py     Семантический поиск по эмбеддингам
│   │   └── sql_search_tool.py   Точный поиск через SQL
│   └── workflows/
│       ├── chat_graph.py        LangGraph граф агентов
│       └── state.py             Общий стейт графа
├── infrastructure/
│   ├── db/
│   │   ├── models.py            SQLAlchemy модели
│   │   ├── session.py           Подключение к PostgreSQL
│   │   ├── vector_repository_impl.py  Векторный поиск через pgvector
│   │   └── chat_repository_impl.py    Сохранение истории чатов
│   └── llm/
│       ├── provider_factory.py  Фабрика LLM (Google / OpenAI / Ollama)
│       └── embeddings.py        Фабрика эмбеддингов
├── ingestion/
│   ├── ingestion_runner.py      CLI для загрузки данных
│   └── embedding_pipeline.py   Генерация эмбеддингов и запись в БД
├── config/
│   └── settings.py              Конфигурация через .env
└── prompts/
    ├── rag.txt                  Промпт для RAG агента
    └── moderation.txt           Промпт для модерации
```
## Схема работы запроса
```
User → POST /api/v1/chat
         ↓
    [moderation_agent]  — релевантен ли запрос?
         ↓ да           ↓ нет → Response { error: "out of scope" }
    [query_agent]       - переписывает запрос для лучшего поиска
         ↓ да
    [rag_agent]         — векторный поиск + SQL поиск
         ↓ да
    [reranker_agent]    - переранжирует top-K → top-N (N << K)
         ↓
    [writer_agent]      — формирует ответ на основе найденных объявлений
         ↓
    Response { chat_id, answer, documents }
```
## 🛠️ Технологии

| Компонент            | Технология                  |
|----------------------|-----------------------------|
| API                  | FastAPI + Uvicorn           |
| LLM                  | Ollama - mistal             |
| Эмбеддинги           | Ollama - bge-m3             |
| Оркестрация агентов  | LangGraph                   |
| База данных          | PostgreSQL 16 + pgvector    |
| ORM                  | SQLAlchemy + SQLModel       |
| Контейнеризация      | Docker + Docker Compose     |
| Зависимости          | uv                          |

## ⚙️ Конфигурация

Создай файл .env в корне проекта:

    # .env
    # LLM
    LLM_PROVIDER=ollama
    LLM_MODEL=qwen2.5:7b-instruct-q6_K
    OLLAMA_BASE_URL=http://host.docker.internal:11434

    # Embeddings
    EMBEDDING_PROVIDER=ollama
    EMBEDDING_MODEL=bge-m3
    EMBEDDING_DIMENSIONS=1024

    # Database
    DB_HOST=db
    DB_PORT=5432
    DB_USER=postgres
    DB_PASSWORD=secret
    DB_NAME=avtobot

    # App
    APP_ENV=development
    # LOG_LEVEL=INFO
    LOG_LEVEL=DEBUG

## 🚀 Запуск

1. Клонируй репозиторий и создай .env

    git clone <repo_url>
    cd <project_dir>

2. Запусти контейнеры

    cd docker
    docker compose up -d --build

3. Загрузи данные

    docker compose exec app uv run python -m src.ingestion.ingestion_runner \
      --file data/train.csv \
      --limit 5000 \
      --only-cars

4. Проверь сервис

    curl http://localhost:8001/health
    curl http://localhost:8001/health/db

5. Swagger UI: http://localhost:8001/docs

## 💬 Использование API

Отправить сообщение:

    curl -X POST http://localhost:8001/api/v1/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "найди Toyota Camry до 1 миллиона"}'

Ответ:

    {
      "chat_id": 1,
      "answer": "Нашёл несколько подходящих вариантов...",
      "documents": [{"id": 42, "title": "Toyota Camry 2018", "score": 0.95}],
      "is_relevant": true
    }

## 🔧 Разработка

    docker compose down             # остановить (данные сохраняются)
    docker compose down -v          # полный сброс с данными
    docker compose up -d --build    # пересобрать после изменений
    docker compose logs app -f      # логи в реальном времени

## 🚧 Возможные улучшения

- Кэширование эмбеддингов — Redis для снижения расходов на API
- Фильтрация в векторном поиске — pre-filtering по городу/цене
- Стриминг ответов — StreamingResponse для отображения по мере генерации
- Авторизация — JWT токены для разграничения чатов по пользователям
- Метрики качества — оценка релевантности ответов через RAGAS
- Метрики качества - применение Langfuse
- Автоматический ingestion — Celery/APScheduler для обновления данных
"""
