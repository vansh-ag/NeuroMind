from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================
# ENUMS
# ============================================================


class ExperienceLevel(str, Enum):
    BEGINNER = "Less than 1 year"
    INTERMEDIATE = "1-3 years"
    EXPERIENCED = "More than 3 years"


class LearningStyle(str, Enum):
    PROJECT_BASED = "Project Based"
    VIDEO_BASED = "Video Based"
    READING_BASED = "Reading Based"
    MIXED = "Mixed"


# ============================================================
# API REQUEST SCHEMA
# ============================================================


class RoadmapRequest(BaseModel):
    """
    Request schema received from the API user.
    """

    goal_title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        examples=["Backend Developer"],
    )

    experience: ExperienceLevel

    known_skills: list[str] = Field(
        default_factory=list,
        max_length=20,
        examples=[["Python", "SQL"]],
    )

    learning_style: LearningStyle

    weekly_hours: int = Field(
        ...,
        ge=1,
        le=80,
        examples=[15],
    )

    @field_validator("goal_title")
    @classmethod
    def validate_goal_title(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("goal_title cannot be empty")

        return cleaned_value

    @field_validator("known_skills")
    @classmethod
    def clean_known_skills(
        cls,
        skills: list[str],
    ) -> list[str]:

        cleaned_skills = []

        for skill in skills:
            cleaned_skill = skill.strip()

            if cleaned_skill:
                cleaned_skills.append(cleaned_skill)

        return list(dict.fromkeys(cleaned_skills))


# ============================================================
# SIMPLE GEMINI RESPONSE SCHEMA
# ============================================================


class LLMSubtask(BaseModel):
    """
    Lightweight schema sent to Gemini.
    """

    title: str


class LLMTask(BaseModel):
    """
    Lightweight task schema sent to Gemini.
    """

    title: str
    description: str
    estimated_hours: int
    subtasks: list[LLMSubtask]


class LLMRoadmap(BaseModel):
    """
    Lightweight structured-output schema used by Gemini.

    Keep this schema intentionally simple because complex nested
    constraints may be rejected by the provider.
    """

    estimated_hours: int
    skills: list[str]
    tasks: list[LLMTask]


# ============================================================
# STRICT APPLICATION VALIDATION SCHEMA
# ============================================================


class GeneratedSubtask(BaseModel):
    """
    Strict application-level validation for a generated subtask.
    """

    title: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )


class GeneratedTask(BaseModel):
    """
    Strict application-level validation for a generated roadmap task.
    """

    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
    )

    estimated_hours: int = Field(
        ...,
        ge=1,
        le=200,
    )

    subtasks: list[GeneratedSubtask] = Field(
        ...,
        min_length=1,
        max_length=10,
    )


class GeneratedRoadmap(BaseModel):
    """
    Strict validated roadmap used inside the application.
    """

    estimated_hours: int = Field(
        ...,
        ge=1,
        le=5000,
    )

    skills: list[str] = Field(
        ...,
        min_length=1,
        max_length=30,
    )

    tasks: list[GeneratedTask] = Field(
        ...,
        min_length=1,
        max_length=30,
    )


# ============================================================
# API RESPONSE SCHEMAS
# ============================================================


class RoadmapSubtaskResponse(BaseModel):
    title: str


class RoadmapTaskResponse(BaseModel):
    title: str
    description: str
    estimated_hours: int
    subtasks: list[RoadmapSubtaskResponse]


class RoadmapResponse(BaseModel):
    roadmap_id: UUID
    estimated_hours: int
    skills: list[str]
    tasks: list[RoadmapTaskResponse]