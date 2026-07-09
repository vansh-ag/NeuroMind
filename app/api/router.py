from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.project import router as project_router
from app.api.routes.roadmap import router as roadmap_router


api_router = APIRouter()


api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)


api_router.include_router(
    roadmap_router,
    prefix="/roadmaps",
    tags=["Roadmaps"],
)


api_router.include_router(
    project_router,
    prefix="/projects",
    tags=["Projects"],
)


api_router.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"],
)