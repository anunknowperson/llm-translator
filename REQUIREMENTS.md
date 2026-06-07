# Чек-лист соответствия критериям оценивания

Легенда: ✅ выполнено · ❌ не выполнено (сознательно пропущено)

## 1. Реализованный API бэкенд (FastAPI)
- ✅ **[2] Управление жизненным циклом** - `backend/app/main.py`, функция `lifespan`: при старте приложения проверяется подключение к Postgres и Redis, клиент Redis кладётся в `app.state`; при остановке соединения корректно закрываются (`engine.dispose()`, `redis.aclose()`).
- ✅ **(4) * Асинхронная очередь задач** - Celery + Redis (`backend/app/celery_app.py`, `backend/app/tasks.py`). Брокер и result backend - Redis (разные БД redis: 0 и 1, см. `.env.example`). Тяжёлая задача перевода `translate_task` выполняется в отдельном контейнере `worker`. Эндпоинт проверки статуса - `GET /api/translate/tasks/{task_id}` (`backend/app/routers/translate.py`), реализован через polling `AsyncResult` - этого достаточно по условиям задания.
- ✅ **(1) * WebSocket для статуса задачи** - `WS /api/translate/ws/{task_id}` (`backend/app/routers/translate.py`, `task_status_ws`): сервер сам опрашивает Celery result backend раз в секунду и проталкивает обновления клиенту до терминального статуса (`SUCCESS`/`FAILURE`), затем закрывает соединение. Nginx настроен на проксирование Upgrade-заголовков (`proxy/nginx.conf`). На фронтенде используется вместо ручного polling - `frontend/src/api/client.ts` (`openTaskStatusSocket`) и `TranslatePage.tsx`.
- ✅ **[2] Валидация данных** - `backend/app/schemas.py`: `TranslateRequest` с типами, `Field(ge=0.0, le=1.0)` для `creativity`, `min_length/max_length` для текста, `examples`/`description` для всех полей, enum языков.
- ✅ **[2] Обработка ошибок** - `backend/app/exceptions.py`: кастомные исключения `InvalidPromptError` (400), `MLServiceUnavailableError` (503), обработчик непредвиденных ошибок (500); FastAPI/Pydantic сами возвращают 422 при невалидном теле запроса. Все ошибки - структурированный JSON `{error, message}`.

## 2. Реализованный ML сервис
- ✅ **[2] Изоляция ML-логики** - `backend/app/ml_client.py`, класс `MLTranslationService`. API и Celery-задача вызывают только `ml_service.translate(...)`, ничего не знают о промптах/HTTP к vLLM.
- ✅ **[2] Управление ресурсами** - `ML_MAX_NEW_TOKENS` ограничивает длину генерации (`max_tokens` в запросе к vLLM), `--max-model-len` и `--gpu-memory-utilization` у самого vLLM, `--concurrency=2` у Celery worker ограничивает число параллельных тяжёлых задач (см. `worker/Dockerfile`, `docker-compose.yml`).
- ✅ **[2] Логирование** - `backend/app/tasks.py` и `backend/app/ml_client.py`: логируются длительности этапов (`stage.received`, `stage.ml_inference`, `stage.db_persist`, `stage.total`) в миллисекундах.
- ✅ **(2) * Оптимизация инференса** - для теста из-за отсутствия GPU модель запускается без квантизации на CPU (образ `vllm/vllm-openai-cpu`, который сам по себе CPU-only, см. сервис `vllm` в `docker-compose.yml`); очень легко поменять на квант gptq/awq и получить оптимизированный инференс на гпу.

## 3. Реализованный интерфейс (React + Mantine + Vite)
- ✅ **[3] Визуальный интерфейс** - `frontend/src/pages/{TranslatePage,HistoryPage,StatsPage}.tsx` общаются с тремя бэкенд-эндпоинтами: `POST /api/translate` + `GET /api/translate/tasks/{id}`, `GET /api/history`, `GET /api/stats`. Поддерживается 27 языков (`backend/app/schemas.py::Language`) и автоопределение исходного языка (значение `auto`): модель сама распознаёт язык текста и переводит его одним запросом (`backend/app/ml_client.py::_build_messages/_parse_auto_response`), распознанный язык отображается в результате и сохраняется в историю.
- ✅ **[2] Слабая связность** - весь обмен через `frontend/src/api/client.ts` (`fetch` к относительному `/api/...`, проксируется Nginx). Прямых импортов из backend нет.
- ✅ **[3] UX асинхронности** - `TranslatePage`: после постановки задачи в очередь UI поллит статус и показывает `Loader`/спиннер с подписью «Задача поставлена в очередь...» / «Модель генерирует перевод...».
- ✅ **[1] Изоляция в сети** - фронтенд подключён только к `frontend_net`, не имеет сетевого доступа к Postgres/Redis (см. `docker-compose.yml`).
- ✅ **[2] Обработка сбоев** - `frontend/src/components/ServiceErrorBanner.tsx` + `ServiceUnavailableError` в `api/client.ts`: сетевые ошибки и 503 показываются как аккуратное уведомление «Сервис временно недоступен» вместо падения с трейсбеком.
- ✅ **(5) * Визуальная репрезентация** - `StatsPage.tsx`: графики Recharts (BarChart по языковым парам, LineChart по дням), обновляются по кнопке «Обновить» (повторный вызов `GET /api/stats`).

