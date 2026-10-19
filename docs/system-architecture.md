# System Architecture

## Scope

TaskHub is a synchronous REST API built with FastAPI, Pydantic v2, SQLAlchemy 2.x, and Alembic. SQLite is the local default. `DATABASE_URL` can select PostgreSQL or MySQL through the matching SQLAlchemy driver.

## Request and data flow

1. `app/main.py` creates the FastAPI application and mounts the `/api` router.
2. Route modules validate request bodies with Pydantic schemas and receive a request-scoped SQLAlchemy `Session` dependency.
3. CRUD modules issue SQLAlchemy 2.x `select()` statements, commit writes, and eager-load relationships needed by response schemas.
4. Pydantic response models read ORM attributes and limit returned fields.
5. Alembic migrations create and evolve database tables from `Base.metadata`.

## Data relationships

- User owns projects, may be assigned tasks, and authors comments.
- Project belongs to one owner and contains tasks.
- Task belongs to one project, may have one assignee, contains comments, and may have many tags.
- Tag and Task are linked by the composite-primary-key `task_tags` association table.
- Comments reference both a task and an author.

## Query loading

Project collection reads use `selectinload` for nested task and tag collections. Project detail uses `joinedload` for project tasks and `selectinload` for task tags; SQLAlchemy results are de-duplicated with `.unique()` before serialization. User profile reads load projects explicitly.
