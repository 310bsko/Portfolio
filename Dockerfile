# Repli (Render, Oracle Cloud…) si Vercel ne convient plus. Non utilisé par Vercel.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev && uv pip install gunicorn

COPY . .
RUN SECRET_KEY=construction uv run --no-sync python manage.py collectstatic --noinput

RUN useradd --create-home application && chown -R application /app
USER application

EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync python manage.py migrate --noinput && uv run --no-sync python manage.py createcachetable && uv run --no-sync gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2"]
