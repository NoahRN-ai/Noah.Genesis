import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Assuming google.api_core.exceptions might be raised
from google.api_core import exceptions as google_exceptions

# For constructing mock Vertex AI responses
from vertexai.generative_models._generative_models import (
    Candidate,
    Content,
    Part,
    FunctionCall,
    GenerationResponse
)


from backend.app.services import llm_service
from backend.app.services.llm_service import (
    get_llm_response,
    _convert_lc_messages_to_vertex_content,
    init_vertex_ai # To potentially mock its behavior if called
)

MODEL_NAME = "gemini-1.0-pro-001" # Example model name

@pytest.fixture(autouse=True)
def mock_vertex_init(mocker):
    """Auto-used fixture to mock vertexai.init."""
    mocker.patch('vertexai.init', return_value=None)

@pytest.fixture(autouse=True)
def set_vertex_initialized(mocker):
    """Auto-used fixture to set _vertex_ai_initialized to True by default."""
    mocker.patch.object(llm_service, '_vertex_ai_initialized', True)

@pytest.fixture
def mock_generative_model(mocker):
    """Mocks the GenerativeModel class."""
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content_async = AsyncMock()

    mock_model_class = mocker.patch('vertexai.generative_models.GenerativeModel')
    mock_model_class.return_value = mock_model_instance
    return mock_model_instance

# --- Tests for get_llm_response ---

@pytest.mark.asyncio
async def test_get_llm_response_success(mock_generative_model):
    expected_text = "This is a test response."
    mock_response_part = Part.from_text(expected_text)
    mock_candidate = Candidate(content=Content(parts=[mock_response_part]), finish_reason="STOP", safety_ratings=[])
    mock_generation_response = GenerationResponse(
        candidates=[mock_candidate],
        prompt_feedback=None,
        usage_metadata=GenerationResponse.UsageMetadata(prompt_token_count=10, candidates_token_count=5, total_token_count=15)
    )
    mock_generative_model.generate_content_async.return_value = mock_generation_response

    history = [HumanMessage(content="Hello")]
    prompt = "Tell me a joke"

    response_str, tool_calls = await get_llm_response(MODEL_NAME, history, prompt)

    assert response_str == expected_text
    assert tool_calls is None
    mock_generative_model.generate_content_async.assert_called_once()


@pytest.mark.asyncio
async def test_get_llm_response_no_candidates(mock_generative_model):
    mock_generation_response = GenerationResponse(
        candidates=[], # No candidates
        prompt_feedback=None,
        usage_metadata=GenerationResponse.UsageMetadata(prompt_token_count=0, candidates_token_count=0, total_token_count=0)
    )
    mock_generative_model.generate_content_async.return_value = mock_generation_response

    history = [HumanMessage(content="Hello")]
    prompt = "Some prompt"

    response_str, tool_calls = await get_llm_response(MODEL_NAME, history, prompt)

    assert "Error: No response candidates found." in response_str
    assert tool_calls is None

@pytest.mark.asyncio
async def test_get_llm_response_blocked_response(mock_generative_model):
    mock_candidate = Candidate(content=Content(parts=[]), finish_reason="SAFETY", safety_ratings=[]) # Blocked
    mock_generation_response = GenerationResponse(
        candidates=[mock_candidate],
        prompt_feedback=None,
        usage_metadata=GenerationResponse.UsageMetadata(prompt_token_count=10, candidates_token_count=0, total_token_count=10)
    )
    mock_generative_model.generate_content_async.return_value = mock_generation_response

    history = [HumanMessage(content="Hello")]
    prompt = "Risky prompt"

    response_str, tool_calls = await get_llm_response(MODEL_NAME, history, prompt)

    assert "Error: Response was blocked or had no content. Finish Reason: SAFETY" in response_str
    assert tool_calls is None


@pytest.mark.asyncio
async def test_get_llm_response_returns_function_call_only(mock_generative_model):
    func_call = FunctionCall(name="test_tool", args={"param": "value"})
    mock_response_part = Part.from_function_call(func_call)
    mock_candidate = Candidate(content=Content(parts=[mock_response_part]), finish_reason="STOP", safety_ratings=[])
    mock_generation_response = GenerationResponse(
        candidates=[mock_candidate],
        prompt_feedback=None,
        usage_metadata=GenerationResponse.UsageMetadata(prompt_token_count=10, candidates_token_count=5, total_token_count=15)
    )
    mock_generative_model.generate_content_async.return_value = mock_generation_response

    history = [HumanMessage(content="Call a tool")]
    prompt = "Use test_tool"

    response_str, tool_calls_list = await get_llm_response(MODEL_NAME, history, prompt)

    assert response_str == "" # Current logic returns empty string if only tool call
    assert tool_calls_list is not None
    assert len(tool_calls_list) == 1
    assert tool_calls_list[0].name == "test_tool"
    assert tool_calls_list[0].args == {"param": "value"}


