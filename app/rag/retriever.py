from uuid import UUID

from app.core.config import settings
from app.rag.embedding_service import (
    embedding_service,
)
from app.rag.vector_store import (
    vector_store,
)


class RoadmapRetriever:
    """
    Retrieve semantically relevant roadmap context.
    """

    async def retrieve(
        self,
        *,
        roadmap_id: UUID,
        query: str,
    ) -> list[str]:
        """
        Embed the user's question and retrieve top-k chunks.
        """

        query_embedding = (
            await embedding_service.embed_query(
                query=query
            )
        )

        return await vector_store.search(
            roadmap_id=roadmap_id,
            query_vector=query_embedding,
            limit=settings.rag_top_k,
        )


roadmap_retriever = RoadmapRetriever()