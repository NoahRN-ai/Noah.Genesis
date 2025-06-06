from typing import Optional

class AppException(Exception):
    """Base class for application-specific exceptions."""
    def __init__(self, detail: str, error_code: Optional[str] = None, status_code: int = 500):
        super().__init__(detail)
        self.detail = detail
        self.error_code = error_code
        self.status_code = status_code # Default status code, can be overridden by handlers

class NotFoundError(AppException):
    """Raised when a requested resource is not found."""
    def __init__(self, detail: str = "Resource not found", error_code: Optional[str] = "NOT_FOUND"):
        super().__init__(detail, error_code, status_code=404)

class OperationFailedError(AppException):
    """Raised when an operation (e.g., write, update) fails unexpectedly."""
    def __init__(self, detail: str = "Operation failed", error_code: Optional[str] = "OPERATION_FAILED"):
        super().__init__(detail, error_code, status_code=500)

class InvalidInputError(AppException):
    """Raised when input data is invalid or fails validation."""
    def __init__(self, detail: str = "Invalid input", error_code: Optional[str] = "INVALID_INPUT"):
        super().__init__(detail, error_code, status_code=400)

class LLMError(AppException):
    """Base class for LLM-related errors."""
    def __init__(self, detail: str = "LLM processing error", error_code: Optional[str] = "LLM_ERROR", status_code: int = 500):
        super().__init__(detail, error_code, status_code)

class LLMConnectionError(LLMError):
    """Raised for issues connecting to the LLM service or underlying infrastructure problems."""
    def __init__(self, detail: str = "LLM connection error", error_code: Optional[str] = "LLM_CONNECTION_ERROR"):
        super().__init__(detail, error_code, status_code=503) # Service Unavailable

class LLMResponseError(LLMError):
    """Raised for issues with the LLM's response (e.g., blocked, empty, malformed)."""
    def __init__(self, detail: str = "LLM response error", error_code: Optional[str] = "LLM_RESPONSE_ERROR"):
        super().__init__(detail, error_code, status_code=500)

class UnauthorizedError(AppException):
    """Raised when an action is unauthorized (though FastAPI typically handles 401/403 directly)."""
    def __init__(self, detail: str = "Unauthorized", error_code: Optional[str] = "UNAUTHORIZED"):
        super().__init__(detail, error_code, status_code=401) # Or 403 if authenticated but not permitted

class ForbiddenError(AppException):
    """Raised when an authenticated user is not permitted to perform an action."""
    def __init__(self, detail: str = "Forbidden", error_code: Optional[str] = "FORBIDDEN"):
        super().__init__(detail, error_code, status_code=403)
