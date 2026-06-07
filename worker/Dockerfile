FROM python:3.12-slim AS base

# (*) uv + (*) кэширование слоёв — манифест зависимостей копируется отдельным слоем
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml ./
RUN uv venv && uv pip install -r pyproject.toml

COPY backend/app ./app

ENV PATH="/app/.venv/bin:${PATH}"

# Graceful shutdown: Celery воркер перехватывает SIGTERM (warm shutdown) и
# завершает текущие задачи перед остановкой; --concurrency ограничивает параллелизм (управление ресурсами)
STOPSIGNAL SIGTERM
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
