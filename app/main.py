from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging(settings.log_level)
app = FastAPI(
    title="TaskHub API",
    description="REST API thực hành FastAPI, SQLAlchemy và quan hệ dữ liệu.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
register_exception_handlers(app)
app.include_router(api_router)
