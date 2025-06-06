from functools import lru_cache
from typing import Optional  # Added for Optional type hint

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Project Noah MVP API"
    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    GCP_PROJECT_ID: str
    VERTEX_AI_REGION: str = "us-central1"
    DEFAULT_LLM_MODEL_NAME: str = (
        "gemini-1.0-pro-001"  # Or specific version like "gemini-1.0-pro-001"
    )

    # RAG Service Configuration (from environment variables set by Terraform outputs/Cloud Run)
    RAG_GCS_BUCKET_NAME: Optional[str] = None
    RAG_CHUNK_MAP_GCS_OBJECT_NAME: Optional[
        str
    ] = "metadata/id_to_chunk_details_map.json"
    VERTEX_AI_INDEX_ENDPOINT_ID: Optional[
        str
    ] = None  # Full Resource Name or Numeric ID
    VERTEX_AI_DEPLOYED_INDEX_ID: Optional[
        str
    ] = None  # User-defined ID for deployed index

    # Firebase configuration for auth - set via env in Cloud Run
    # If using a service account JSON for Firebase Admin SDK:
    FIREBASE_SERVICE_ACCOUNT_JSON_PATH: Optional[
        str
    ] = None  # Path to service account file
    # OR set GOOGLE_APPLICATION_CREDENTIALS which Firebase Admin SDK can also use.
    # OR if running on GCP with right SA, it might auto-discover.

    # Define a model_config to load from .env file for local dev
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache  # Cache the settings object
def get_settings() -> Settings:
    return Settings()


settings = get_settings()  # Global settings object accessible via import
