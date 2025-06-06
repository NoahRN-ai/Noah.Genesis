import json
import logging
import os
from typing import Any, Optional

import vertexai
from google.cloud import storage
from vertexai.language_models import TextEmbeddingModel

# Correct import for IndexEndpoint based on Vertex AI SDK structure
from vertexai.resources.preview.aiplatform.matching_engine.index_endpoint import (
    IndexEndpoint,
)

# Configure logging
logger = logging.getLogger(__name__)

# --- Configuration (from environment variables) ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
RAG_GCS_BUCKET_NAME = os.getenv("RAG_GCS_BUCKET_NAME")
CHUNK_MAP_GCS_OBJECT_NAME = os.getenv(
    "RAG_CHUNK_MAP_GCS_OBJECT_NAME", "metadata/id_to_chunk_details_map.json"
)
VERTEX_AI_INDEX_ENDPOINT_ID = os.getenv(
    "VERTEX_AI_INDEX_ENDPOINT_ID"
)  # Full Resource Name or just ID
VERTEX_AI_DEPLOYED_INDEX_ID = os.getenv(
    "VERTEX_AI_DEPLOYED_INDEX_ID"
)  # User-defined ID used in Terraform

EMBEDDING_MODEL_NAME = "textembedding-gecko@003"

_vertex_ai_initialized_rag_service = False
_id_to_chunk_details_map: Optional[dict[str, dict[str, Any]]] = None
_embedding_model: Optional[TextEmbeddingModel] = None
_index_endpoint_client: Optional[IndexEndpoint] = None


def _init_rag_dependencies_once():
    global \
        _vertex_ai_initialized_rag_service, \
        _id_to_chunk_details_map, \
        _embedding_model, \
        _index_endpoint_client

    if _vertex_ai_initialized_rag_service:
        return

    if not all(
        [
            GCP_PROJECT_ID,
            GCP_REGION,
            RAG_GCS_BUCKET_NAME,
            CHUNK_MAP_GCS_OBJECT_NAME,
            VERTEX_AI_INDEX_ENDPOINT_ID,
            VERTEX_AI_DEPLOYED_INDEX_ID,
        ]
    ):
        logger.error(
            "RAG Service: Missing one or more critical environment variables. Check GCP_PROJECT_ID, GCP_REGION, RAG_GCS_BUCKET_NAME, CHUNK_MAP_GCS_OBJECT_NAME, VERTEX_AI_INDEX_ENDPOINT_ID, VERTEX_AI_DEPLOYED_INDEX_ID."
        )
        return

    try:
        vertexai.init(
            project=GCP_PROJECT_ID, location=GCP_REGION
        )  # Ensure it's initialized

        # 1. Load Embedding Model
        _embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL_NAME)
        logger.info(f"RAG Service: Embedding model '{EMBEDDING_MODEL_NAME}' loaded.")

        # 2. Load ID-to-Chunk Details Map from GCS
        logger.info(
            f"RAG Service: Loading chunk metadata map from gs://{RAG_GCS_BUCKET_NAME}/{CHUNK_MAP_GCS_OBJECT_NAME}..."
        )
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(RAG_GCS_BUCKET_NAME)
        blob = bucket.blob(CHUNK_MAP_GCS_OBJECT_NAME)

        if not blob.exists():
            logger.error(
                f"RAG Service: Chunk metadata map not found at gs://{RAG_GCS_BUCKET_NAME}/{CHUNK_MAP_GCS_OBJECT_NAME}. RAG will not function correctly."
            )
            _id_to_chunk_details_map = {}
        else:
            try:
                json_data = blob.download_as_string()
                _id_to_chunk_details_map = json.loads(json_data)
                logger.info(
                    f"RAG Service: Successfully loaded chunk metadata map with {len(_id_to_chunk_details_map)} entries."
                )
            except Exception as e_json:
                logger.error(
                    f"RAG Service: Failed to parse chunk metadata map JSON from GCS: {e_json}"
                )
                _id_to_chunk_details_map = {}

        # 3. Initialize Vertex AI Index Endpoint client
        # The VERTEX_AI_INDEX_ENDPOINT_ID should be the full resource name path for IndexEndpoint constructor.
        # Example: "projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/indexEndpoints/{ENDPOINT_NUMERIC_ID}"
        # Terraform output `vertex_ai_rag_index_endpoint_id` provides this full path.
        _index_endpoint_client = IndexEndpoint(
            index_endpoint_name=VERTEX_AI_INDEX_ENDPOINT_ID
        )
        logger.info(
            f"RAG Service: Vertex AI Index Endpoint client initialized for endpoint '{VERTEX_AI_INDEX_ENDPOINT_ID}'."
        )

        _vertex_ai_initialized_rag_service = True
    except Exception as e:
        logger.error(
            f"RAG Service: Failed to initialize dependencies: {e}", exc_info=True
        )


