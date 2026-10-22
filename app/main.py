from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.router import api_router

app = FastAPI(
    title="TaskHub API",
    description="REST API thực hành FastAPI, SQLAlchemy và quan hệ dữ liệu.",
    version="0.1.0",
)
register_exception_handlers(app)
app.include_router(api_router)
