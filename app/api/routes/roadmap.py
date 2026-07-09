from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.roadmap import (
    RoadmapRequest,
    RoadmapResponse,
)
from app.services.roadmap_service import RoadmapService


router = APIRouter()


@router.post(
    "",
    response_model=RoadmapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a personalized learning roadmap",
)
async def generate_roadmap(
    payload: RoadmapRequest,
    session: AsyncSession = Depends(get_db),
) -> RoadmapResponse:
    """
    Generate and persist a personalized learning roadmap.
    """

    service = RoadmapService(
        session=session
    )

    return await service.generate_roadmap(
        request=payload
    )


@router.get(
    "/{roadmap_id}",
    response_model=RoadmapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a roadmap by ID",
)
async def get_roadmap(
    roadmap_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> RoadmapResponse:
    """
    Retrieve an existing roadmap.
    """

    service = RoadmapService(
        session=session
    )

    return await service.get_roadmap(
        roadmap_id=roadmap_id
    )