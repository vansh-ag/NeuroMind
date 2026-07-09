from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import gemini_client
from app.core.exceptions import (
    RoadmapNotFoundError,
)
from app.rag.retriever import (
    roadmap_retriever,
)
from app.repositories.roadmap_repository import (
    RoadmapRepository,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)


class ChatService:
    """
    Orchestrate the roadmap-grounded RAG chat workflow.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.roadmap_repository = (
            RoadmapRepository(
                session=session
            )
        )

    async def chat(
        self,
        request: ChatRequest,
    ) -> ChatResponse:
        """
        Validate roadmap existence, retrieve relevant context,
        and generate a grounded answer.
        """

        roadmap = (
            await self.roadmap_repository.get_by_id(
                roadmap_id=request.roadmap_id
            )
        )

        if roadmap is None:
            raise RoadmapNotFoundError(
                roadmap_id=str(
                    request.roadmap_id
                )
            )

        retrieved_context = (
            await roadmap_retriever.retrieve(
                roadmap_id=request.roadmap_id,
                query=request.message,
            )
        )

        return await gemini_client.generate_chat_response(
            message=request.message,
            retrieved_context=retrieved_context,
        )