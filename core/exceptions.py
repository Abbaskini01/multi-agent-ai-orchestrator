"""
Neural Glass AI Orchestrator — Global Exception Domain & Handlers
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from core.config import settings
from core.logger import log_event


class NeuralGlassBaseException(Exception):
    """Base exception class for platform errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMProviderException(NeuralGlassBaseException):
    """Raised when an external LLM SDK request fails."""
    pass


class WorkspaceStorageException(NeuralGlassBaseException):
    """Raised when sandbox storage operations fail."""
    pass


def register_exception_handlers(app):
    """Registers HTTP problem-detail exception handlers on FastAPI."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        log_event("http_validation_error", path=request.url.path, errors=exc.errors(), level="warning")
        return JSONResponse(
            status_code=422,
            content={
                "type": "https://neuralglass.ai/errors/validation-error",
                "title": "Unprocessable Entity",
                "status": 422,
                "detail": "Input validation failed for request payload.",
                "errors": exc.errors() if settings.debug else []
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        log_event("http_exception", path=request.url.path, status_code=exc.status_code, detail=exc.detail, level="warning")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": f"https://neuralglass.ai/errors/http-{exc.status_code}",
                "title": "HTTP Exception",
                "status": exc.status_code,
                "detail": str(exc.detail)
            }
        )

    @app.exception_handler(NeuralGlassBaseException)
    async def domain_exception_handler(request: Request, exc: NeuralGlassBaseException):
        log_event("domain_exception", path=request.url.path, error=exc.message, level="error")
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://neuralglass.ai/errors/domain-error",
                "title": "Domain Execution Error",
                "status": 500,
                "detail": exc.message if settings.debug else "A platform execution error occurred."
            }
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log_event("unhandled_global_exception", path=request.url.path, error=str(exc), level="error")
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://neuralglass.ai/errors/internal-server-error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": str(exc) if settings.debug else "An unexpected internal error occurred."
            }
        )