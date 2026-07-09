from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.project import (
    ProjectRequest,
    ProjectResponse,
)
from app.services.project_service import ProjectService


router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend a practical project",
)
async def recommend_project(
    payload: ProjectRequest,
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """
    Recommend a personalized project from either a roadmap
    or directly supplied goal and skills.
    """

    service = ProjectService(
        session=session
    )

    return await service.recommend_project(
        request=payload
    )