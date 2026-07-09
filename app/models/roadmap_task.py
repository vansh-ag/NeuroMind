import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.roadmap import Roadmap
    from app.models.roadmap_subtask import RoadmapSubtask


class RoadmapTask(Base):
    """
    Stores a major learning task belonging to a roadmap.
    """

    __tablename__ = "roadmap_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "roadmaps.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    estimated_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    roadmap: Mapped["Roadmap"] = relationship(
        back_populates="tasks",
    )

    subtasks: Mapped[list["RoadmapSubtask"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="RoadmapSubtask.sequence_order",
        lazy="selectin",
    )