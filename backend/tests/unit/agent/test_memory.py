import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import json

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage as LangChainToolMessage

from backend.app.models.firestore_models import (
    InteractionHistory,
    InteractionHistoryCreate,
    InteractionActor,
    ToolCall as PydanticToolCallModel,
    ToolResponse as PydanticToolResponseModel,
    PatientDataLog,
    DataType,
    UserRole # Though not directly used in memory.py, good for context if needed
)
from backend.app.agent.memory import (
    save_interaction,
    load_session_history,
    fetch_patient_data_logs_tool
)

# Fixed timestamp for testing
FIXED_NOW = datetime.now(timezone.utc)
A_BIT_AGO = FIXED_NOW - timedelta(minutes=5)

@pytest.fixture
def mock_create_ih_entry(mocker):
    return mocker.patch('backend.app.agent.memory.create_interaction_history_entry', new_callable=AsyncMock)

@pytest.fixture
def mock_list_ih_session(mocker):
    return mocker.patch('backend.app.agent.memory.list_interaction_history_for_session', new_callable=AsyncMock)

@pytest.fixture
def mock_list_patient_logs(mocker):
    return mocker.patch('backend.app.agent.memory.list_patient_data_logs_for_user', new_callable=AsyncMock)


# --- Tests for save_interaction ---

@pytest.mark.asyncio
async def test_save_interaction_success(mock_create_ih_entry):
    session_id = "session1"
    user_id = "user1"
    actor = InteractionActor.USER
    message_content = "Hello there!"

    # Mock the return value of the create_interaction_history_entry service function
    mock_created_entry = InteractionHistory(
        id="interaction_id_123",
        session_id=session_id,
        user_id=user_id,
        actor=actor,
        message_content=message_content,
        tool_calls=None,
        tool_responses=None,
        timestamp=FIXED_NOW,
        created_at=FIXED_NOW,
        updated_at=FIXED_NOW
    )
    mock_create_ih_entry.return_value = mock_created_entry

    result = await save_interaction(session_id, user_id, actor, message_content)

    mock_create_ih_entry.assert_called_once()
    call_args = mock_create_ih_entry.call_args[0][0] # Get the InteractionHistoryCreate object

    assert isinstance(call_args, InteractionHistoryCreate)
    assert call_args.session_id == session_id
    assert call_args.user_id == user_id
    assert call_args.actor == actor
    assert call_args.message_content == message_content
    assert call_args.tool_calls is None
    assert call_args.tool_responses is None

    assert result == mock_created_entry

@pytest.mark.asyncio
async def test_save_interaction_with_tools(mock_create_ih_entry):
    session_id = "session_tools"
    user_id = "user_tools"
    actor = InteractionActor.AGENT
    message_content = "Using tools."

    pydantic_tool_calls = [PydanticToolCallModel(id="tc1", name="get_weather", args={"location": "Paris"})]
    pydantic_tool_responses = [PydanticToolResponseModel(tool_call_id="tc1", name="get_weather", content={"temp": "20C"})]

    mock_created_entry = InteractionHistory(
        id="interaction_id_tools", session_id=session_id, user_id=user_id, actor=actor,
        message_content=message_content, tool_calls=pydantic_tool_calls, tool_responses=pydantic_tool_responses,
        timestamp=FIXED_NOW, created_at=FIXED_NOW, updated_at=FIXED_NOW
    )
    mock_create_ih_entry.return_value = mock_created_entry

    result = await save_interaction(session_id, user_id, actor, message_content, pydantic_tool_calls, pydantic_tool_responses)

    mock_create_ih_entry.assert_called_once()
    call_args = mock_create_ih_entry.call_args[0][0]

    assert call_args.tool_calls == pydantic_tool_calls
    assert call_args.tool_responses == pydantic_tool_responses
    assert result == mock_created_entry


# --- Tests for load_session_history ---

