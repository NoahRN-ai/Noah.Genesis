import datetime
import json

# --- Mock Data for Simulation ---
MOCK_PATIENT_PROFILES_STORE = {
    "patient001": {
        "patientId": "patient001", "name": "John Doe", "dob": "1980-01-01",
        "mrn": "MRN12345", "allergies": ["Penicillin"],
        "principalProblem": "Pneumonia", "admissionDate": "2024-07-20T10:00:00Z"
    },
    "patient002": {
        "patientId": "patient002", "name": "Jane Smith", "dob": "1975-05-15",
        "mrn": "MRN67890", "allergies": ["None known"],
        "principalProblem": "CHF Exacerbation", "admissionDate": "2024-07-19T15:30:00Z"
    }
}

MOCK_PATIENT_EVENTS_STORE = {
    "patient001": [
        {"timestamp": "2024-07-21T08:00:00Z", "event_type": "vital_sign", "details": {"sign_name": "Temperature", "value": 38.5, "unit": "C"}},
        {"timestamp": "2024-07-21T09:15:00Z", "event_type": "observation", "details": {"text_observation": "Patient coughing frequently."}}
    ],
    "patient002": [
        {"timestamp": "2024-07-21T07:30:00Z", "event_type": "vital_sign", "details": {"sign_name": "Heart Rate", "value": 95, "unit": "bpm"}},
        {"timestamp": "2024-07-21T08:45:00Z", "event_type": "intervention", "details": {"description": "Administered Furosemide 20mg IV."}}
    ]
}

MOCK_TODO_LIST_STORE = [] # Simulates the MOCK_TASKS_DB from todo_list_manager

# --- Agent Interface Stubs ---

def call_data_aggregation_firestore(patient_id: str) -> dict:
    """
    Simulates fetching patient profile from Firestore.
    (Corresponds to Step 1 / noah_foundational_data_aggregation_mvp)
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Calling Data Aggregation (Firestore) for patient_id: {patient_id}")
    profile = MOCK_PATIENT_PROFILES_STORE.get(patient_id)
    if profile:
        print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Found profile: {json.dumps(profile)}")
        return {"status": "success", "data": profile}
    else:
        print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Profile not found for patient_id: {patient_id}")
        return {"status": "error", "message": "Patient profile not found"}

def call_data_aggregation_alloydb_events(patient_id: str, filters: dict = None) -> list:
    """
    Simulates fetching events from AlloyDB.
    (Corresponds to Step 1 & 6 / noah_foundational_data_aggregation_mvp, noah_shift_events_log_display_mvp)
    Basic filtering simulation for demonstration.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Calling Data Aggregation (AlloyDB Events) for patient_id: {patient_id}, filters: {filters}")
    events = MOCK_PATIENT_EVENTS_STORE.get(patient_id, [])

    # Simplified filter simulation (only by event_type for this stub)
    if filters and "event_type" in filters:
        events = [event for event in events if event.get("event_type") == filters["event_type"]]

    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Found {len(events)} events.")
    return {"status": "success", "data": events}


def call_patient_summary_agent(patient_profile: dict, patient_events: list, summary_type: str) -> str:
    """
    Simulates calling the patient summary agent.
    (Corresponds to Step 2 / noah_patient_summary_agent_mvp)
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Calling Patient Summary Agent for patient: {patient_profile.get('name', 'N/A')}, summary_type: {summary_type}")
    # In a real scenario, this would involve RAG and LLM calls.
    mock_summary = (
        f"--- Mock {summary_type.replace('_', ' ').title()} for {patient_profile.get('name', 'N/A')} ---\n"
        f"Patient admitted for {patient_profile.get('principalProblem', 'N/A')}.\n"
        f"Key Events ({len(patient_events)}): {', '.join([evt.get('event_type') for evt in patient_events[:2]])}...\n"
        f"Allergies: {', '.join(patient_profile.get('allergies', ['None']))}.\n"
        f"This is a simulated summary based on available data."
    )
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Generated summary: {mock_summary[:100]}...") # Print snippet
    return {"status": "success", "summary_text": mock_summary}

def call_shift_event_capture_agent(patient_id: str, event_details: dict, event_type: str) -> dict:
    """
    Simulates logging an event via the shift event capture agent.
    (Corresponds to Step 3 / noah_shift_event_capture_agent_mvp)
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Calling Shift Event Capture Agent for patient_id: {patient_id}")
    print(f"  Event Type: {event_type}, Details: {json.dumps(event_details)}")

    # Simulate adding to a log or a temporary store if needed for complex workflows
    mock_event_log_entry = {
        "log_id": f"log_{datetime.datetime.utcnow().timestamp()}",
        "patient_id": patient_id,
        "event_type": event_type,
        "details": event_details,
        "status": "successfully_logged_mock"
    }
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Event (simulated) logged: {mock_event_log_entry['log_id']}")
    return {"status": "success", "log_entry": mock_event_log_entry}

