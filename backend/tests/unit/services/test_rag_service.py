import pytest
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from backend.app.services import rag_service # To allow patching its members
from backend.app.services.rag_service import (
    generate_embedding_for_query,
    retrieve_relevant_chunks,
    _init_rag_dependencies_once # Will test this indirectly or by resetting state
)

# Mocked environment variables
MOCK_ENV = {
    "GCP_PROJECT_ID": "test-project",
    "GCP_REGION": "test-region",
    "RAG_GCS_BUCKET_NAME": "test-rag-bucket",
    "RAG_ID_TO_CHUNK_MAP_JSON_PATH": "test-map.json",
    "RAG_EMBEDDING_MODEL_ID": "textembedding-gecko@003",
    "RAG_INDEX_ID": "test_index_123",
    "RAG_INDEX_ENDPOINT_ID": "test_index_endpoint_456"
}

@pytest.fixture(autouse=True)
def mock_env_vars_fixture(mocker):
    """Auto-used fixture to mock environment variables for RAG service."""
    mocker.patch.dict(os.environ, MOCK_ENV)

@pytest.fixture(autouse=True)
def mock_vertex_init_rag_fixture(mocker):
    """Auto-used fixture to mock vertexai.init for RAG service tests."""
    mocker.patch('vertexai.init', return_value=None)

@pytest.fixture
def reset_rag_service_state(mocker):
    """Fixture to reset RAG service internal state before a test."""
    mocker.patch.object(rag_service, '_vertex_ai_initialized_rag_service', False)
    mocker.patch.object(rag_service, '_embedding_model', None)
    mocker.patch.object(rag_service, '_index_endpoint_client', None)
    mocker.patch.object(rag_service, '_id_to_chunk_details_map', {})
    mocker.patch.object(rag_service, '_rag_gcs_bucket_name', None) # Ensure this is also reset or correctly set by init