_init_rag_dependencies_once()  # Initialize on module load


async def generate_embedding_for_query(query_text: str) -> Optional[list[float]]:
    """Generates embedding for a single query text."""
    if not _embedding_model:
        logger.error("RAG Service: Embedding model not initialized.")
        _init_rag_dependencies_once()  # Attempt re-initialization
        if not _embedding_model:
            return None
    try:
        embeddings = await _embedding_model.get_embeddings_async([query_text])
        return embeddings[0].values if embeddings else None
    except Exception as e:
        logger.error(
            f"RAG Service: Failed to generate embedding for query: {e}", exc_info=True
        )
        return None


async def retrieve_relevant_chunks(
    query_text: str,
    top_k: int = 3,
    # Optional: filtering parameters if namespaces were set up in index data
    # filter_source_document: Optional[str] = None
) -> list[dict[str, Any]]:
    """Retrieves relevant text chunks for a given query using Vertex AI Vector Search.

    Args:
    ----
        query_text: The user's query.
        top_k: The number of top relevant chunks to retrieve.

    Returns:
    -------
        A list of dictionaries, each containing "id", "chunk_text",
        "source_document_name", "score", and other "metadata".
    """
    if (
        not _vertex_ai_initialized_rag_service
        or not _index_endpoint_client
        or _id_to_chunk_details_map is None
        or not _embedding_model
    ):
        logger.error(
            "RAG Service or its dependencies are not initialized. Cannot retrieve chunks."
        )
        _init_rag_dependencies_once()  # Attempt re-initialization
        if (
            not _vertex_ai_initialized_rag_service
            or not _index_endpoint_client
            or _id_to_chunk_details_map is None
            or not _embedding_model
        ):
            return []

    query_embedding = await generate_embedding_for_query(query_text)
    if not query_embedding:
        return []

    try:
        logger.debug(
            f"RAG Service: Querying Vector Search endpoint with deployed index '{VERTEX_AI_DEPLOYED_INDEX_ID}' for top {top_k} neighbors."
        )

        # find_neighbors takes a list of queries (embeddings)
        response = await _index_endpoint_client.find_neighbors_async(
            deployed_index_id=VERTEX_AI_DEPLOYED_INDEX_ID,
            queries=[query_embedding],
            num_neighbors=top_k,
        )

        relevant_chunks = []
        if (
            response and response[0]
        ):  # Check if response and the first query's neighbors exist
            for neighbor in response[0]:
                chunk_id = neighbor.id
                chunk_score = neighbor.distance

                chunk_details = _id_to_chunk_details_map.get(chunk_id)
                if chunk_details:
                    relevant_chunks.append(
                        {
                            "id": chunk_id,
                            "chunk_text": chunk_details.get("text", ""),
                            "source_document_name": chunk_details.get(
                                "source", "Unknown"
                            ),
                            "score": chunk_score,
                            "metadata": {
                                "chunk_index_in_doc": chunk_details.get("chunk_idx"),
                                "start_index_in_doc": chunk_details.get("start_idx"),
                            },
                        }
                    )
                else:
                    logger.warning(
                        f"RAG Service: Chunk ID '{chunk_id}' found by Vector Search, but no details in metadata map."
                    )

        logger.info(
            f"RAG Service: Retrieved {len(relevant_chunks)} relevant chunks for query."
        )
        return relevant_chunks

    except Exception as e:
        logger.error(
            f"RAG Service: Error during Vector Search query or processing: {e}",
            exc_info=True,
        )
        return []
