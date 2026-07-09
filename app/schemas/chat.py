from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class ChatRequest(BaseModel):
    """
    Request schema for roadmap-grounded chat.
    """

    roadmap_id: UUID

    message: str = Field(
        ...,
        min_length=2,
        max_length=2000,
    )


class LLMChatResponse(BaseModel):
    """
    Lightweight schema used for Gemini structured output.
    """

    response: str

    follow_up_questions: list[str]


class ChatResponse(BaseModel):
    """
    Strict public API response schema.
    """

    response: str = Field(
        ...,
        min_length=1,
        max_length=5000,
    )

    follow_up_questions: list[str] = Field(
        default_factory=list,
        max_length=3,
    )