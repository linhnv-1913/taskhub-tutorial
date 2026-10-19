from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(
    title="TaskHub API",
    description="REST API thực hành FastAPI, SQLAlchemy và quan hệ dữ liệu.",
    version="0.1.0",
)
app.include_router(api_router)
