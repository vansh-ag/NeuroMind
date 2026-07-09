from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.indexer import roadmap_indexer
from app.ai.client import gemini_client
from app.core.exceptions import RoadmapNotFoundError
from app.models.roadmap import Roadmap
from app.models.roadmap_subtask import RoadmapSubtask
from app.models.roadmap_task import RoadmapTask
from app.repositories.roadmap_repository import (
    RoadmapRepository,
)
from app.schemas.roadmap import (
    GeneratedRoadmap,
    RoadmapRequest,
    RoadmapResponse,
    RoadmapSubtaskResponse,
    RoadmapTaskResponse,
)


class RoadmapService:
    """
    Service responsible for roadmap business workflows.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.repository = RoadmapRepository(
            session=session
        )


    async def generate_roadmap(
        self,
        request: RoadmapRequest,
    ) -> RoadmapResponse:
        """
        Generate, persist, and return a personalized roadmap.
        """

        generated = await gemini_client.generate_roadmap(
            request=request
        )

        roadmap_model = self._build_roadmap_model(
            request=request,
            generated=generated,
        )

        saved_roadmap = await self.repository.create(
            roadmap=roadmap_model
        )

        await roadmap_indexer.index(
            roadmap=saved_roadmap
        )

        return self._to_response(
            saved_roadmap
        )


    async def get_roadmap(
        self,
        roadmap_id: UUID,
    ) -> RoadmapResponse:
        """
        Retrieve a persisted roadmap.
        """

        roadmap = await self.repository.get_by_id(
            roadmap_id=roadmap_id
        )

        if roadmap is None:
            raise RoadmapNotFoundError(
                roadmap_id=str(roadmap_id)
            )

        return self._to_response(
            roadmap
        )


    @staticmethod
    def _build_roadmap_model(
        request: RoadmapRequest,
        generated: GeneratedRoadmap,
    ) -> Roadmap:
        """
        Convert validated request and LLM output into ORM objects.
        """

        roadmap = Roadmap(
            goal_title=request.goal_title,
            experience=request.experience.value,
            known_skills=request.known_skills,
            learning_style=request.learning_style.value,
            weekly_hours=request.weekly_hours,
            estimated_hours=generated.estimated_hours,
            skills=generated.skills,
        )

        for task_index, generated_task in enumerate(
            generated.tasks,
            start=1,
        ):
            task = RoadmapTask(
                title=generated_task.title,
                description=generated_task.description,
                estimated_hours=generated_task.estimated_hours,
                sequence_order=task_index,
            )

            for subtask_index, generated_subtask in enumerate(
                generated_task.subtasks,
                start=1,
            ):
                subtask = RoadmapSubtask(
                    title=generated_subtask.title,
                    sequence_order=subtask_index,
                )

                task.subtasks.append(
                    subtask
                )

            roadmap.tasks.append(
                task
            )

        return roadmap


    @staticmethod
    def _to_response(
        roadmap: Roadmap,
    ) -> RoadmapResponse:
        """
        Convert ORM model into the public API response schema.
        """

        return RoadmapResponse(
            roadmap_id=roadmap.id,
            estimated_hours=roadmap.estimated_hours,
            skills=roadmap.skills,
            tasks=[
                RoadmapTaskResponse(
                    title=task.title,
                    description=task.description,
                    estimated_hours=task.estimated_hours,
                    subtasks=[
                        RoadmapSubtaskResponse(
                            title=subtask.title
                        )
                        for subtask in task.subtasks
                    ],
                )
                for task in roadmap.tasks
            ],
        )