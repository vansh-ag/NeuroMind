import logging

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.exceptions import LLMGenerationError


logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Generate vector embeddings for roadmap documents
    and user queries.
    """

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    async def _embed(
        self,
        *,
        text: str,
    ) -> list[float]:
        """
        Generate one embedding vector.
        """

        try:
            result = await self.client.aio.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimensions,
                ),
            )

        except Exception as exc:
            logger.exception(
                "embedding_generation_failed",
                extra={
                    "model": self.model,
                    "error_type": type(exc).__name__,
                },
            )

            raise LLMGenerationError(
                "Failed to generate embedding."
            ) from exc

        if not result.embeddings:
            raise LLMGenerationError(
                "The embedding service returned no embeddings."
            )

        values = result.embeddings[0].values

        if values is None:
            raise LLMGenerationError(
                "The embedding service returned empty vector values."
            )

        vector = list(values)

        if len(vector) != self.dimensions:
            logger.error(
                "embedding_dimension_mismatch",
                extra={
                    "expected": self.dimensions,
                    "received": len(vector),
                },
            )

            raise LLMGenerationError(
                "The embedding vector has an unexpected dimension."
            )

        return vector

    async def embed_document(
        self,
        *,
        content: str,
    ) -> list[float]:
        """
        Generate an embedding for stored roadmap content.
        """

        prepared_text = (
            "Represent this learning roadmap task for retrieval:\n\n"
            f"{content}"
        )

        return await self._embed(
            text=prepared_text
        )

    async def embed_query(
        self,
        *,
        query: str,
    ) -> list[float]:
        """
        Generate an embedding for a user search question.
        """

        prepared_text = (
            "Find roadmap sections relevant to this learner question:\n\n"
            f"{query}"
        )

        return await self._embed(
            text=prepared_text
        )


embedding_service = EmbeddingService()