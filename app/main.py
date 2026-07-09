import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.exception_handlers import (
    register_exception_handlers,
)
from app.core.logging import configure_logging


configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown.
    """

    logger.info(
        "application_starting",
        extra={
            "app_name": settings.app_name,
            "environment": settings.app_env,
        },
    )

    yield

    logger.info(
        "application_shutting_down",
        extra={
            "app_name": settings.app_name,
        },
    )


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered learning assistant that generates personalized "
        "learning roadmaps, recommends projects, and answers "
        "roadmap-based questions using Retrieval-Augmented Generation."
    ),
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)


register_exception_handlers(app)


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get(
    "/",
    tags=["Root"],
    summary="API root",
)
async def root():
    return {
        "name": settings.app_name,
        "message": "Welcome to NeuroMind API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }