FROM python:3.12-slim AS base

# (*) используется uv для управления зависимостями + (*) кэширование слоёв:
# сначала копируем только манифест зависимостей, чтобы слой с зависимостями
# переиспользовался, пока pyproject.toml не меняется
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY backend/pyproject.toml ./
RUN uv venv && uv pip install -r pyproject.toml

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./
COPY backend/entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["./entrypoint.sh"]
