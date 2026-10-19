# Code Standards

- Use Python 3.12+, type annotations, and SQLAlchemy 2.x mapped attributes.
- Keep persistence models in `app/models/`, API contracts in `app/schemas/`, route handlers in `app/api/routes/`, and database operations in `app/crud/`.
- Keep code files under 200 lines and use one focused module per model, schema area, or route group.
- Use a synchronous SQLAlchemy session per request. Commit writes explicitly and roll back after database errors.
- Use Pydantic request schemas to validate input and response schemas as explicit output allowlists.
- Eager-load ORM relationships required by nested responses; use `.unique()` when a query uses `joinedload` for a collection.
- Load local settings from `.env`; commit only `.env.example`, never local credentials or database files.
- Track schema changes with Alembic. Review generated migrations before applying them.
