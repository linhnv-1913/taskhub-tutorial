# TaskHub API

TaskHub is a learning project for building a REST API with FastAPI, Pydantic v2, SQLAlchemy 2.x, and Alembic. It includes CRUD operations, JWT authentication, role- and ownership-based authorization, task filtering, pagination, bookmarks, assignment, and comments. Comment email notifications use an optional SMTP configuration. SQLite is the default database; PostgreSQL and MySQL are available with their respective drivers.

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

## CORS, logging, and Docker Compose

`CORS_ALLOWED_ORIGINS` is a JSON list of exact browser origins, for example `["http://localhost:3000"]`. Set `CORS_ALLOWED_ORIGINS=[]` or omit the variable when browser clients are not used; a blank value (`CORS_ALLOWED_ORIGINS=`) is invalid. Wildcard origins are rejected; bearer-token requests allow the `Authorization` and `Content-Type` headers without cookie credentials. Set `LOG_LEVEL` to `CRITICAL`, `ERROR`, `WARNING`, `INFO`, or `DEBUG`. Application logs use the console, and Uvicorn logs request access and unhandled server tracebacks.

To run the API with PostgreSQL in Docker Compose, create `.env` from `.env.example` if it does not exist; preserve an existing `.env` and add any missing values. Set a JWT secret and set `POSTGRES_PASSWORD` to a generated hexadecimal value. Generate a 64-character value with `python -c "import secrets; print(secrets.token_hex(32))"`. Set `CORS_ALLOWED_ORIGINS` in `.env` to the frontend's exact JSON origin list before starting the stack.

```powershell
docker compose up --build
```

Compose waits for PostgreSQL, applies Alembic migrations, then starts the API. The API is available on the host at `127.0.0.1:8000`; its database-backed readiness check is available at [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health). View API logs with `docker compose logs -f api`. Stop the services with `docker compose down`; the named PostgreSQL volume remains. The API port is bound to localhost for use behind a reverse proxy. A public deployment still needs its own TLS, secret management, and database backup setup.

To install the integration-test dependencies and run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest
```

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
- Registration is available only through `POST /api/users/register`. It does not accept a role or active-state field.
- New projects belong to the authenticated user. The project owner or an admin can update or delete a project and create tasks in it. The PM role does not grant access to projects owned by other users.
- Only admins can create tags (`POST /api/tags`). Roles are `MEMBER`, `PM`, and `ADMIN`. Operators can create administrators with the CLI below. The API has no endpoint for self-escalating privileges.
- Existing users remain active and are migrated to the `MEMBER` role, but have no `password_hash`; an operator must set a password through a trusted process before they can log in.

## Operator CLI

After applying migrations, create a new administrator without editing SQL:

```powershell
.\.venv\Scripts\python.exe -m app.cli create-admin --username admin --email admin@example.com
.\.venv\Scripts\python.exe -m app.cli seed --owner admin
```

On Linux/macOS, use `.venv/bin/python` instead. `create-admin` prompts for a hidden password and confirmation, applies the registration validation rules (12–128 password characters), and stores an Argon2id hash. Duplicate usernames or emails are rejected; existing accounts are never promoted or overwritten. `--full-name` is optional. `seed` requires an existing active owner and creates a `TaskHub demo` project with two assigned tasks. Repeating it fills missing demo records without duplicating them or resetting existing data. It does not create accounts or default passwords. Both commands use the configured `DATABASE_URL` and return a nonzero exit code on failure.

For the running Compose stack:

```powershell
docker compose exec api python -m app.cli create-admin --username admin --email admin@example.com
docker compose exec api python -m app.cli seed --owner admin
```

## Task endpoints

- `GET /api/tasks?status=IN_PROGRESS&priority=HIGH&skip=0&limit=20` filters by status and priority and returns `items` and the matching `total` in stable ID order. Statuses are `TODO`, `IN_PROGRESS`, and `DONE`. Priorities are `LOW`, `MEDIUM`, and `HIGH`; the default is `MEDIUM`.
- `GET /api/projects/{project_id}/tasks?skip=10&limit=5` returns `items` and the matching `total`; `skip` must be non-negative and `limit` must be from 1 to 100 (default 20).
- `GET /api/projects?skip=0&limit=20` and `GET /api/tags?skip=0&limit=20` use the same paginated response shape and bounds.
- `POST /api/tasks/{task_id}/bookmark` requires an active authenticated user. The first request returns 201; repeated requests return 200. Each bookmark belongs to one user.
- `DELETE /api/tasks/{task_id}/bookmark` removes the current user's bookmark and returns 204. It returns 404 if the task or bookmark does not exist.
- `POST /api/tasks/{task_id}/assign` accepts an `assignee_id`; only the project owner or an admin can assign or reassign a task. The assignee must be active.
- `GET /api/tasks/{task_id}/comments?skip=0&limit=20` returns comments in stable ID order with `items` and `total`; pagination bounds match other list endpoints.
- `POST /api/tasks/{task_id}/comments` accepts a nonblank `content` from any active user. The author ID comes from the bearer token.
- `PATCH /api/tasks/{task_id}/comments/{comment_id}` edits comment content. The author, an admin, or the project's owner may edit or delete a comment.
- `DELETE /api/tasks/{task_id}/comments/{comment_id}` deletes a comment and returns 204. A comment must belong to the task in the path.

Comment notifications go to the task assignee, or to the project owner when the task is unassigned. The commenter is not notified. SMTP delivery is best-effort and runs after the comment is committed; SMTP failures do not undo the comment.

Configure SMTP through `.env` when notifications are needed:

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_FROM_EMAIL=taskhub@example.com
SMTP_USERNAME=taskhub@example.com
SMTP_PASSWORD=replace-with-a-local-secret
SMTP_STARTTLS=true
SMTP_TIMEOUT_SECONDS=10
```

If `SMTP_HOST` or `SMTP_FROM_EMAIL` is missing, the API still saves comments and logs that email delivery is skipped. Keep SMTP credentials out of version control.

## Optional Redis tag cache

Set `REDIS_URL=redis://localhost:6379/0` to cache authenticated `GET /api/tags` responses separately for each page. `TAG_CACHE_TTL_SECONDS` defaults to 60 and accepts 1–3600 seconds. After a tag is created, cached pages are invalidated; Redis failures fall back to the database without preventing tag creation. A failed invalidation or a read concurrent with creation may temporarily return stale data until the TTL expires. Use a separate Redis database for each TaskHub environment.

Redis integration tests require an isolated Redis database. For example, set `TASKHUB_TEST_REDIS_URL=redis://localhost:6379/1` before running pytest; without it, those tests are skipped.

## Core CRUD endpoints

- `GET /api/users/{username}/profile` returns the profile and project list to an authenticated user.
- Projects support `GET` and `POST /api/projects`, `GET`, `PATCH`, and `DELETE /api/projects/{project_id}`.
- Tasks support `GET` and `POST /api/projects/{project_id}/tasks`.
- Tags support `GET /api/tags` and `POST /api/tags`.

Project, task, tag, and profile read endpoints require an active bearer token. Project, task, and tag lists are paginated with `items` and `total` fields. Project creation, project updates/deletions, task creation, and tag creation require the permissions described above.

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
