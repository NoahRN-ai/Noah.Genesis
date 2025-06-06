import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, HTTPException # Added HTTPException here for clarity, though it was used below
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware # For frontend later
import firebase_admin # For lifespan manager
from google.api_core import exceptions as google_exceptions # For generic GCP error handling

from backend.app.api.v1.api import api_router_v1
from backend.app.core.config import settings
from backend.app.core.security import initialize_firebase_admin # To call in lifespan
from backend.app.core.exceptions import (
    AppException, NotFoundError, InvalidInputError, LLMError,
    LLMConnectionError, LLMResponseError, OperationFailedError,
    UnauthorizedError, ForbiddenError
)
from backend.app.models.api_models import ErrorDetail

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL.upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Initializing resources...")
    try:
        initialize_firebase_admin()
    except Exception as e:
        logger.error(f"Critical error during Firebase Admin SDK initialization: {e}", exc_info=True)
    logger.info("Core resources (Firebase Admin) initialized via lifespan event.")
    yield
    logger.info("Application shutdown: Cleaning up resources...")
    if firebase_admin._DEFAULT_APP_NAME in firebase_admin._apps:
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
            logger.info("Firebase Admin app deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting Firebase Admin app during shutdown: {e}", exc_info=True)
    logger.info("Cleanup finished.")


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# --- Global Exception Handlers ---
# These should be defined after `app` is initialized and ideally before middlewares/routers if they could raise.
# However, for exceptions from route handlers, their placement relative to middlewares that *don't* process responses
# (like CORS) is less critical than for middlewares that *do* (like a logging/timing one).
# Placing them before routers is standard.

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(f"Application exception caught: {exc.detail} (Code: {exc.error_code}, Status: {exc.status_code}) for {request.method} {request.url.path}", exc_info= (exc.status_code >= 500) )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(detail=exc.detail, error_code=exc.error_code).model_dump(exclude_none=True)
    )

# --- Middlewares ---
# Middlewares are processed in the order they are added.
# Exception handlers are checked after routing and middleware processing if an exception bubbles up.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path} Client: {request.client.host if request.client else 'Unknown'}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
    return response

# --- FastAPI's Default & Other Specific Exception Handlers ---
# These are more specific than the generic `AppException` handler if those exceptions are raised directly.
# If an `AppException` subclass is raised, it will be caught by `app_exception_handler` first.

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Request validation error: {exc.errors()} for {request.method} {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body if hasattr(exc, 'body') else None},
    )

# It's important to place generic FastAPI HTTPException handler after custom specific ones,
# or ensure custom ones cover what you need. If an HTTPException is raised that isn't an AppException,
# this will catch it.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    # Avoid double logging if it's an AppException that was re-raised as HTTPException or similar
    # This check is simplistic; more robust context passing might be needed if this becomes an issue.
    if not isinstance(exc, AppException): # Or a more specific check
        logger.log(log_level, f"FastAPI HTTPException: {exc.status_code} {exc.detail} for {request.method} {request.url.path}", exc_info= (exc.status_code >= 500) )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}, # Standard FastAPI HTTPException doesn't have error_code
        headers=exc.headers,
    )


@app.exception_handler(google_exceptions.GoogleAPICallError)
async def google_api_call_exception_handler(request: Request, exc: google_exceptions.GoogleAPICallError):
    logger.error(f"Google API Call Error: {exc} for {request.method} {request.url.path}", exc_info=True)
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "A downstream Google Cloud service is unavailable or returned an error."
    error_code = "GOOGLE_API_ERROR"
    if isinstance(exc, google_exceptions.NotFound):
        status_code = status.HTTP_404_NOT_FOUND
        detail = "A required Google Cloud resource was not found."
        error_code = "GOOGLE_API_NOT_FOUND"
    elif isinstance(exc, google_exceptions.PermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
        detail = "Permission denied while accessing a Google Cloud service."
        error_code = "GOOGLE_API_PERMISSION_DENIED"
    elif isinstance(exc, google_exceptions.ResourceExhausted):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        detail = "Quota exhausted for a Google Cloud service. Please try again later."
        error_code = "GOOGLE_API_RESOURCE_EXHAUSTED"

    return JSONResponse(
        status_code=status_code,
        content=ErrorDetail(detail=detail, error_code=error_code).model_dump(exclude_none=True)
    )

# The generic Exception handler should be last as a catch-all.
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc} for {request.method} {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorDetail(detail="An unexpected internal server error occurred.", error_code="INTERNAL_SERVER_ERROR").model_dump(exclude_none=True)
    )

# --- Routers ---
app.include_router(api_router_v1, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "app_name": settings.APP_NAME}

# To run locally (from project root, after `poetry install`):
# poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
# Ensure .env file is present in project root with GCP_PROJECT_ID etc.
