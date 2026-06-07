import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import Redis

from app.config import settings
from app.db import engine
from app.exceptions import register_exception_handlers
from app.routers import health, history, translate

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("app")


# Управление жизненным циклом контекстных переменных: lifespan инициализирует
# подключения к БД и Redis при старте и аккуратно закрывает их при остановке (Model-in-App style для внешних ресурсов)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup: checking database connection")
    async with engine.connect() as conn:
        await conn.run_sync(lambda _: None)

    logger.info("startup: checking redis connection")
    redis = Redis(host=settings.redis_host, port=settings.redis_port)
    await redis.ping()
    app.state.redis = redis

    logger.info("startup: complete")
    yield

    logger.info("shutdown: closing connections")
    await redis.aclose()
    await engine.dispose()
    logger.info("shutdown: complete")


app = FastAPI(
    title="LLM Translation Service",
    description="Сервис перевода текста на базе Qwen3.5-0.8B через vLLM (CPU)",
    version="0.1.0",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(translate.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# Метрики: Prometheus-инструментация, эндпоинт /metrics для скрейпа
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
