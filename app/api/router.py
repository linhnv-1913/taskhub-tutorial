from fastapi import APIRouter

from app.api.routes.projects import router as projects_router
from app.api.routes.tags import router as tags_router
from app.api.routes.tasks import collection_router as tasks_collection_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.users import router as users_router

api_router = APIRouter(prefix="/api")
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks_router, prefix="/projects/{project_id}/tasks", tags=["tasks"])
api_router.include_router(tasks_collection_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(tags_router, prefix="/tags", tags=["tags"])
