from fastapi import APIRouter

from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.connections import router as connections_router
from app.api.cookies import router as cookies_router
from app.api.history import router as history_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(cookies_router)
api_router.include_router(connections_router)
api_router.include_router(analysis_router)
api_router.include_router(history_router)
