import asyncio
import logging
import time
import uuid

from app.celery_app import celery_app
from app.db import async_session_factory
from app.ml_client import ml_service
from app.models import Translation

logger = logging.getLogger("translate_task")

# Celery выполняет задачи синхронно в воркер-процессе, а наш ML-клиент и ORM —
# асинхронные (httpx.AsyncClient, SQLAlchemy async engine с пулом соединений asyncpg).
# `asyncio.run()` создавал бы новый event loop на каждую задачу, но соединения из пула
# остаются привязанными к loop первого вызова — отсюда "Future attached to a different
# loop". Поэтому держим один постоянный loop на процесс воркера и переиспользуем его.
_worker_loop: asyncio.AbstractEventLoop | None = None


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
    return _worker_loop


async def _run_translation(
    text: str, source_lang: str, target_lang: str, creativity: float
) -> dict:
    t0 = time.perf_counter()

    # Логирование: фиксируем время каждого этапа обработки
    translated, detected_lang = await ml_service.translate(text, source_lang, target_lang, creativity)
    t1 = time.perf_counter()
    logger.info("stage.ml_inference", extra={"elapsed_ms": round((t1 - t0) * 1000, 1), "detected_lang": detected_lang})

    # Автоопределение языка: если был выбран "auto", в историю и в ответ записываем
    # фактический язык, распознанный моделью (если распознать не удалось — оставляем "auto")
    actual_source_lang = detected_lang if source_lang == "auto" and detected_lang else source_lang

    async with async_session_factory() as session:
        row = Translation(
            id=uuid.uuid4(),
            source_text=text,
            translated_text=translated,
            source_lang=actual_source_lang,
            target_lang=target_lang,
            creativity=creativity,
        )
        session.add(row)
        await session.commit()
    t2 = time.perf_counter()
    logger.info("stage.db_persist", extra={"elapsed_ms": round((t2 - t1) * 1000, 1)})

    logger.info("stage.total", extra={"elapsed_ms": round((t2 - t0) * 1000, 1)})
    return {
        "source_text": text,
        "translated_text": translated,
        "source_lang": actual_source_lang,
        "target_lang": target_lang,
        "creativity": creativity,
    }


@celery_app.task(name="translate_task", bind=True)
def translate_task(self, text: str, source_lang: str, target_lang: str, creativity: float) -> dict:
    received_at = time.perf_counter()
    logger.info("stage.received", extra={"task_id": self.request.id})
    loop = _get_worker_loop()
    result = loop.run_until_complete(_run_translation(text, source_lang, target_lang, creativity))
    logger.info(
        "stage.done",
        extra={"task_id": self.request.id, "elapsed_ms": round((time.perf_counter() - received_at) * 1000, 1)},
    )
    return result
