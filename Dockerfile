FROM python:3.9

WORKDIR /app

RUN pip install uv

# Node.jsとnpmをインストール（Tailwind CSS用）
RUN apt-get update && apt-get install -y nodejs npm

COPY uv.lock pyproject.toml ./

RUN uv sync

COPY . .

# Tailwind CSSをインストール
RUN uv run python manage.py tailwind install
RUN sync

# 本番用CSSをビルド
RUN uv run python manage.py tailwind build

# 静的ファイルを収集
RUN uv run python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]