# TaskHub API

TaskHub is a learning project for building a REST API with FastAPI, Pydantic v2, SQLAlchemy 2.x, and Alembic. It includes CRUD operations, JWT authentication, role- and ownership-based authorization, task filtering, pagination, and bookmarks. SQLite is the default database; PostgreSQL and MySQL are available with their respective drivers.

## Run on Windows

Requires Python 3.12 or 3.13 (the commands below use Python 3.12).

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
if (-not (Select-String -Path .env -Pattern '^JWT_SECRET_KEY=.{64,}$' -Quiet)) {
    $random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $secretBytes = New-Object byte[] 32
    $random.GetBytes($secretBytes)
    $jwtSecret = [System.BitConverter]::ToString($secretBytes).Replace('-', '').ToLowerInvariant()
    $random.Dispose()
    Add-Content -Path .env -Value "JWT_SECRET_KEY=$jwtSecret"
    Remove-Variable jwtSecret
    Remove-Variable secretBytes
}
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

If `.env` already exists, keep its current settings and add `JWT_SECRET_KEY` only if it is missing. Never commit a real signing key. Access tokens expire after 15 minutes by default; `ACCESS_TOKEN_EXPIRE_MINUTES` can be set from 1 to 1440.

Open [Swagger UI](http://127.0.0.1:8000/docs). SQLite creates `taskhub.db` in the project root after migrations run, regardless of the current working directory.

`requirements.lock` includes both the PostgreSQL (`psycopg`) and MySQL (`PyMySQL`) drivers. To install only the core dependencies for SQLite, replace the two package installation commands above with:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

To install a database driver from `pyproject.toml`, use `python -m pip install -e ".[postgres]"` or `python -m pip install -e ".[mysql]"` instead of the package installation commands above.

## Authentication and authorization

- `POST /api/users/register` accepts `username`, `email`, `full_name`, and `password`; the password must be 12–128 characters and is stored as an Argon2id hash.
- `POST /api/users/login` accepts the form fields `username` (username or email) and `password`; the response contains `access_token` and `token_type=bearer`.
- Send the token in the `Authorization: Bearer <access_token>` header.
- `GET /api/users/me` returns the authenticated user's account. `PUT /api/users/me` replaces the current user's `username`, `email`, and `full_name`.
- `POST /api/users` remains as an alias hidden from OpenAPI for compatibility and also requires a password.
- New projects belong to the authenticated user. Only the project owner or an admin can update or delete a project, or create tasks in it.
- Only admins can create tags (`POST /api/tags`). Registration does not accept a role or active-state field. An operator can grant admin access to a verified user through a trusted database command, such as `UPDATE users SET role = 'ADMIN' WHERE id = <verified-user-id>;`. The API has no endpoint for self-escalating privileges.
- Existing users remain active after the migration but have no `password_hash`, so they cannot log in until an operator sets a password through a trusted process.

## Task endpoints

- `GET /api/tasks?status=TODO&priority=HIGH` filters by status and priority and returns results in stable ID order. Priorities are `LOW`, `MEDIUM`, and `HIGH`; the default is `MEDIUM`.
- `GET /api/projects/{project_id}/tasks?skip=10&limit=5` supports pagination; `skip` must be non-negative and `limit` must be from 1 to 100 (default 20).
- `POST /api/tasks/{task_id}/bookmark` requires an active authenticated user. The first request returns 201; repeated requests return 200. Each bookmark belongs to one user.

## Core CRUD endpoints

- `GET /api/users/{username}/profile` returns the profile and project list.
- Projects support `GET` and `POST /api/projects`, `GET`, `PATCH`, and `DELETE /api/projects/{project_id}`.
- Tasks support `GET` and `POST /api/projects/{project_id}/tasks`.
- Tags support `GET /api/tags` and `POST /api/tags`.

Project, task, and tag read endpoints are public. Project creation, project updates/deletions, task creation, and tag creation require the permissions described above.

## Database and project structure

The application reads `DATABASE_URL` and JWT settings from the environment or `.env`. Do not put real credentials in `.env.example` or Git. For each schema change, create a migration with `alembic revision --autogenerate -m "describe-change"`, review it, then apply it with `alembic upgrade head`.

PostgreSQL example:

```dotenv
DATABASE_URL=postgresql+psycopg://taskhub:password@localhost:5432/taskhub
```

MySQL example:

```dotenv
DATABASE_URL=mysql+pymysql://taskhub:password@localhost:3306/taskhub
```

- `app/models/`: SQLAlchemy models and association tables.
- `app/schemas/`: Pydantic request and response allowlists.
- `app/crud/`: database operations and queries.
- `app/api/routes/`: FastAPI routers and dependencies.
- `app/db/`, `migrations/`: database engine, sessions, and Alembic migrations.
