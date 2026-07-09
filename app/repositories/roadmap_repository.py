from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap
from app.models.roadmap_task import RoadmapTask


class RoadmapRepository:
    """
    Repository responsible for roadmap database operations.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session


    async def create(
        self,
        roadmap: Roadmap,
    ) -> Roadmap:
        """
        Persist a roadmap and all nested tasks/subtasks.

        SQLAlchemy cascade relationships handle nested persistence.
        """

        self.session.add(roadmap)

        try:
            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        await self.session.refresh(roadmap)

        return roadmap


    async def get_by_id(
        self,
        roadmap_id: UUID,
    ) -> Roadmap | None:
        """
        Retrieve a roadmap with its ordered tasks and subtasks.
        """

        statement = (
            select(Roadmap)
            .where(
                Roadmap.id == roadmap_id
            )
            .options(
                selectinload(Roadmap.tasks)
                .selectinload(RoadmapTask.subtasks)
            )
        )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()