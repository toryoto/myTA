# ベースイメージ
FROM python:3.9-slim as base

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*
RUN pip install uv

# Python依存関係
COPY uv.lock pyproject.toml ./
RUN uv sync

COPY . .

# 開発環境
FROM base as development

EXPOSE 8000
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# 本番環境
FROM base as production

# ビルド時はsettings.pyで自動的に一時キーが生成される
RUN uv run python manage.py tailwind install
RUN uv run python manage.py tailwind build
RUN uv run python manage.py collectstatic --noinput

RUN adduser --disabled-password appuser
RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# 実行時はSecret Managerから DJANGO_SECRET_KEY が自動注入される
CMD ["uv", "run", "gunicorn", "project.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:$PORT", "--workers", "2"]