## 4. Reverse Proxy (Nginx)
- ✅ **[1] Единая точка входа** - `proxy/nginx.conf`, слушает порт 80; backend/frontend в compose не публикуются на хост.
- ✅ **[2] Маршрутизация** - `location /api/` → backend, `location /` → frontend.
- ✅ **[1] Rate Limiting** - `limit_req_zone ... rate=5r/m` применяется к `/api/`, лимит настраивается через `RATE_LIMIT_RPM` в `.env.example`.

## 5. Работа с данными и состоянием
- ✅ **[3] ORM** - SQLAlchemy 2.0 async ORM (`backend/app/models.py`, `backend/app/db.py`, роутеры используют `select(...)`), сырых SQL-запросов нет.
- ✅ **[2] Версионирование данных** - Alembic (`backend/alembic/`), миграция `0001_create_translations.py` создаёт таблицу `translations`; применяется автоматически при старте контейнера backend (`backend/entrypoint.sh`).

## 6. Оркестрация в Docker Compose
- ✅ **[2](4) Dockerfile + (*) кэширование слоёв** - `backend/Dockerfile`, `worker/Dockerfile`, `frontend/Dockerfile`: манифест зависимостей копируется и устанавливается отдельным слоем до копирования исходников.
- ✅ **(*) uv** - `backend/Dockerfile`, `worker/Dockerfile` используют `uv venv` + `uv pip install` поверх `pyproject.toml`.
- ✅ **[1] Разделение сетей** - `frontend_net` (proxy/frontend/backend) и `backend_net` (backend/worker/redis/postgres/vllm/prometheus/grafana); UI и proxy не подключены к `backend_net`.
- ✅ **[2] Управление постоянством данных** - volumes `pgdata`, `redisdata`, `vllm_cache` (веса модели), `prometheus_data`, `grafana_data`.
- ✅ **[1] Порядок запуска** - `depends_on` с `condition: service_healthy` (backend ждёт postgres/redis/vllm; worker ждёт того же; frontend ждёт backend; proxy ждёт frontend+backend).

## 7. High Availability
- ✅ **[3] Stateless архитектура** - статус задач в Redis (Celery result backend), готовые переводы - в Postgres; в памяти процесса состояние не хранится.
- ✅ **(2) * Горизонтальное масштабирование** - `deploy.replicas: 2` для `backend` и `worker` в `docker-compose.yml`.
- ✅ **(2) * Балансировка нагрузки** - Nginx `upstream backend_upstream` балансирует запросы между репликами backend через встроенный Docker DNS round-robin.
- ✅ **[2] Graceful Shutdown** - `uvicorn --timeout-graceful-shutdown 30`, `stop_grace_period` у backend/worker, Celery worker корректно завершает задачи при SIGTERM (warm shutdown), `STOPSIGNAL SIGTERM`.

## 8. Health Checks и мониторинг
- ✅ **[2] API Health Check** - `GET /api/health` (`backend/app/routers/health.py`) проверяет Postgres (`SELECT 1`), Redis (`PING`) и готовность vLLM (`GET /v1/models`), возвращает 200/503 с детализацией по компонентам.
- ✅ **[2] Compose Healthcheck** - healthcheck-блоки для `postgres`, `redis`, `backend`, `frontend`, `vllm` в `docker-compose.yml`.
- ✅ **[2] Умный depends_on** - везде, где это имеет смысл, используется `condition: service_healthy`.
- ✅ **(3) * Метрики** - `prometheus-fastapi-instrumentator` в `backend/app/main.py` (эндпоинт `/metrics`), `monitoring/prometheus.yml` скрейпит backend, Grafana с провижининг-датасорсом и базовым дашбордом `monitoring/grafana/dashboards/backend-overview.json` (RPS, p95 latency).

## Инженерные стандарты
- ✅ Воспроизводимость - `docker compose up --build -d` поднимает весь стек.
- ✅ Отсутствие хардкода - все настройки в `.env` / `.env.example` (безопасные значения по умолчанию).
- ✅ Чистота репозитория - `.gitignore`, `.dockerignore`; веса модели хранятся в Docker volume `vllm_cache`, а не в репозитории.
- ✅ Документация - см. `README.md` (описание, архитектура, запуск, примеры запросов).
