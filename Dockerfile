FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////var/lib/taskhub/taskhub.db

WORKDIR /app

RUN adduser --disabled-password --gecos "" --uid 10001 taskhub \
    && mkdir -p /var/lib/taskhub \
    && chown taskhub:taskhub /var/lib/taskhub

COPY pyproject.toml README.md ./
COPY alembic.ini ./
COPY app ./app
COPY migrations ./migrations

RUN python -m pip install --no-cache-dir --timeout 120 --retries 5 ".[postgres]"

USER taskhub

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
