from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class AppException(Exception):
    """Base exception for all system-specific errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )


class EntityAlreadyExistsException(AppException):
    def __init__(self, entity_name: str, identifier: str):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' already exists.",
            status_code=status.HTTP_409_CONFLICT
        )


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationException(AppException):
    def __init__(self, message: str = "Access denied."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(f"AppException: {exc.message} (status: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "message": exc.message,
                    "type": exc.__class__.__name__
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "message": "An unexpected error occurred on the server.",
                    "type": "InternalServerError"
                }
            }
        )
