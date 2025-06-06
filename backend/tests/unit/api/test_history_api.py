import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from backend.app.main import app # FastAPI app instance
from backend.app.models.api_models import UserInfo, SessionHistoryResponse, InteractionOutput
from backend.app.models.firestore_models import InteractionHistory, InteractionActor, UserRole
from backend.app.core.security import get_current_active_user

# Fixed UserInfo for testing
TEST_USER = UserInfo(
    user_id="test_user_hist_123",
    email="history_user@example.com",
    role=UserRole.PATIENT,
    disabled=False
)
FIXED_TIMESTAMP = datetime.now(timezone.utc)

@pytest.fixture
def mock_list_interaction_history_fixture(mocker):
    # Mock the service function where it's imported by the history endpoint module
    return mocker.patch('backend.app.api.v1.endpoints.history.list_interaction_history_for_session', new_callable=AsyncMock)

# --- Tests for GET /{session_id}/history ---

@pytest.mark.asyncio
async def test_get_session_history_success(mock_list_interaction_history_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER
    session_id = "session_valid_user"

    mock_interaction1 = InteractionHistory(
        id="ih1", session_id=session_id, user_id=TEST_USER.user_id, # User ID matches
        actor=InteractionActor.USER, message_content="Hello", timestamp=FIXED_TIMESTAMP,
        created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_interaction2 = InteractionHistory(
        id="ih2", session_id=session_id, user_id=TEST_USER.user_id, # User ID matches
        actor=InteractionActor.AGENT, message_content="Hi there", timestamp=FIXED_TIMESTAMP,
        created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_list_interaction_history_fixture.return_value = [mock_interaction1, mock_interaction2]

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/history/{session_id}/history?limit=10")

    assert response.status_code == 200
    response_data = SessionHistoryResponse(**response.json())
    assert response_data.session_id == session_id
    assert len(response_data.interactions) == 2
    assert response_data.interactions[0].actor == InteractionActor.USER.value
    assert response_data.interactions[0].message_content == "Hello"
    assert response_data.interactions[1].actor == InteractionActor.AGENT.value

    mock_list_interaction_history_fixture.assert_called_once_with(session_id=session_id, limit=10)
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_get_session_history_unauthorized_user_mismatch(mock_list_interaction_history_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER
    session_id = "session_other_user"

    # First item in history belongs to a different user
    mock_interaction_other_user = InteractionHistory(
        id="ih_other", session_id=session_id, user_id="other_user_id_789",
        actor=InteractionActor.USER, message_content="Secret message", timestamp=FIXED_TIMESTAMP,
        created_at=FIXED_TIMESTAMP, updated_at=FIXED_TIMESTAMP
    )
    mock_list_interaction_history_fixture.return_value = [mock_interaction_other_user]

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/history/{session_id}/history")

    assert response.status_code == 403 # Forbidden
    mock_list_interaction_history_fixture.assert_called_once_with(session_id=session_id, limit=20) # Default limit
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_get_session_history_empty(mock_list_interaction_history_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER
    session_id = "session_empty_hist"
    mock_list_interaction_history_fixture.return_value = [] # No history

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/history/{session_id}/history")

    assert response.status_code == 200
    response_data = SessionHistoryResponse(**response.json())
    assert response_data.session_id == session_id
    assert len(response_data.interactions) == 0

    mock_list_interaction_history_fixture.assert_called_once_with(session_id=session_id, limit=20)
    del app.dependency_overrides[get_current_active_user]


@pytest.mark.asyncio
async def test_get_session_history_service_error(mock_list_interaction_history_fixture):
    app.dependency_overrides[get_current_active_user] = lambda: TEST_USER
    session_id = "session_svc_error"
    mock_list_interaction_history_fixture.side_effect = Exception("Firestore is having a moment")

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/v1/history/{session_id}/history")

    assert response.status_code == 500
    # Optionally check error response body if standardized

    del app.dependency_overrides[get_current_active_user]

```
