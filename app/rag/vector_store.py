import logging
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.config import settings


logger = logging.getLogger(__name__)


class VectorStore:
    """
    Qdrant vector storage abstraction.

    Stores:
    - embedding vector;
    - roadmap_id;
    - chunk_index;
    - task_title;
    - original chunk content.
    """

    def __init__(self) -> None:
        self.client = AsyncQdrantClient(
            path=settings.qdrant_path
        )

        self.collection_name = (
            settings.qdrant_collection_name
        )

        self.vector_size = (
            settings.embedding_dimensions
        )

    async def ensure_collection(
        self,
    ) -> None:
        """
        Create the vector collection when it does not exist.
        """

        exists = await self.client.collection_exists(
            collection_name=self.collection_name
        )

        if exists:
            return

        await self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE,
            ),
        )

        logger.info(
            "qdrant_collection_created",
            extra={
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
            },
        )

    async def replace_roadmap_chunks(
        self,
        *,
        roadmap_id: UUID,
        points: list[PointStruct],
    ) -> None:
        """
        Replace all indexed chunks for one roadmap.

        This allows safe re-indexing without duplicate chunks.
        """

        await self.ensure_collection()

        roadmap_filter = Filter(
            must=[
                FieldCondition(
                    key="roadmap_id",
                    match=MatchValue(
                        value=str(roadmap_id)
                    ),
                )
            ]
        )

        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=roadmap_filter,
            wait=True,
        )

        if not points:
            return

        await self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

        logger.info(
            "roadmap_vectors_upserted",
            extra={
                "roadmap_id": str(roadmap_id),
                "point_count": len(points),
            },
        )

    async def search(
        self,
        *,
        roadmap_id: UUID,
        query_vector: list[float],
        limit: int,
    ) -> list[str]:
        """
        Search for relevant chunks within one roadmap.

        Vector similarity ranks chunks while the payload
        filter prevents cross-roadmap retrieval.
        """

        await self.ensure_collection()

        roadmap_filter = Filter(
            must=[
                FieldCondition(
                    key="roadmap_id",
                    match=MatchValue(
                        value=str(roadmap_id)
                    ),
                )
            ]
        )

        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=roadmap_filter,
            limit=limit,
            with_payload=True,
        )

        contents: list[str] = []

        for point in result.points:
            if not point.payload:
                continue

            content = point.payload.get("content")

            if isinstance(content, str):
                contents.append(content)

        return contents


vector_store = VectorStore()