@pytest.mark.asyncio
async def test_get_llm_response_vertex_ai_not_initialized(mocker):
    # Override the autouse fixture for this specific test
    mocker.patch.object(llm_service, '_vertex_ai_initialized', False)

    history = [HumanMessage(content="Hello")]
    prompt = "Any prompt"

    response_str, tool_calls = await get_llm_response(MODEL_NAME, history, prompt)

    assert response_str == "Error: Vertex AI not initialized. Call init_vertex_ai() first."
    assert tool_calls is None

@pytest.mark.asyncio
async def test_get_llm_response_handles_google_api_exception(mock_generative_model):
    mock_generative_model.generate_content_async.side_effect = google_exceptions.InvalidArgument("Test API error")

    history = [HumanMessage(content="Hello")]
    prompt = "Trigger error"

    response_str, tool_calls = await get_llm_response(MODEL_NAME, history, prompt)

    assert "An API error occurred: Test API error" in response_str
    assert tool_calls is None

# --- Tests for _convert_lc_messages_to_vertex_content ---

def test_convert_lc_messages_human_message():
    lc_messages = [HumanMessage(content="Hello from user")]
    vertex_content = _convert_lc_messages_to_vertex_content(lc_messages)
    assert len(vertex_content) == 1
    assert vertex_content[0].role == "user"
    assert len(vertex_content[0].parts) == 1
    assert vertex_content[0].parts[0].text == "Hello from user"

def test_convert_lc_messages_ai_message_text_only():
    lc_messages = [AIMessage(content="Hello from AI")]
    vertex_content = _convert_lc_messages_to_vertex_content(lc_messages)
    assert len(vertex_content) == 1
    assert vertex_content[0].role == "model"
    assert len(vertex_content[0].parts) == 1
    assert vertex_content[0].parts[0].text == "Hello from AI"

def test_convert_lc_messages_ai_message_with_tool_calls():
    tool_call_id = "tool_call_123"
    tool_name = "get_weather"
    tool_args = {"location": "Paris"}
    lc_messages = [AIMessage(
        content="", # Can be empty if only tool calls
        tool_calls=[{"id": tool_call_id, "name": tool_name, "args": tool_args}]
    )]
    vertex_content = _convert_lc_messages_to_vertex_content(lc_messages)
    assert len(vertex_content) == 1
    assert vertex_content[0].role == "model"
    assert len(vertex_content[0].parts) == 1
    assert vertex_content[0].parts[0].function_call is not None
    assert vertex_content[0].parts[0].function_call.name == tool_name
    assert vertex_content[0].parts[0].function_call.args == tool_args
    # Note: LangChain tool_calls are List[Dict], Vertex AI function_call is a single object.
    # The converter takes the first tool call if multiple are present in one AIMessage,
    # or would create multiple parts if the AIMessage content itself was a list of parts.
    # Current implementation seems to process the AIMessage.content (if text) and then tool_calls.
    # If AIMessage.content is empty and tool_calls exist, it makes one FunctionCall Part.

def test_convert_lc_messages_tool_message():
    tool_call_id = "tool_call_123"
    tool_name = "get_weather" # Not directly used by ToolMessage in Vertex format, but good for context
    tool_response_content = {"temperature": "20C", "conditions": "sunny"}
    lc_messages = [ToolMessage(
        content=str(tool_response_content), # ToolMessage content is typically string
        tool_call_id=tool_call_id,
        name=tool_name
    )]
    vertex_content = _convert_lc_messages_to_vertex_content(lc_messages)
    assert len(vertex_content) == 1
    assert vertex_content[0].role == "function" # Or "tool" depending on Vertex AI's exact expectation for ToolMessage
    assert len(vertex_content[0].parts) == 1
    assert vertex_content[0].parts[0].function_response is not None
    assert vertex_content[0].parts[0].function_response.name == tool_name # Name is used here
    assert vertex_content[0].parts[0].function_response.response == {"content": str(tool_response_content)}


def test_convert_lc_messages_empty_history_with_prompt():
    # This tests how _convert_lc_messages_to_vertex_content is used by get_llm_response
    # where `history` is empty but `prompt` is provided.
    # `get_llm_response` adds the current prompt as a HumanMessage.
    lc_messages = [HumanMessage(content="Current prompt")]
    vertex_content = _convert_lc_messages_to_vertex_content(lc_messages)
    assert len(vertex_content) == 1
    assert vertex_content[0].role == "user"
    assert vertex_content[0].parts[0].text == "Current prompt"

def test_convert_lc_messages_mixed_history():
    lc_messages = [
        HumanMessage(content="First user message"),
        AIMessage(content="First AI response"),
        ToolMessage(content="Tool output", tool_call_id="t1", name="tool1"),
        AIMessage(tool_calls=[{"id": "t2", "name": "tool2", "args": {}}]),
    ]
    vertex_content = _convert_lc_messages_to_vertex_content(lc_messages)
    assert len(vertex_content) == 4
    assert vertex_content[0].role == "user"
    assert vertex_content[1].role == "model"
    assert vertex_content[1].parts[0].text == "First AI response"
    assert vertex_content[2].role == "function"
    assert vertex_content[2].parts[0].function_response.name == "tool1"
    assert vertex_content[3].role == "model"
    assert vertex_content[3].parts[0].function_call.name == "tool2"
```
