import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base, TimestampMixin


if TYPE_CHECKING:
    from app.models.roadmap_task import RoadmapTask


class Roadmap(TimestampMixin, Base):
    """
    Stores the user profile and generated roadmap metadata.
    """

    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    goal_title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    experience: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    known_skills: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    learning_style: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    weekly_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    estimated_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    skills: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    tasks: Mapped[list["RoadmapTask"]] = relationship(
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapTask.sequence_order",
        lazy="selectin",
    )