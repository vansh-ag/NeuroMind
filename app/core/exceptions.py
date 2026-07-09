class ApplicationError(Exception):
    """
    Base exception for application-specific errors.
    """

    def __init__(
        self,
        message: str,
        code: str = "APPLICATION_ERROR",
    ) -> None:
        self.message = message
        self.code = code

        super().__init__(message)


class LLMGenerationError(ApplicationError):
    """
    Raised when communication with the LLM provider fails.
    """

    def __init__(
        self,
        message: str = (
            "Failed to generate content using the AI service."
        ),
    ) -> None:
        super().__init__(
            message=message,
            code="LLM_GENERATION_ERROR",
        )


class InvalidLLMResponseError(ApplicationError):
    """
    Raised when generated AI output remains invalid.
    """

    def __init__(
        self,
        message: str = (
            "The AI service returned an invalid structured response."
        ),
    ) -> None:
        super().__init__(
            message=message,
            code="INVALID_LLM_RESPONSE",
        )


class RoadmapNotFoundError(ApplicationError):
    """
    Raised when a requested roadmap does not exist.
    """

    def __init__(
        self,
        roadmap_id: str,
    ) -> None:
        super().__init__(
            message=f"Roadmap '{roadmap_id}' was not found.",
            code="ROADMAP_NOT_FOUND",
        )