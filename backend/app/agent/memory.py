import json
from typing import List, Optional, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from datetime import datetime

from backend.app.models.firestore_models import (
    PatientDataLog,
    InteractionActor,
    ToolCall as PydanticToolCallModel, # Intended: name, args, id
    ToolResponse as PydanticToolResponseModel, # Intended: tool_call_id, name, content
    InteractionHistoryCreate,
    InteractionHistory
)
from backend.app.services.firestore_service import (
    create_interaction_history_entry,
    list_interaction_history_for_session,
    list_patient_data_logs_for_user
)

async def save_interaction(
    session_id: str,
    user_id: str,
    actor: InteractionActor,
    message_content: str,
    tool_calls: Optional[List[PydanticToolCallModel]] = None,
    tool_responses: Optional[List[PydanticToolResponseModel]] = None
) -> InteractionHistory:
    """
    Saves a single interaction turn to Firestore.
    This includes user messages or agent responses, which may involve tool usage.
    """
    entry_data = InteractionHistoryCreate(
        session_id=session_id,
        user_id=user_id,
        actor=actor,
        message_content=message_content,
        tool_calls=tool_calls, # Assumes tool_calls are already List[PydanticToolCallModel]
        tool_responses=tool_responses # Assumes tool_responses are already List[PydanticToolResponseModel]
    )
    created_entry = await create_interaction_history_entry(entry_data)
    return created_entry

async def load_session_history(session_id: str, limit: int = 20) -> List[BaseMessage]:
    """
    Loads the N most recent interactions for a session and converts them to LangChain messages.

    Args:
        session_id: The ID of the session to load history for.
        limit: The maximum number of recent InteractionHistory documents to retrieve.

    Returns:
        A list of LangChain BaseMessage objects in chronological order (oldest of
        the retrieved recent messages first), ready for use as LLM context.
    """
    interaction_history_docs: List[InteractionHistory] = await list_interaction_history_for_session(
        session_id=session_id,
        limit=limit,
        order_by="timestamp",
        descending=True
    )
    interaction_history_docs.reverse()

    langchain_messages: List[BaseMessage] = []
    for entry in interaction_history_docs:
        if entry.actor == InteractionActor.USER:
            langchain_messages.append(HumanMessage(content=entry.message_content))
        elif entry.actor == InteractionActor.AGENT:
            lc_tool_calls_list = []
            if entry.tool_calls:
                for pydantic_tc in entry.tool_calls:
                    # Directly use fields from the refined PydanticToolCallModel
                    lc_tool_calls_list.append({
                        "name": pydantic_tc.name,
                        "args": pydantic_tc.args,
                        "id": pydantic_tc.id
                    })

            agent_message = AIMessage(
                content=entry.message_content,
                tool_calls=lc_tool_calls_list if lc_tool_calls_list else []
            )
            langchain_messages.append(agent_message)

            if entry.tool_responses:
                for pydantic_tr in entry.tool_responses:
                    # Directly use fields from the refined PydanticToolResponseModel
                    tool_output_content_str = pydantic_tr.content
                    if isinstance(pydantic_tr.content, dict):
                        tool_output_content_str = json.dumps(pydantic_tr.content)
                    elif not isinstance(pydantic_tr.content, str):
                        tool_output_content_str = str(pydantic_tr.content)

                    langchain_messages.append(ToolMessage(
                        content=tool_output_content_str,
                        tool_call_id=pydantic_tr.tool_call_id, # Directly from PydanticToolResponseModel
                        name=pydantic_tr.name # Directly from PydanticToolResponseModel
                    ))
    return langchain_messages


@tool
async def fetch_patient_data_logs_tool(patient_user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetches a list of patient data logs for a given user.

    Args:
        patient_user_id: The ID of the patient whose data logs are to be fetched.
        limit: The maximum number of log entries to retrieve. Defaults to 5.

    Returns:
        A list of dictionaries, where each dictionary represents a patient data log
        entry with selected fields (log_id, timestamp, data_type, content, source, created_at).
        Timestamps are formatted as ISO 8601 strings.
    """
    logs: List[PatientDataLog] = await list_patient_data_logs_for_user(
        user_id=patient_user_id,
        limit=limit,
        order_by="timestamp",
        descending=True
    )
    processed_logs = []
    for log in logs:
        processed_logs.append({
            "log_id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "data_type": log.data_type.value if log.data_type else None, # Assuming data_type is an Enum
            "content": log.content,
            "source": log.source,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    return processed_logs