def call_todo_list_manager(action: str, payload: dict) -> dict:
    """
    Simulates interacting with the To-Do list manager.
    (Corresponds to Step 7 / noah_plan_of_care_todo_mvp)
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Calling To-Do List Manager. Action: {action}, Payload: {json.dumps(payload)}")

    if action == "add_task":
        task_id = f"task_{datetime.datetime.utcnow().timestamp()}"
        new_task = {
            "task_id": task_id,
            "description": payload.get("description"),
            "priority": payload.get("priority"),
            "status": "Pending",
            "patient_id": payload.get("patient_id", "general"),
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        MOCK_TODO_LIST_STORE.append(new_task) # Add to the mock store
        print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Task added: {task_id}")
        return {"status": "success", "task": new_task}

    elif action == "get_all_tasks":
        patient_id_filter = payload.get("patient_id")
        tasks_to_return = MOCK_TODO_LIST_STORE
        if patient_id_filter:
             tasks_to_return = [
                task for task in MOCK_TODO_LIST_STORE
                if task.get("patient_id") == patient_id_filter or task.get("patient_id") == "general"
            ]
        print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Returning {len(tasks_to_return)} tasks.")
        return {"status": "success", "tasks": list(tasks_to_return)} # Return a copy

    elif action == "update_task_status":
        task_id = payload.get("task_id")
        new_status = payload.get("new_status")
        for task in MOCK_TODO_LIST_STORE:
            if task["task_id"] == task_id:
                task["status"] = new_status
                task["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Task {task_id} status updated to {new_status}.")
                return {"status": "success", "task": task}
        print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Task {task_id} not found for update.")
        return {"status": "error", "message": f"Task {task_id} not found"}

    else:
        print(f"[{datetime.datetime.utcnow().isoformat()}] STUB: Unknown action '{action}' for To-Do List Manager.")
        return {"status": "error", "message": f"Unknown action: {action}"}

if __name__ == "__main__":
    print("--- Agent Interface Stubs Demo ---")

    print("\n1. Testing Firestore Profile Fetch:")
    call_data_aggregation_firestore("patient001")
    call_data_aggregation_firestore("patient_nonexistent")

    print("\n2. Testing AlloyDB Events Fetch:")
    call_data_aggregation_alloydb_events("patient001")
    call_data_aggregation_alloydb_events("patient002", filters={"event_type": "intervention"})

    print("\n3. Testing Patient Summary Agent:")
    profile_data = MOCK_PATIENT_PROFILES_STORE.get("patient001", {})
    events_data = MOCK_PATIENT_EVENTS_STORE.get("patient001", [])
    call_patient_summary_agent(profile_data, events_data, summary_type="daily_update")

    print("\n4. Testing Shift Event Capture Agent:")
    call_shift_event_capture_agent("patient002", event_details={"text_observation": "Patient seems anxious."}, event_type="observation")

    print("\n5. Testing To-Do List Manager:")
    call_todo_list_manager(action="add_task", payload={"description": "Check vital signs Q4H", "priority": "High", "patient_id": "patient001"})
    call_todo_list_manager(action="add_task", payload={"description": "Order more supplies", "priority": "Medium", "patient_id": "general"})
    all_tasks_response = call_todo_list_manager(action="get_all_tasks", payload={})
    if all_tasks_response.get('tasks'):
        first_task_id = all_tasks_response['tasks'][0]['task_id']
        call_todo_list_manager(action="update_task_status", payload={"task_id": first_task_id, "new_status": "Completed"})

    call_todo_list_manager(action="get_all_tasks", payload={"patient_id": "patient001"})


    print("\n--- Demo Completed ---")