@pytest.mark.asyncio
async def test_load_session_history_success_various_messages(mock_list_ih_session):
    session_id = "session_various"
    user_id = "user_various"

    # Firestore returns newest first, so this is reverse chronological
    mock_db_entries = [
        InteractionHistory( # Agent response with tool call and tool response
            id="ih3", session_id=session_id, user_id=user_id, actor=InteractionActor.AGENT,
            message_content="Okay, I called the tool.",
            tool_calls=[PydanticToolCallModel(id="tool_xyz", name="query_db", args={"patient_id": "p1"})],
            tool_responses=[PydanticToolResponseModel(tool_call_id="tool_xyz", name="query_db", content={"result": "found"})],
            timestamp=FIXED_NOW, created_at=FIXED_NOW, updated_at=FIXED_NOW
        ),
        InteractionHistory( # User message that triggered the tool call
            id="ih2", session_id=session_id, user_id=user_id, actor=InteractionActor.USER,
            message_content="Can you check the database for patient p1?",
            timestamp=A_BIT_AGO, created_at=A_BIT_AGO, updated_at=A_BIT_AGO
        ),
         InteractionHistory( # Simple AI message
            id="ih1", session_id=session_id, user_id=user_id, actor=InteractionActor.AGENT,
            message_content="Hello! How can I help you today?",
            tool_calls=None, tool_responses=None,
            timestamp=A_BIT_AGO - timedelta(minutes=1), created_at=A_BIT_AGO, updated_at=A_BIT_AGO
        )
    ]
    mock_list_ih_session.return_value = mock_db_entries

    messages = await load_session_history(session_id)

    mock_list_ih_session.assert_called_once_with(session_id=session_id, limit=20, order_by="timestamp", descending=True)

    assert len(messages) == 4 # ih1 (AI), ih2 (Human), ih3 (AI), ih3_tool_response (Tool)

    # Chronological order (oldest first)
    assert isinstance(messages[0], AIMessage)
    assert messages[0].content == "Hello! How can I help you today?"
    assert not messages[0].tool_calls

    assert isinstance(messages[1], HumanMessage)
    assert messages[1].content == "Can you check the database for patient p1?"

    assert isinstance(messages[2], AIMessage)
    assert messages[2].content == "Okay, I called the tool."
    assert len(messages[2].tool_calls) == 1
    assert messages[2].tool_calls[0]["id"] == "tool_xyz"
    assert messages[2].tool_calls[0]["name"] == "query_db"
    assert messages[2].tool_calls[0]["args"] == {"patient_id": "p1"}

    assert isinstance(messages[3], LangChainToolMessage)
    assert messages[3].content == json.dumps({"result": "found"}) # ToolMessage content is stringified
    assert messages[3].tool_call_id == "tool_xyz"
    assert messages[3].name == "query_db"


@pytest.mark.asyncio
async def test_load_session_history_empty(mock_list_ih_session):
    session_id = "session_empty"
    mock_list_ih_session.return_value = []

    messages = await load_session_history(session_id)

    mock_list_ih_session.assert_called_once_with(session_id=session_id, limit=20, order_by="timestamp", descending=True)
    assert messages == []


# --- Tests for fetch_patient_data_logs_tool ---

@pytest.mark.asyncio
async def test_fetch_patient_data_logs_tool_success(mock_list_patient_logs):
    patient_user_id = "patient123"
    limit = 3

    mock_log_entries = [
        PatientDataLog(
            id="log1", user_id=patient_user_id, timestamp=FIXED_NOW,
            data_type=DataType.BLOOD_GLUCOSE, content={"value": 100, "unit": "mg/dL"},
            source="glucometer", created_at=FIXED_NOW, updated_at=FIXED_NOW, created_by_user_id=patient_user_id
        ),
        PatientDataLog(
            id="log2", user_id=patient_user_id, timestamp=A_BIT_AGO,
            data_type=DataType.BLOOD_PRESSURE, content={"systolic": 120, "diastolic": 80, "unit": "mmHg"},
            source="manual", created_at=A_BIT_AGO, updated_at=A_BIT_AGO, created_by_user_id=patient_user_id
        )
    ]
    mock_list_patient_logs.return_value = mock_log_entries

    # Note: fetch_patient_data_logs_tool is not async itself, but it calls an async function
    # The @tool decorator might make it awaitable if Langchain expects that.
    # For testing the core logic, we call it directly. If it were truly async due to @tool, this would need await.
    # Based on the provided snippet, it's an async def, so it should be awaited.
    processed_logs = await fetch_patient_data_logs_tool.ainvoke({"patient_user_id": patient_user_id, "limit": limit})
    # If testing the raw function without Langchain's tool wrapper:
    # processed_logs = await fetch_patient_data_logs_tool(patient_user_id=patient_user_id, limit=limit)


    mock_list_patient_logs.assert_called_once_with(
        user_id=patient_user_id, limit=limit, order_by="timestamp", descending=True
    )

    assert len(processed_logs) == 2

    log1_processed = processed_logs[0]
    assert log1_processed["log_id"] == "log1"
    assert log1_processed["timestamp"] == FIXED_NOW.isoformat()
    assert log1_processed["data_type"] == DataType.BLOOD_GLUCOSE.value
    assert log1_processed["content"] == {"value": 100, "unit": "mg/dL"}
    assert log1_processed["source"] == "glucometer"
    assert log1_processed["created_at"] == FIXED_NOW.isoformat()

    log2_processed = processed_logs[1]
    assert log2_processed["log_id"] == "log2"
    assert log2_processed["timestamp"] == A_BIT_AGO.isoformat()
    assert log2_processed["data_type"] == DataType.BLOOD_PRESSURE.value
    assert log2_processed["content"] == {"systolic": 120, "diastolic": 80, "unit": "mmHg"}
    assert log2_processed["source"] == "manual"
    assert log2_processed["created_at"] == A_BIT_AGO.isoformat()

@pytest.mark.asyncio
async def test_fetch_patient_data_logs_tool_empty(mock_list_patient_logs):
    patient_user_id = "patient_no_logs"
    mock_list_patient_logs.return_value = []

    processed_logs = await fetch_patient_data_logs_tool.ainvoke({"patient_user_id": patient_user_id})
    # Or: processed_logs = await fetch_patient_data_logs_tool(patient_user_id=patient_user_id)


    mock_list_patient_logs.assert_called_once_with(
        user_id=patient_user_id, limit=5, order_by="timestamp", descending=True # Default limit
    )
    assert processed_logs == []

```
