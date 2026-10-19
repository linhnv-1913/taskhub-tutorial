# Development Roadmap

## Current milestone: TaskHub API foundation

| Roadmap section | Status | Delivered scope |
|---|---|---|
| 1. Setup môi trường – FastAPI & SQLAlchemy | Complete | Python 3.12 venv, FastAPI/Uvicorn, SQLAlchemy, dotenv, Alembic, SQLite default, PostgreSQL/MySQL drivers |
| 2. CRUD cơ bản – SQLAlchemy, Pydantic & APIRouter | Complete | Create/read/update/delete projects, create users/tags, list projects and tags, OpenAPI schemas |
| 3. Quan hệ Model & tối ưu truy vấn | Complete | User/Project/Task/Comment/Tag relations, Task–Tag many-to-many, nested responses, eager loading |
| 4. JWT & OAuth2 | Not started | Outside this implementation scope |
| 5. Permissions, filtering, pagination | Not started | Outside this implementation scope |
| 6. Complex business logic & transactions | Not started | Outside this implementation scope |
| 7. Testing, background tasks & caching | Not started | Outside this implementation scope |
| 8. Final review and deployment | Not started | Outside this implementation scope |

## Next milestone

Implement authentication and authorization only after the corresponding roadmap scope is approved.
