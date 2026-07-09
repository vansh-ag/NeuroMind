from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter()


@router.get(
    "",
    summary="Check API health",
    description="Returns the current health status of the API.",
)
async def health_check():
    """
    Health check endpoint.

    Used to verify that the API service is running.
    """

    return {
        "status": "healthy",
        "service": "AI Learning Assistant API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }