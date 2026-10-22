# TaskHub API

A hands-on FastAPI project following the roadmap through section 3, covering setup, basic CRUD, SQLAlchemy relationships, and nested queries. SQLite is used by default; PostgreSQL and MySQL can be enabled with optional drivers and `DATABASE_URL`.

## Run on Windows

Requires Python 3.12 or 3.13 (the commands below use Python 3.12).

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

Note: `requirements.lock` currently includes both the PostgreSQL (`psycopg`) and MySQL (`PyMySQL`) drivers, so the installation commands above install both even though SQLite remains the default database. To install only the core dependencies for SQLite, replace the two package installation commands above with:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

To install either the PostgreSQL or MySQL driver defined in `pyproject.toml`, use `python -m pip install -e ".[postgres]"` or `python -m pip install -e ".[mysql]"` instead of the package installation commands above.

## Database

The application reads `DATABASE_URL` from an environment variable or `.env`. PostgreSQL example:

```dotenv
DATABASE_URL=postgresql+psycopg://taskhub:password@localhost:5432/taskhub
```

MySQL example:

```dotenv
DATABASE_URL=mysql+pymysql://taskhub:password@localhost:3306/taskhub
```

Do not put real credentials in `.env.example` or Git. For each schema change, create a migration with `alembic revision --autogenerate -m "describe-change"`, review the migration, and then run `alembic upgrade head`.

## API scope: sections 1–3

- `POST /api/users` creates a user; `GET /api/users/{username}/profile` returns the profile and project list.
- `GET /api/projects`, `POST /api/projects`, `GET /api/projects/{project_id}`, `PATCH /api/projects/{project_id}`, `DELETE /api/projects/{project_id}`.
- `GET /api/projects/{project_id}/tasks`, `POST /api/projects/{project_id}/tasks`.
- `GET /api/tags`, `POST /api/tags`.

Create a user first, then create a project with `owner_id`; create tags first if you want to attach `tag_ids` to a task. Request and response details are available at `/docs`.

The current API scope does not include endpoints for comments or authentication.

## Project structure

- `app/models/`: SQLAlchemy models and the Task–Tag association table.
- `app/schemas/`: Pydantic request/response models.
- `app/crud/`: data operations and eager-loading queries.
- `app/api/routes/`: FastAPI routers.
- `app/db/` and `migrations/`: engine, session dependency, and Alembic.
- `docs/`: roadmap, architecture, conventions, and changelog.
