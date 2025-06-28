FROM python:3.9-slim

WORKDIR /app

# Node.jsとnpmをインストール（Tailwind CSS用）
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY uv.lock pyproject.toml ./

RUN uv sync

COPY . .

# Tailwind CSSをインストール
RUN uv run python manage.py tailwind install

# データベースマイグレーション
RUN uv run python manage.py migrate

# 本番用CSSをビルド
RUN uv run python manage.py tailwind build

# 静的ファイルを収集
RUN uv run python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]