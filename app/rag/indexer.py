import logging
from uuid import uuid4

from qdrant_client.models import PointStruct

from app.models.roadmap import Roadmap
from app.rag.document_builder import (
    build_roadmap_documents,
)
from app.rag.embedding_service import (
    embedding_service,
)
from app.rag.vector_store import (
    vector_store,
)


logger = logging.getLogger(__name__)


class RoadmapIndexer:
    """
    Convert a saved roadmap into embedded Qdrant points.
    """

    async def index(
        self,
        *,
        roadmap: Roadmap,
    ) -> None:
        """
        Build task-level chunks, embed them, and store them.
        """

        documents = build_roadmap_documents(
            roadmap
        )

        points: list[PointStruct] = []

        for document in documents:
            embedding = (
                await embedding_service.embed_document(
                    content=document.content
                )
            )

            point = PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "roadmap_id": str(roadmap.id),
                    "chunk_index": document.chunk_index,
                    "task_title": document.task_title,
                    "content": document.content,
                },
            )

            points.append(point)

        await vector_store.replace_roadmap_chunks(
            roadmap_id=roadmap.id,
            points=points,
        )

        logger.info(
            "roadmap_indexing_completed",
            extra={
                "roadmap_id": str(roadmap.id),
                "chunk_count": len(points),
            },
        )


roadmap_indexer = RoadmapIndexer()