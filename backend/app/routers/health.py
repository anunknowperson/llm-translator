import httpx
from fastapi import APIRouter, Response, status
from redis.asyncio import Redis
from sqlalchemy import text

from app.config import settings
from app.db import async_session_factory
from app.schemas import HealthComponent, HealthResponse

router = APIRouter(tags=["health"])


# API Health Check: проверяет не только живость процесса, но и доступность БД, Redis и готовность ML-модели
@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response) -> HealthResponse:
    components: list[HealthComponent] = []

    # Postgres
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        components.append(HealthComponent(name="postgres", status="ok"))
    except Exception as exc:
        components.append(HealthComponent(name="postgres", status="error", detail=str(exc)))

    # Redis
    try:
        redis = Redis(host=settings.redis_host, port=settings.redis_port)
        await redis.ping()
        await redis.aclose()
        components.append(HealthComponent(name="redis", status="ok"))
    except Exception as exc:
        components.append(HealthComponent(name="redis", status="error", detail=str(exc)))

    # vLLM
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.vllm_base_url}/models")
            r.raise_for_status()
        components.append(HealthComponent(name="vllm", status="ok"))
    except Exception as exc:
        components.append(HealthComponent(name="vllm", status="error", detail=str(exc)))

    overall_ok = all(c.status == "ok" for c in components)
    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(status="ok" if overall_ok else "degraded", components=components)
