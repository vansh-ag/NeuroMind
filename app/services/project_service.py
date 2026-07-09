from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import gemini_client
from app.core.exceptions import RoadmapNotFoundError
from app.repositories.roadmap_repository import (
    RoadmapRepository,
)
from app.schemas.project import (
    ProjectRequest,
    ProjectResponse,
)


class ProjectService:
    """
    Service responsible for project recommendation workflow.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.roadmap_repository = RoadmapRepository(
            session=session
        )

    async def recommend_project(
        self,
        request: ProjectRequest,
    ) -> ProjectResponse:
        """
        Recommend a project using either a stored roadmap
        or directly supplied goal and skills.
        """

        if request.roadmap_id is not None:
            roadmap = await self.roadmap_repository.get_by_id(
                roadmap_id=request.roadmap_id
            )

            if roadmap is None:
                raise RoadmapNotFoundError(
                    roadmap_id=str(request.roadmap_id)
                )

            goal_title = roadmap.goal_title
            skills = roadmap.skills

        else:
            goal_title = request.goal_title
            skills = request.skills

        recommendation = (
            await gemini_client.generate_project_recommendation(
                goal_title=goal_title,
                skills=skills,
            )
        )

        return ProjectResponse(
            **recommendation.model_dump()
        )