import pytest
import httpx
import os
from unittest.mock import AsyncMock, MagicMock
from google.cloud import firestore_v1 as系数_firestore # For the verification client

from backend.app.main import app # FastAPI app instance
from backend.app.models.api_models import ChatRequest, ChatResponse, UserInfo
from backend.app.models.firestore_models import InteractionActor, UserRole
from backend.app.core.security import get_current_active_user

# Assumed to be set in the test environment (e.g., pyproject.toml or run script)
FIRESTORE_EMULATOR_HOST = os.environ.get("FIRESTORE_EMULATOR_HOST") # e.g., "localhost:8080"
FIRESTORE_PROJECT_ID = os.environ.get("FIRESTORE_PROJECT_ID", "test-project-id") # Dummy project ID

# Skip all tests in this file if the emulator is not configured
if not FIRESTORE_EMULATOR_HOST:
    pytest.skip("FIRESTORE_EMULATOR_HOST not set, skipping integration tests", allow_module_level=True)

# Fixed UserInfo for testing
TEST_USER = UserInfo(
    user_id="int_test_user_123",
    email="int_test@example.com",
    role=UserRole.PATIENT,
    disabled=False
)

@pytest.fixture(scope="module")
def firestore_emulator_verification_client():
    """Provides a Firestore client specifically for test verification, connected to the emulator."""
    # For the verification client, we explicitly point to the emulator
    # The application's client will pick up FIRESTORE_EMULATOR_HOST automatically
    cred_mock = MagicMock() # Mock credentials for local emulator client
    client =系数_firestore.AsyncClient(project=FIRESTORE_PROJECT_ID, credentials=cred_mock)
    return client

@pytest.fixture(autouse=True)
async def clear_emulator_firestore():
    """Clears all data from the Firestore emulator before each test."""
    if not FIRESTORE_EMULATOR_HOST: # Should already be skipped by module-level skip, but as a safeguard
        return

    clear_url = f"http://{FIRESTORE_EMULATOR_HOST}/emulator/v1/projects/{FIRESTORE_PROJECT_ID}/databases/(default)/documents"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(clear_url)
            response.raise_for_status() # Raise an exception for bad status codes
    except httpx.RequestError as e:
        pytest.fail(f"Failed to connect to Firestore emulator to clear data: {e}. Is it running at {FIRESTORE_EMULATOR_HOST}?")
    except httpx.HTTPStatusError as e:
        # It's okay if it's 404 (no data to delete) or 200 (data deleted)
        if e.response.status_code not in [200, 404]:
             pytest.fail(f"Failed to clear Firestore emulator data, status {e.response.status_code}: {e.response.text}")


@pytest.fixture
def mock_get_llm_response_integration(mocker):
    """Mocks get_llm_response at the chat endpoint module level."""
    # Path should be where it's *used*
    return mocker.patch('backend.app.api.v1.endpoints.chat.get_llm_response', new_callable=AsyncMock)


@pytest.mark.asyncio
async def test_chat_message_creates_history_in_emulator(
    firestore_emulator_verification_client, # Client for verification
    mock_get_llm_response_integration
):
    # 1. Setup: Override auth and mock LLM
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER

    user_id = TEST_USER.user_id
    session_id = "integration_session_001"
    user_query_text = "Hello, this is an integration test query."
    ai_response_text = "Acknowledged: integration test query."

    mock_get_llm_response_integration.return_value = (ai_response_text, None) # (text, tool_calls)

    # 2. Make API call
    request_payload = ChatRequest(message=user_query_text, session_id=session_id)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json=request_payload.model_dump())

    # 3. Assert API response
    assert response.status_code == 200
    chat_response = ChatResponse(**response.json())
    assert chat_response.response == ai_response_text
    assert chat_response.session_id == session_id

    # 4. Verify data in Firestore Emulator
    history_collection_ref = firestore_emulator_verification_client.collection("interaction_history")
    query = history_collection_ref.where("session_id", "==", session_id).order_by("timestamp")

    docs = []
    async for doc in query.stream():
        docs.append(doc.to_dict())

    assert len(docs) == 2, "Should find two interaction history documents"

    # Document 1: User message
    user_message_doc = docs[0]
    assert user_message_doc["user_id"] == user_id
    assert user_message_doc["session_id"] == session_id
    assert user_message_doc["actor"] == InteractionActor.USER.value
    assert user_message_doc["message_content"] == user_query_text
    assert "timestamp" in user_message_doc

    # Document 2: AI message
    ai_message_doc = docs[1]
    assert ai_message_doc["user_id"] == user_id
    assert ai_message_doc["session_id"] == session_id
    assert ai_message_doc["actor"] == InteractionActor.AGENT.value
    assert ai_message_doc["message_content"] == ai_response_text
    assert "timestamp" in ai_message_doc
    assert ai_message_doc["timestamp"] >= user_message_doc["timestamp"] # AI msg should be later or same

    # Clean up dependency override
    del app.dependency_overrides[get_current_active_user]

```
