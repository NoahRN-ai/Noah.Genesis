from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import base models from firestore_models to ensure consistency where applicable
# and to reference enums or shared structures.
from .firestore_models import (
    UserRole, PatientDataLogDataType, InteractionActor,
    ToolCall as FirestoreToolCall,
    ToolResponse as FirestoreToolResponse
)

# --- Chat API Models ---
class ChatRequest(BaseModel):
    user_query_text: str
    user_voice_input_bytes: Optional[bytes] = None # Not used directly by LLM yet, for STT later
    session_id: Optional[str] = None # Client can manage session IDs, or server can generate

class ChatResponse(BaseModel):
    agent_response_text: str
    session_id: str
    interaction_id: str # ID of the agent's response InteractionHistory entry
    # generated_data: Optional[Dict[str, Any]] = None # Placeholder for future structured outputs

# --- History API Models ---
class InteractionOutput(BaseModel): # API representation of an interaction
    interaction_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    actor: InteractionActor
    message_content: str
    tool_calls: Optional[List[FirestoreToolCall]] = None # Re-using Firestore Pydantic model for structure
    tool_responses: Optional[List[FirestoreToolResponse]] = None # Re-using Firestore Pydantic model for structure

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "interaction_id": "interaction_xyz",
                "session_id": "session_abc",
                "user_id": "user_123",
                "timestamp": "2025-07-04T10:30:00Z",
                "actor": "user",
                "message_content": "Hello there!",
            }]
        }
    }

class SessionHistoryResponse(BaseModel):
    session_id: str
    interactions: List[InteractionOutput]
    # Add pagination tokens if implementing full cursor-based pagination later
    # next_page_token: Optional[str] = None


# --- PatientDataLog API Models ---
class PatientDataLogCreateInput(BaseModel):
    # user_id for whom the data is logged is now a query parameter in the endpoint for clarity.
    # created_by_user_id will be the authenticated user.
    timestamp: datetime # Timestamp the data pertains to
    data_type: PatientDataLogDataType
    content: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = Field(default="Noah.Genesis_MVP", examples=["Nurse Manual Entry", "Patient App Input"])

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "timestamp": "2025-07-04T09:00:00Z",
                "data_type": "observation",
                "content": {"blood_pressure": "120/80", "heart_rate": 70},
                "source": "Manual Nurse Input"
            }]
        }
    }

class PatientDataLogResponse(BaseModel): # Based on FirestorePatientDataLog structure
    log_id: str
    user_id: str
    created_by_user_id: str
    timestamp: datetime
    data_type: PatientDataLogDataType
    content: Dict[str, Any]
    source: str
    created_at: datetime # Record creation time
    updated_at: datetime # Record update time

    model_config = { # Allow ORM mode to easily convert from Pydantic model instances from service
        "from_attributes": True
    }


# --- UserProfile API Models ---
class UserProfileUpdateInput(BaseModel): # Based on FirestoreUserProfileUpdate structure
    role: Optional[UserRole] = None
    display_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "display_name": "Nurse Jane Doe",
                "preferences": {"summary_length": "concise"}
            }]
        }
    }

class UserProfileResponse(BaseModel): # Based on FirestoreUserProfile structure
    user_id: str
    role: UserRole
    display_name: Optional[str] = None
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }
