from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum
import uuid # Added import

# --- Utility ---
def utcnow():
    return datetime.now(timezone.utc)

# Utility function for default tool call ID
def generate_default_tool_call_id():
    return str(uuid.uuid4())

# --- UserProfile ---
class UserRole(str, Enum):
    NURSE = "nurse"
    PATIENT = "patient"

class UserProfileBase(BaseModel):
    role: UserRole
    display_name: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    # created_at and updated_at will be managed by the service layer on write
    # to ensure they reflect actual DB transaction times more accurately,
    # or can be added here with default_factory=utcnow if preferred for model state.
    # For consistency, making them server-set upon write seems better.

class UserProfileCreate(UserProfileBase):
    pass # All fields from Base are relevant for creation initially

class UserProfileUpdate(BaseModel): # Allows partial updates
    role: Optional[UserRole] = None
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UserProfile(UserProfileBase): # Represents a UserProfile document read from DB
    user_id: str # Document ID
    created_at: datetime
    updated_at: datetime


# --- PatientDataLog ---
class PatientDataLogDataType(str, Enum):
    OBSERVATION = "observation"
    SYMPTOM_REPORT = "symptom_report"
    LLM_SUMMARY = "llm_summary"
    NURSING_NOTE_DRAFT = "nursing_note_draft"
    SHIFT_HANDOFF_DRAFT = "shift_handoff_draft"
    USER_DOCUMENT = "user_document" # E.g. patient uploaded document text

class PatientDataLogBase(BaseModel):
    user_id: str # Patient who owns the data
    created_by_user_id: str # User who entered the data (can be self or nurse)
    timestamp: datetime # Timestamp the data pertains to (e.g., observation time)
    data_type: PatientDataLogDataType
    content: Dict[str, Any] = Field(default_factory=dict) # Flexible content structure
    source: str = "Noah.Genesis_MVP"

class PatientDataLogCreate(PatientDataLogBase):
    pass

class PatientDataLogUpdate(BaseModel): # Allows partial updates
    # user_id and created_by_user_id are typically not updatable for a log entry
    timestamp: Optional[datetime] = None
    data_type: Optional[PatientDataLogDataType] = None
    content: Optional[Dict[str, Any]] = None
    source: Optional[str] = None

class PatientDataLog(PatientDataLogBase): # Represents a PatientDataLog document read from DB
    log_id: str # Document ID
    created_at: datetime # Timestamp of record creation in DB
    updated_at: datetime # Timestamp of last update in DB


# --- InteractionHistory ---
class InteractionActor(str, Enum):
    USER = "user"
    AGENT = "agent"

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]
    id: str = Field(default_factory=generate_default_tool_call_id)

class ToolResponse(BaseModel):
    tool_call_id: str # Corresponds to the 'id' of the ToolCall it's responding to
    name: str # The name of the tool that was called
    content: Any # The output/content from the tool execution

class InteractionHistoryBase(BaseModel):
    session_id: str
    user_id: str
    actor: InteractionActor
    message_content: str
    tool_calls: Optional[List[ToolCall]] = None # Verified: Uses updated ToolCall
    tool_responses: Optional[List[ToolResponse]] = None # Verified: Uses updated ToolResponse
    # timestamp will be managed by the service layer for accuracy on write

class InteractionHistoryCreate(InteractionHistoryBase):
    pass

class InteractionHistoryUpdate(BaseModel): # Interactions are typically immutable, but if edits were allowed:
    message_content: Optional[str] = None
    # tool_calls and tool_responses are usually part of the initial record

class InteractionHistory(InteractionHistoryBase): # Represents an InteractionHistory document read from DB
    interaction_id: str # Document ID
    timestamp: datetime # Timestamp of when the interaction occurred/was logged
