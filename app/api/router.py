"""All API endpoints in one place: each router's URL prefix and Swagger tag.

main.py adds settings.API_PREFIX ("/api") in front of everything here.
"""
from fastapi import APIRouter

from app.api.endpoints import ask, documents, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(ask.router, prefix="/ask", tags=["ask"])
