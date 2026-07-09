from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class ProjectRequest(BaseModel):
    """
    Request schema for project recommendation.

    Supports either:
    1. roadmap_id
    2. goal_title + skills
    """

    roadmap_id: UUID | None = None

    goal_title: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    skills: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    @model_validator(mode="after")
    def validate_input_mode(
        self,
    ) -> "ProjectRequest":
        has_roadmap = self.roadmap_id is not None

        has_direct_input = (
            self.goal_title is not None
            and self.skills is not None
        )

        if not has_roadmap and not has_direct_input:
            raise ValueError(
                "Provide either roadmap_id or both goal_title and skills."
            )

        if has_roadmap and has_direct_input:
            raise ValueError(
                "Provide either roadmap_id or goal_title with skills, not both."
            )

        return self


class LLMProjectRecommendation(BaseModel):
    """
    Lightweight structured output schema sent to Gemini.
    """

    title: str
    difficulty: str
    estimated_hours: int
    tech_stack: list[str]
    features: list[str]
    why_this_project: str


class ProjectRecommendation(BaseModel):
    """
    Strict application-level validation.
    """

    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
    )

    difficulty: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    estimated_hours: int = Field(
        ...,
        ge=1,
        le=500,
    )

    tech_stack: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
    )

    features: list[str] = Field(
        ...,
        min_length=2,
        max_length=20,
    )

    why_this_project: str = Field(
        ...,
        min_length=10,
        max_length=1000,
    )


class ProjectResponse(ProjectRecommendation):
    """
    Public API response.
    """

    pass