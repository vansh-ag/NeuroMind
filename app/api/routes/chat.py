from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import (
    ChatService,
)


router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with a generated roadmap",
)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Answer user questions using roadmap-grounded RAG.
    """

    service = ChatService(
        session=session
    )

    return await service.chat(
        request=payload
    )