@pytest.fixture
def mock_gcs_client_fixture(mocker):
    mock_client = MagicMock()
    mocker.patch('google.cloud.storage.Client', return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_embedding_model_fixture(mocker):
    mock_model = MagicMock()
    mock_model.get_embeddings_async = AsyncMock()
    mocker.patch('vertexai.language_models.TextEmbeddingModel.from_pretrained', return_value=mock_model)
    return mock_model

@pytest.fixture
def mock_index_endpoint_client_fixture(mocker):
    mock_ep_client = MagicMock()
    mock_ep_client.find_neighbors_async = AsyncMock()
    # Note: The class path might be different based on SDK version. Adjust if needed.
    mocker.patch('vertexai.resources.preview.aiplatform.matching_engine.index_endpoint.IndexEndpoint', return_value=mock_ep_client)
    return mock_ep_client


# --- Tests for _init_rag_dependencies_once (tested indirectly) ---

@pytest.mark.asyncio
async def test_init_rag_dependencies_success(
    reset_rag_service_state, # Ensure clean state
    mock_gcs_client_fixture,
    mock_embedding_model_fixture,
    mock_index_endpoint_client_fixture,
    caplog # To check logs
):
    sample_map_data = {"id1": {"text": "chunk1"}, "id2": {"text": "chunk2"}}
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True
    mock_blob.download_as_string.return_value = json.dumps(sample_map_data).encode('utf-8')
    mock_gcs_client_fixture.bucket.return_value.blob.return_value = mock_blob

    # Call a function that triggers initialization
    await generate_embedding_for_query("test query") # This will try to init if not already

    assert rag_service._vertex_ai_initialized_rag_service is True
    assert rag_service._embedding_model is not None
    assert rag_service._index_endpoint_client is not None
    assert rag_service._id_to_chunk_details_map == sample_map_data
    assert rag_service._rag_gcs_bucket_name == MOCK_ENV["RAG_GCS_BUCKET_NAME"]
    mock_gcs_client_fixture.bucket.assert_called_with(MOCK_ENV["RAG_GCS_BUCKET_NAME"])
    mock_gcs_client_fixture.bucket.return_value.blob.assert_called_with(MOCK_ENV["RAG_ID_TO_CHUNK_MAP_JSON_PATH"])


@pytest.mark.asyncio
async def test_init_rag_dependencies_gcs_map_not_found(
    reset_rag_service_state, mock_gcs_client_fixture, caplog
):
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False # Map file does not exist
    mock_gcs_client_fixture.bucket.return_value.blob.return_value = mock_blob

    # Explicitly call init or a function that triggers it
    rag_service._init_rag_dependencies_once() # Call directly after reset for this specific test

    assert rag_service._vertex_ai_initialized_rag_service is False # Should fail early if map is critical
    assert rag_service._id_to_chunk_details_map == {}
    assert any("Failed to load RAG ID-to-chunk map from GCS" in record.message for record in caplog.records)
    assert any(MOCK_ENV["RAG_ID_TO_CHUNK_MAP_JSON_PATH"] + " not found" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_init_rag_dependencies_gcs_map_invalid_json(
    reset_rag_service_state, mock_gcs_client_fixture, caplog
):
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True
    mock_blob.download_as_string.return_value = b"this is not json" # Invalid JSON
    mock_gcs_client_fixture.bucket.return_value.blob.return_value = mock_blob

    rag_service._init_rag_dependencies_once()

    assert rag_service._vertex_ai_initialized_rag_service is False
    assert rag_service._id_to_chunk_details_map == {}
    assert any("Failed to parse JSON from RAG ID-to-chunk map" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_init_rag_dependencies_missing_env_vars(reset_rag_service_state, mocker, caplog):
    mocker.patch.dict(os.environ, {k: v for k, v in MOCK_ENV.items() if k != "GCP_PROJECT_ID"}) # Remove one var

    rag_service._init_rag_dependencies_once()

    assert rag_service._vertex_ai_initialized_rag_service is False
    assert any("Missing required environment variable for RAG service: GCP_PROJECT_ID" in record.message for record in caplog.records)


# --- Tests for generate_embedding_for_query ---

@pytest.mark.asyncio
async def test_generate_embedding_success(
    reset_rag_service_state, mock_gcs_client_fixture, mock_embedding_model_fixture, mock_index_endpoint_client_fixture
):
    # Ensure successful initialization for this test
    sample_map_data = {"id1": {"text": "chunk1"}}
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True
    mock_blob.download_as_string.return_value = json.dumps(sample_map_data).encode('utf-8')
    mock_gcs_client_fixture.bucket.return_value.blob.return_value = mock_blob

    mock_embedding_result = MagicMock()
    mock_embedding_result.values = [0.1, 0.2, 0.3]
    mock_embedding_model_fixture.get_embeddings_async.return_value = [mock_embedding_result]

    query = "test query for embedding"
    embedding = await generate_embedding_for_query(query)

    assert rag_service._vertex_ai_initialized_rag_service is True # Init should have run
    assert embedding == [0.1, 0.2, 0.3]
    mock_embedding_model_fixture.get_embeddings_async.assert_called_once_with([query])


@pytest.mark.asyncio
async def test_generate_embedding_model_not_initialized(reset_rag_service_state, mocker, caplog):
    # Make init fail, e.g., by ensuring a required env var is missing for this specific test run of init
    mocker.patch.dict(os.environ, {k: v for k, v in MOCK_ENV.items() if k != "RAG_EMBEDDING_MODEL_ID"})

    embedding = await generate_embedding_for_query("query")
    assert embedding is None
    assert any("RAG service not initialized. Cannot generate embedding." in record.message for record in caplog.records)
    # Also check that init was attempted and failed
    assert any("Missing required environment variable for RAG service: RAG_EMBEDDING_MODEL_ID" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_generate_embedding_api_error(
    reset_rag_service_state, mock_gcs_client_fixture, mock_embedding_model_fixture, mock_index_endpoint_client_fixture, caplog
):
    # Successful init
    mock_blob = MagicMock(); mock_blob.exists.return_value = True
    mock_blob.download_as_string.return_value = json.dumps({"id1": {"text": "c1"}}).encode('utf-8')
    mock_gcs_client_fixture.bucket.return_value.blob.return_value = mock_blob

    mock_embedding_model_fixture.get_embeddings_async.side_effect = Exception("Embedding API Error")

    embedding = await generate_embedding_for_query("query")
    assert embedding is None
    assert any("Error generating embedding: Embedding API Error" in record.message for record in caplog.records)


# --- Tests for retrieve_relevant_chunks ---

@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_success(
    reset_rag_service_state, mock_gcs_client_fixture, mock_embedding_model_fixture, mock_index_endpoint_client_fixture, mocker
):
    # 1. Successful init with map data
    sample_map = {
        "chunk_id_1": {"text": "Relevant text 1", "source": "doc A", "page": 1},
        "chunk_id_2": {"text": "Relevant text 2", "source": "doc B", "page": 5},
    }
    mock_blob = MagicMock(); mock_blob.exists.return_value = True
    mock_blob.download_as_string.return_value = json.dumps(sample_map).encode('utf-8')
    mock_gcs_client_fixture.bucket.return_value.blob.return_value = mock_blob

    # 2. Mock generate_embedding_for_query (or let it run if _embedding_model is mocked)
    mock_query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    mocker.patch.object(rag_service, 'generate_embedding_for_query', AsyncMock(return_value=mock_query_embedding))

    # 3. Mock find_neighbors_async
    mock_neighbor1 = MagicMock(); mock_neighbor1.id = "chunk_id_1"; mock_neighbor1.distance = 0.8
    mock_neighbor2 = MagicMock(); mock_neighbor2.id = "chunk_id_2"; mock_neighbor2.distance = 0.7
    mock_index_endpoint_client_fixture.find_neighbors_async.return_value = [mock_neighbor1, mock_neighbor2]

    query_text = "Find relevant info"
    num_chunks = 2
    chunks = await retrieve_relevant_chunks(query_text, num_chunks)

    assert rag_service.generate_embedding_for_query.called_once_with(query_text)
    mock_index_endpoint_client_fixture.find_neighbors_async.assert_called_once()
    # Check args of find_neighbors_async if specific deployed_index_id is important

    assert len(chunks) == 2
    assert chunks[0]["id"] == "chunk_id_1"
    assert chunks[0]["text"] == sample_map["chunk_id_1"]["text"]
    assert chunks[0]["source"] == sample_map["chunk_id_1"]["source"]
    assert chunks[0]["distance"] == 0.8
    assert chunks[1]["id"] == "chunk_id_2"


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_service_not_initialized(reset_rag_service_state, mocker, caplog):
    mocker.patch.dict(os.environ, {k: v for k, v in MOCK_ENV.items() if k != "GCP_PROJECT_ID"}) # Cause init to fail

    chunks = await retrieve_relevant_chunks("query", 5)
    assert chunks == []
    assert any("RAG service not initialized. Cannot retrieve chunks." in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_no_embedding(reset_rag_service_state, mocker, caplog):
    # Init successfully, but embedding fails
    mocker.patch.object(rag_service, '_init_rag_dependencies_once', MagicMock()) # Prevent actual init
    mocker.patch.object(rag_service, '_vertex_ai_initialized_rag_service', True) # Pretend init was fine
    mocker.patch.object(rag_service, 'generate_embedding_for_query', AsyncMock(return_value=None))

    chunks = await retrieve_relevant_chunks("query", 5)
    assert chunks == []
    assert any("Failed to generate embedding for query. Cannot retrieve chunks." in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_vector_search_fails(
    reset_rag_service_state, mock_index_endpoint_client_fixture, mocker, caplog
):
    mocker.patch.object(rag_service, '_init_rag_dependencies_once', MagicMock())
    mocker.patch.object(rag_service, '_vertex_ai_initialized_rag_service', True)
    mocker.patch.object(rag_service, 'generate_embedding_for_query', AsyncMock(return_value=[0.1]*128)) # Dummy embedding

    mock_index_endpoint_client_fixture.find_neighbors_async.side_effect = Exception("Vector Search Error")

    chunks = await retrieve_relevant_chunks("query", 5)
    assert chunks == []
    assert any("Error retrieving neighbors from Vector Search: Vector Search Error" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_id_not_in_map(
    reset_rag_service_state, mock_gcs_client_fixture, mock_embedding_model_fixture, mock_index_endpoint_client_fixture, mocker, caplog
):
    # Init with a map that's missing an ID that will be returned by Vector Search
    sample_map = {"actual_id_1": {"text": "Text 1", "source": "Doc X"}}
    mock_blob = MagicMock(); mock_blob.exists.return_value = True
    mock_blob.download_as_string.return_value = json.dumps(sample_map).encode('utf-8')
    mock_gcs_client_fixture.bucket.return_value.blob.return_value = mock_blob

    mocker.patch.object(rag_service, 'generate_embedding_for_query', AsyncMock(return_value=[0.1]*128))

    mock_neighbor_known = MagicMock(); mock_neighbor_known.id = "actual_id_1"; mock_neighbor_known.distance = 0.7
    mock_neighbor_unknown = MagicMock(); mock_neighbor_unknown.id = "unknown_id_99"; mock_neighbor_unknown.distance = 0.6
    mock_index_endpoint_client_fixture.find_neighbors_async.return_value = [mock_neighbor_unknown, mock_neighbor_known]

    # Need to ensure _id_to_chunk_details_map is actually populated by the init logic.
    # The init is triggered by the first call to a RAG function if not initialized.
    # For this test, let's ensure it's pre-populated correctly after init.

    # Call retrieve_relevant_chunks, which will trigger init
    chunks = await retrieve_relevant_chunks("query", 2)

    assert len(chunks) == 1 # Only the known chunk should be returned
    assert chunks[0]["id"] == "actual_id_1"
    assert any("Chunk ID unknown_id_99 from Vector Search not found in local ID-to-chunk map. Skipping." in record.message for record in caplog.records)

```
