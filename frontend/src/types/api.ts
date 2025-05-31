```typescript
// Matches backend/app/models/api_models.py and firestore_models.py where appropriate

// --- General ---
export interface UserInfo {
  userId: string; // Firebase UID
  email?: string | null;
  displayName?: string | null;
  // role could be fetched from our UserProfile after auth
}

// --- Chat API ---
export interface ChatRequestPayload {
  user_query_text: string;
  user_voice_input_bytes?: string; // Base64 encoded string if sending bytes
  session_id?: string | null;
}

export interface ChatResponsePayload {
  agent_response_text: string;
  session_id: string;
  interaction_id: string;
}

// --- History API ---
// ToolCall and ToolResponse mirror firestore_models for display
export interface ToolCallData {
  name: string;
  args: Record<string, any>;
  id: string;
}

export interface ToolResponseData {
  tool_call_id: string;
  name: string;
  content: any;
}

export interface InteractionOutputData {
  interaction_id: string;
  session_id: string;
  user_id: string;
  timestamp: string; // ISO datetime string
  actor: 'user' | 'agent';
  message_content: string;
  tool_calls?: ToolCallData[] | null;
  tool_responses?: ToolResponseData[] | null;
}

export interface SessionHistoryResponsePayload {
  session_id: string;
  interactions: InteractionOutputData[];
}

// --- UserProfile API ---
export type UserRole = 'nurse' | 'patient';

export interface UserProfileData {
  user_id: string;
  role: UserRole;
  display_name?: string | null;
  preferences: Record<string, any>;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface UserProfileUpdatePayload {
  role?: UserRole | null;
  display_name?: string | null;
  preferences?: Record<string, any> | null;
}

// --- PatientDataLog API ---
export type PatientDataLogDataType =
  | "observation"
  | "symptom_report"
  | "llm_summary"
  | "nursing_note_draft"
  | "shift_handoff_draft"
  | "user_document";

export interface PatientDataLogCreatePayload {
  // target_patient_user_id is a query param in the API
  timestamp: string; // ISO datetime string
  data_type: PatientDataLogDataType;
  content: Record<string, any>;
  source?: string | null;
}

export interface PatientDataLogData {
  log_id: string;
  user_id: string; // Patient owner
  created_by_user_id: string; // User who submitted
  timestamp: string; // ISO datetime string for the event
  data_type: PatientDataLogDataType;
  content: Record<string, any>;
  source: string;
  created_at: string; // ISO datetime string for record creation
  updated_at: string; // ISO datetime string for record update
}

// Used by components to structure message display
export interface DisplayMessage {
  id: string; // interaction_id or a client-generated ID for local messages
  text: string;
  sender: 'user' | 'agent' | 'system'; // 'system' for status messages like 'typing' or errors
  timestamp?: Date; // Date object for easy formatting
  isTyping?: boolean; // For agent typing indicator
  tool_calls?: ToolCallData[] | null; // For displaying agent's intent to call tools
  // If we want to display tool results explicitly, add here or handle within agent message text
}
```
