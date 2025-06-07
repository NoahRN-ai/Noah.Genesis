import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, call

from backend.app.main import app # FastAPI app instance
from backend.app.models.api_models import ChatRequest, ChatResponse, UserInfo
from backend.app.models.firestore_models import InteractionHistory, InteractionActor, UserRole
from backend.app.core.security import get_current_active_user

# Fixed UserInfo for testing
TEST_USER_INFO = UserInfo(
    user_id="test_user_123",
    email="test@example.com",
    role=UserRole.PATIENT,
    disabled=False
)

@pytest.fixture
def mock_save_interaction_fixture(mocker):
    # This mock will be used by the chat endpoint
    return mocker.patch('backend.app.api.v1.endpoints.chat.save_interaction', new_callable=AsyncMock)

@pytest.fixture
def mock_load_session_history_fixture(mocker):
    return mocker.patch('backend.app.api.v1.endpoints.chat.load_session_history', new_callable=AsyncMock)

@pytest.fixture
def mock_get_llm_response_fixture(mocker):
    return mocker.patch('backend.app.api.v1.endpoints.chat.get_llm_response', new_callable=AsyncMock)


@pytest.mark.asyncio
async def test_handle_chat_message_success(
    mock_save_interaction_fixture,
    mock_load_session_history_fixture,
    mock_get_llm_response_fixture
):
    # Override dependency for this test
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_INFO

    mock_load_session_history_fixture.return_value = [] # No previous history
    mock_get_llm_response_fixture.return_value = ("AI says hello!", None) # (text_response, tool_calls)

    # Mock return values for save_interaction if needed, otherwise just let it be called
    mock_save_interaction_fixture.return_value = MagicMock(spec=InteractionHistory)


    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "User says hi", "session_id": "session_abc"}
        )

    assert response.status_code == 200
    chat_response_data = response.json()
    assert chat_response_data["response"] == "AI says hello!"
    assert chat_response_data["session_id"] == "session_abc"

    # Assert load_session_history called
    mock_load_session_history_fixture.assert_called_once_with(session_id="session_abc")

    # Assert get_llm_response called
    mock_get_llm_response_fixture.assert_called_once()
    # Check args of get_llm_response: model_name, history, prompt
    llm_call_args = mock_get_llm_response_fixture.call_args[0]
    assert llm_call_args[1] == [] # history
    assert llm_call_args[2] == "User says hi" # prompt

    # Assert save_interaction was called twice
    assert mock_save_interaction_fixture.call_count == 2

    # Call 1: User message
    user_save_call = mock_save_interaction_fixture.call_args_list[0]
    assert user_save_call[0][0] == "session_abc" # session_id
    assert user_save_call[0][1] == TEST_USER_INFO.user_id # user_id
    assert user_save_call[0][2] == InteractionActor.USER # actor
    assert user_save_call[0][3] == "User says hi" # message_content

    # Call 2: AI message
    ai_save_call = mock_save_interaction_fixture.call_args_list[1]
    assert ai_save_call[0][0] == "session_abc"
    assert ai_save_call[0][1] == TEST_USER_INFO.user_id
    assert ai_save_call[0][2] == InteractionActor.AGENT
    assert ai_save_call[0][3] == "AI says hello!"

    # Clean up dependency override
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_handle_chat_message_llm_service_error(
    mock_save_interaction_fixture,
    mock_load_session_history_fixture,
    mock_get_llm_response_fixture
):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_INFO
    mock_load_session_history_fixture.return_value = []
    llm_error_message = "Error: LLM is down"
    mock_get_llm_response_fixture.return_value = (llm_error_message, None)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "User query", "session_id": "session_err"}
        )

    assert response.status_code == 200
    chat_response_data = response.json()
    assert chat_response_data["response"] == llm_error_message

    # Assert AI's error response was saved
    ai_save_call = mock_save_interaction_fixture.call_args_list[1] # Second call is AI
    assert ai_save_call[0][3] == llm_error_message # message_content for AI

    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_handle_chat_message_llm_service_exception(
    mock_load_session_history_fixture, # Still need to mock dependencies even if not directly used before exception
    mock_get_llm_response_fixture
):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_INFO
    mock_load_session_history_fixture.return_value = []
    mock_get_llm_response_fixture.side_effect = Exception("LLM exploded")

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "User query", "session_id": "session_ex"}
        )

    assert response.status_code == 503 # Service Unavailable as per endpoint logic
    # Optionally check response body if there's a standard error format

    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_handle_chat_message_history_load_error(
    mock_save_interaction_fixture,
    mock_load_session_history_fixture,
    mock_get_llm_response_fixture
):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_INFO
    mock_load_session_history_fixture.side_effect = Exception("Firestore connection error")
    mock_get_llm_response_fixture.return_value = ("AI response assuming no history", None)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "User says hi", "session_id": "session_hist_err"}
        )

    assert response.status_code == 200 # Endpoint handles this by proceeding with empty history
    chat_response_data = response.json()
    assert chat_response_data["response"] == "AI response assuming no history"

    # Assert get_llm_response was called with empty history
    llm_call_args = mock_get_llm_response_fixture.call_args[0]
    assert llm_call_args[1] == [] # history should be empty

    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_handle_chat_message_user_save_error_continues(
    mock_save_interaction_fixture,
    mock_load_session_history_fixture,
    mock_get_llm_response_fixture
):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER_INFO

    # First call (user save) raises error, second call (AI save) succeeds
    mock_save_interaction_fixture.side_effect = [
        Exception("Failed to save user message"),
        MagicMock(spec=InteractionHistory) # Successful save for AI
    ]
    mock_load_session_history_fixture.return_value = [] # Assume no history or history load succeeded
    mock_get_llm_response_fixture.return_value = ("AI got it anyway", None)

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "User's important message", "session_id": "session_user_save_err"}
        )

    assert response.status_code == 200 # Endpoint logs and continues
    chat_response_data = response.json()
    assert chat_response_data["response"] == "AI got it anyway"

    # Assert save_interaction was attempted twice
    assert mock_save_interaction_fixture.call_count == 2

    # Assert second save_interaction (AI) was called correctly
    ai_save_call = mock_save_interaction_fixture.call_args_list[1]
    assert ai_save_call[0][3] == "AI got it anyway"

    del app.dependency_overrides[get_current_active_user]

```
