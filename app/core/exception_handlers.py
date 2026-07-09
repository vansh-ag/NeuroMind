import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ApplicationError,
    InvalidLLMResponseError,
    LLMGenerationError,
    RoadmapNotFoundError,
)


logger = logging.getLogger(__name__)


def create_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    """
    Create a consistent API error response.
    """

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    """
    Register application exception handlers.
    """

    @app.exception_handler(RoadmapNotFoundError)
    async def roadmap_not_found_handler(
        request: Request,
        exc: RoadmapNotFoundError,
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code=exc.code,
            message=exc.message,
        )


    @app.exception_handler(InvalidLLMResponseError)
    async def invalid_llm_response_handler(
        request: Request,
        exc: InvalidLLMResponseError,
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=exc.code,
            message=exc.message,
        )


    @app.exception_handler(LLMGenerationError)
    async def llm_generation_error_handler(
        request: Request,
        exc: LLMGenerationError,
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=exc.code,
            message=exc.message,
        )


    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=exc.code,
            message=exc.message,
        )