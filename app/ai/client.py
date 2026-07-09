import logging

from google import genai
from google.genai import types
from google.genai.errors import ServerError
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.prompts.chat_prompt import (
    CHAT_SYSTEM_PROMPT,
    build_chat_prompt,
)
from app.ai.prompts.project_prompt import (
    PROJECT_SYSTEM_PROMPT,
    build_project_prompt,
)
from app.ai.prompts.roadmap_prompt import (
    ROADMAP_SYSTEM_PROMPT,
    build_roadmap_prompt,
)
from app.core.config import settings
from app.core.exceptions import (
    InvalidLLMResponseError,
    LLMGenerationError,
)
from app.schemas.chat import (
    ChatResponse,
    LLMChatResponse,
)
from app.schemas.project import (
    LLMProjectRecommendation,
    ProjectRecommendation,
)
from app.schemas.roadmap import (
    GeneratedRoadmap,
    LLMRoadmap,
    RoadmapRequest,
)


logger = logging.getLogger(__name__)


class TransientLLMError(Exception):
    """
    Internal exception for temporary Gemini failures.

    Examples:
    - temporary provider unavailability;
    - model overload;
    - transient server errors.

    These failures may succeed when retried.
    """


class GeminiClient:
    """
    Client responsible for communication with Gemini.

    Responsibilities:
    - Generate structured learning roadmaps.
    - Validate roadmap responses.
    - Correct malformed roadmap responses.
    - Generate project recommendations.
    - Generate roadmap-grounded chat responses.
    - Retry temporary Gemini server failures.
    """

    MAX_VALIDATION_ATTEMPTS = 2

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.gemini_model

    # ============================================================
    # ROADMAP GENERATION
    # ============================================================

    @retry(
        retry=retry_if_exception_type(
            TransientLLMError
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=2,
            max=8,
        ),
        reraise=True,
    )
    async def _generate_roadmap_content(
        self,
        *,
        prompt: str,
    ) -> str:
        """
        Call Gemini for roadmap generation.

        Temporary Gemini server failures are retried with
        exponential backoff.
        """

        try:
            response = (
                await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            ROADMAP_SYSTEM_PROMPT
                        ),
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema=LLMRoadmap,
                        temperature=0.3,
                    ),
                )
            )

        except ServerError as exc:
            logger.warning(
                "gemini_roadmap_temporary_error",
                extra={
                    "model": self.model,
                    "error": str(exc),
                },
            )

            raise TransientLLMError(
                "Gemini is temporarily unavailable."
            ) from exc

        except Exception as exc:
            logger.exception(
                "gemini_roadmap_request_failed",
                extra={
                    "model": self.model,
                    "error_type": (
                        type(exc).__name__
                    ),
                },
            )

            raise LLMGenerationError(
                "Failed to generate roadmap "
                "using the AI service."
            ) from exc

        if not response.text:
            logger.error(
                "gemini_roadmap_empty_response"
            )

            raise InvalidLLMResponseError(
                "The AI service returned an empty "
                "roadmap response."
            )

        return response.text

    @staticmethod
    def _build_roadmap_correction_prompt(
        *,
        original_prompt: str,
        invalid_response: str,
        validation_error: ValidationError,
    ) -> str:
        """
        Build a correction prompt from Pydantic
        validation errors.
        """

        error_messages: list[str] = []

        for error in validation_error.errors():
            location = ".".join(
                str(part)
                for part in error["loc"]
            )

            message = error["msg"]

            error_messages.append(
                f"- {location}: {message}"
            )

        formatted_errors = "\n".join(
            error_messages
        )

        return f"""
The previous roadmap response failed application validation.

ORIGINAL REQUEST:

{original_prompt}


VALIDATION ERRORS:

{formatted_errors}


PREVIOUS INVALID RESPONSE:

{invalid_response}


Generate the complete roadmap again.

Correction requirements:

- Fix every listed validation error.
- Preserve the original learning goal.
- Preserve learner personalization.
- Keep task titles concise.
- Keep subtask titles short and actionable.
- Do not put paragraphs inside subtask titles.
- Keep descriptions inside description fields.
- Return the complete roadmap.
- Do not return only corrected fields.
"""

    async def generate_roadmap(
        self,
        request: RoadmapRequest,
    ) -> GeneratedRoadmap:
        """
        Generate and validate a personalized roadmap.

        Flow:
        1. Generate structured roadmap.
        2. Validate with GeneratedRoadmap.
        3. If invalid, build correction prompt.
        4. Regenerate once.
        5. Return valid roadmap.
        """

        original_prompt = build_roadmap_prompt(
            request
        )

        current_prompt = original_prompt

        logger.info(
            "roadmap_generation_started",
            extra={
                "goal_title": request.goal_title,
                "model": self.model,
            },
        )

        for attempt in range(
            1,
            self.MAX_VALIDATION_ATTEMPTS + 1,
        ):
            try:
                response_text = (
                    await self._generate_roadmap_content(
                        prompt=current_prompt
                    )
                )

            except TransientLLMError as exc:
                logger.error(
                    "roadmap_generation_unavailable",
                    extra={
                        "goal_title": (
                            request.goal_title
                        ),
                    },
                )

                raise LLMGenerationError(
                    "The AI service is temporarily "
                    "unavailable. Please try again shortly."
                ) from exc

            try:
                roadmap = (
                    GeneratedRoadmap.model_validate_json(
                        response_text
                    )
                )

            except ValidationError as exc:
                logger.warning(
                    "roadmap_response_validation_failed",
                    extra={
                        "goal_title": (
                            request.goal_title
                        ),
                        "attempt": attempt,
                        "validation_error_count": (
                            exc.error_count()
                        ),
                    },
                )

                if (
                    attempt
                    >= self.MAX_VALIDATION_ATTEMPTS
                ):
                    raise InvalidLLMResponseError(
                        "The generated roadmap remained "
                        "invalid after the correction attempt."
                    ) from exc

                current_prompt = (
                    self._build_roadmap_correction_prompt(
                        original_prompt=(
                            original_prompt
                        ),
                        invalid_response=(
                            response_text
                        ),
                        validation_error=exc,
                    )
                )

                continue

            logger.info(
                "roadmap_generation_completed",
                extra={
                    "goal_title": request.goal_title,
                    "estimated_hours": (
                        roadmap.estimated_hours
                    ),
                    "task_count": len(
                        roadmap.tasks
                    ),
                    "skill_count": len(
                        roadmap.skills
                    ),
                    "validation_attempt": attempt,
                },
            )

            return roadmap

        raise InvalidLLMResponseError(
            "Unable to generate a valid roadmap."
        )

    # ============================================================
    # PROJECT RECOMMENDATION
    # ============================================================

    @retry(
        retry=retry_if_exception_type(
            TransientLLMError
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=2,
            max=8,
        ),
        reraise=True,
    )
    async def _generate_project_content(
        self,
        *,
        prompt: str,
    ) -> str:
        """
        Call Gemini for project recommendation generation.

        Temporary Gemini server failures are retried.
        """

        try:
            response = (
                await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            PROJECT_SYSTEM_PROMPT
                        ),
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema=(
                            LLMProjectRecommendation
                        ),
                        temperature=0.4,
                    ),
                )
            )

        except ServerError as exc:
            logger.warning(
                "gemini_project_temporary_error",
                extra={
                    "model": self.model,
                    "error": str(exc),
                },
            )

            raise TransientLLMError(
                "Gemini is temporarily unavailable."
            ) from exc

        except Exception as exc:
            logger.exception(
                "gemini_project_request_failed",
                extra={
                    "model": self.model,
                    "error_type": (
                        type(exc).__name__
                    ),
                },
            )

            raise LLMGenerationError(
                "Failed to generate project "
                "recommendation."
            ) from exc

        if not response.text:
            logger.error(
                "gemini_project_empty_response"
            )

            raise InvalidLLMResponseError(
                "The AI service returned an empty "
                "project recommendation."
            )

        return response.text

    async def generate_project_recommendation(
        self,
        *,
        goal_title: str,
        skills: list[str],
    ) -> ProjectRecommendation:
        """
        Generate and validate a personalized
        project recommendation.
        """

        prompt = build_project_prompt(
            goal_title=goal_title,
            skills=skills,
        )

        logger.info(
            "project_generation_started",
            extra={
                "goal_title": goal_title,
                "skill_count": len(skills),
                "model": self.model,
            },
        )

        try:
            response_text = (
                await self._generate_project_content(
                    prompt=prompt
                )
            )

        except TransientLLMError as exc:
            logger.error(
                "project_generation_unavailable",
                extra={
                    "goal_title": goal_title,
                },
            )

            raise LLMGenerationError(
                "The AI service is temporarily "
                "unavailable. Please try again shortly."
            ) from exc

        try:
            project = (
                ProjectRecommendation.model_validate_json(
                    response_text
                )
            )

        except ValidationError as exc:
            logger.exception(
                "project_response_validation_failed",
                extra={
                    "goal_title": goal_title,
                    "validation_error_count": (
                        exc.error_count()
                    ),
                },
            )

            raise InvalidLLMResponseError(
                "The generated project recommendation "
                "did not match the required schema."
            ) from exc

        logger.info(
            "project_generation_completed",
            extra={
                "goal_title": goal_title,
                "project_title": project.title,
                "difficulty": project.difficulty,
                "estimated_hours": (
                    project.estimated_hours
                ),
            },
        )

        return project

    # ============================================================
    # RAG CHAT GENERATION
    # ============================================================

    @retry(
        retry=retry_if_exception_type(
            TransientLLMError
        ),
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=2,
            max=8,
        ),
        reraise=True,
    )
    async def _generate_chat_content(
        self,
        *,
        prompt: str,
    ) -> str:
        """
        Call Gemini for roadmap-grounded chat generation.

        Temporary Gemini server failures are retried.
        """

        try:
            response = (
                await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            CHAT_SYSTEM_PROMPT
                        ),
                        response_mime_type=(
                            "application/json"
                        ),
                        response_schema=(
                            LLMChatResponse
                        ),
                        temperature=0.3,
                    ),
                )
            )

        except ServerError as exc:
            logger.warning(
                "gemini_chat_temporary_error",
                extra={
                    "model": self.model,
                    "error": str(exc),
                },
            )

            raise TransientLLMError(
                "Gemini is temporarily unavailable."
            ) from exc

        except Exception as exc:
            logger.exception(
                "gemini_chat_request_failed",
                extra={
                    "model": self.model,
                    "error_type": (
                        type(exc).__name__
                    ),
                },
            )

            raise LLMGenerationError(
                "Failed to generate chat response."
            ) from exc

        if not response.text:
            logger.error(
                "gemini_chat_empty_response"
            )

            raise InvalidLLMResponseError(
                "The AI service returned an empty "
                "chat response."
            )

        return response.text

    async def generate_chat_response(
        self,
        *,
        message: str,
        retrieved_context: list[str],
    ) -> ChatResponse:
        """
        Generate a grounded response using retrieved
        roadmap context.

        The LLM receives only the chunks retrieved by
        the RAG pipeline, not the complete roadmap.
        """

        if not retrieved_context:
            logger.warning(
                "chat_context_not_found"
            )

            return ChatResponse(
                response=(
                    "I could not find enough relevant "
                    "roadmap context to answer this "
                    "question reliably."
                ),
                follow_up_questions=[
                    (
                        "Would you like to ask about a "
                        "specific roadmap task?"
                    )
                ],
            )

        prompt = build_chat_prompt(
            message=message,
            retrieved_context=retrieved_context,
        )

        logger.info(
            "chat_generation_started",
            extra={
                "retrieved_chunk_count": len(
                    retrieved_context
                ),
                "model": self.model,
            },
        )

        try:
            response_text = (
                await self._generate_chat_content(
                    prompt=prompt
                )
            )

        except TransientLLMError as exc:
            logger.error(
                "chat_generation_unavailable"
            )

            raise LLMGenerationError(
                "The AI service is temporarily "
                "unavailable. Please try again shortly."
            ) from exc

        try:
            chat_response = (
                ChatResponse.model_validate_json(
                    response_text
                )
            )

        except ValidationError as exc:
            logger.exception(
                "chat_response_validation_failed",
                extra={
                    "validation_error_count": (
                        exc.error_count()
                    ),
                },
            )

            raise InvalidLLMResponseError(
                "The generated chat response "
                "did not match the required schema."
            ) from exc

        logger.info(
            "chat_generation_completed",
            extra={
                "retrieved_chunk_count": len(
                    retrieved_context
                ),
                "follow_up_count": len(
                    chat_response.follow_up_questions
                ),
            },
        )

        return chat_response


gemini_client = GeminiClient()