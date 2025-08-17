# Базовый образ с Python
FROM python:3.11-slim

# Установка зависимостей системы
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /LaunchX

# Копируем зависимости
COPY requirements.txt .

RUN pip install fastapi gunicorn uvicorn Werkzeug SQLAlchemy pydantic[email] TgCrypto python-jose psycopg2 python-multipart aiogram python-dotenv dotenv httpx Pyrogram

# Установка зависимостей Python
RUN /bin/sh -c python3 -m pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Указываем переменные среды (если нужны, можно вынести в .env)
ENV PYTHONUNBUFFERED=1

# Запуск FastAPI приложения на порту 5050
CMD ["gunicorn", "main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:5050"]
