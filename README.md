# TaskHub API

A small REST API built with FastAPI and SQLAlchemy. SQLite is the local default; PostgreSQL and MySQL are available through optional drivers.

## Requirements

Python 3.12 or 3.13. The commands below use Python 3.12 on Windows.

## Run on Windows

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open [Swagger UI](http://127.0.0.1:8000/docs). SQLite creates `taskhub.db` in the project root after migrations run, regardless of the current working directory.

## Database configuration

The application reads `DATABASE_URL` from the environment or `.env`. Do not put real credentials in `.env.example` or Git. Schema changes should be made with reviewed Alembic migrations.
