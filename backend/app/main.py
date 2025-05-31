import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware # For frontend later
import firebase_admin # For lifespan manager
from google.api_core import exceptions as google_exceptions # For generic GCP error handling


from backend.app.api.v1.api import api_router_v1
from backend.app.core.config import settings
from backend.app.core.security import initialize_firebase_admin # To call in lifespan

# Configure logging (can be more sophisticated using logging.config.dictConfig)
# Ensure this is configured before any loggers are instantiated if using dictConfig
# For basicConfig, it's fine here.
logging.basicConfig(level=settings.LOG_LEVEL.upper(),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Initializing resources...")
    # Initialize Firebase Admin SDK
    try:
        initialize_firebase_admin() # From security.py
    except Exception as e:
        logger.error(f"Critical error during Firebase Admin SDK initialization: {e}", exc_info=True)
        # Decide if app should fail to start if Firebase is critical

    # Initialize Vertex AI (already happens on llm_service module import, but good place for other global inits)
    # from backend.app.services.llm_service import _init_vertex_ai_once # Example
    # _init_vertex_ai_once() # Ensure it's called if not already by module import

    # Initialize RAG dependencies (already happens on rag_service module import)
    # from backend.app.services.rag_service import _init_rag_dependencies_once # Example
    # _init_rag_dependencies_once()

    logger.info("Core resources (Firebase Admin) initialized via lifespan event.")
    yield
    logger.info("Application shutdown: Cleaning up resources...")
    # Add cleanup logic here if needed (e.g., closing DB connections if not auto-managed)
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
    docs_url=f"{settings.API_V1_PREFIX}/docs", # Standard docs URL
    redoc_url=f"{settings.API_V1_PREFIX}/redoc", # Standard ReDoc URL
    lifespan=lifespan
)

# --- Middlewares ---

# CORS (Cross-Origin Resource Sharing) - configure as needed for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify frontend origins: e.g., ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic Structured Logging Middleware Example
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    # Log basic request info
    logger.info(f"Request: {request.method} {request.url.path} Client: {request.client.host if request.client else 'Unknown'}")
    response = await call_next(request)
    # Log basic response info
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
    return response

# --- Exception Handlers ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log detailed validation errors
    logger.warning(f"Request validation error: {exc.errors()} for {request.method} {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body if hasattr(exc, 'body') else None},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Log FastAPI HTTPExceptions
    log_level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(log_level, f"HTTPException: {exc.status_code} {exc.detail} for {request.method} {request.url.path}", exc_info= (exc.status_code >= 500) )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )

@app.exception_handler(google_exceptions.GoogleAPICallError)
async def google_api_call_exception_handler(request: Request, exc: google_exceptions.GoogleAPICallError):
    logger.error(f"Google API Call Error: {exc} for {request.method} {request.url.path}", exc_info=True)
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "A downstream Google Cloud service is unavailable or returned an error."
    if isinstance(exc, google_exceptions.NotFound):
        status_code = status.HTTP_404_NOT_FOUND
        detail = "A required Google Cloud resource was not found."
    elif isinstance(exc, google_exceptions.PermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
        detail = "Permission denied while accessing a Google Cloud service."
    elif isinstance(exc, google_exceptions.ResourceExhausted):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        detail = "Quota exhausted for a Google Cloud service. Please try again later."

    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "error_type": type(exc).__name__}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log any other unhandled exceptions
    logger.error(f"Unhandled exception: {exc} for {request.method} {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
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
