import datetime
import json
import os
import sys

# --- Attempt to import actual agent functionalities ---
# This allows agent_interfaces.py to act as a true facade if possible,
# otherwise it falls back to its own simpler stubs.

# Path setup - assuming all MVP directories are siblings
current_script_dir = os.path.dirname(os.path.realpath(__file__))
project_root = os.path.dirname(
    current_script_dir
)  # Assuming this script is in noah_agent_orchestration_groundwork

# Add sibling MVP directories to sys.path
mvp_dirs = [
    "noah_foundational_data_aggregation_mvp",  # Though this one doesn't have callable Python functions in the same way
    "noah_patient_summary_agent_mvp",
    "noah_shift_event_capture_agent_mvp",
    "noah_shift_events_log_display_mvp",
    "noah_plan_of_care_todo_mvp",
]
for mvp_dir in mvp_dirs:
    path_to_add = os.path.join(project_root, mvp_dir)
    if path_to_add not in sys.path:
        sys.path.insert(0, path_to_add)

# Try importing specific functions/data stores
try:
    from patient_summary_agent import (
        MOCK_PATIENT_PROFILES as PSA_PROFILES,  # From patient_summary_agent
    )
    from patient_summary_agent import (
        generate_summary_with_llm as psa_generate_summary,  # From patient_summary_agent
    )
    from patient_summary_agent import (
        get_mock_event_logs as psa_get_event_logs,  # From patient_summary_agent (for context)
    )
    from patient_summary_agent import (
        get_mock_patient_data as psa_get_profile,  # From patient_summary_agent
    )

    IMPORTED_PSA = True
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported from noah_patient_summary_agent_mvp."
    )
except ImportError as e:
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] WARN: Failed to import from noah_patient_summary_agent_mvp: {e}. Using local stubs for patient summary."
    )
    IMPORTED_PSA = False
    PSA_PROFILES = {  # Local fallback
        "patient001": {
            "patientId": "patient001",
            "name": "John Doe (Local Orchestration Fallback)",
            "principalProblem": "Pneumonia",
            "allergies": ["None"],
        },
        "patient002": {
            "patientId": "patient002",
            "name": "Jane Smith (Local Orchestration Fallback)",
            "principalProblem": "CHF",
            "allergies": ["Penicillin"],
        },
    }


try:
    from shift_event_capture import (
        SHARED_MOCK_EVENTS_DB as SECA_SHARED_EVENTS,  # From shift_event_capture
    )
    from shift_event_capture import (
        log_event as seca_log_event,  # From shift_event_capture
    )

    IMPORTED_SECA = True
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported from noah_shift_event_capture_agent_mvp."
    )
except ImportError as e:
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] WARN: Failed to import from noah_shift_event_capture_agent_mvp: {e}. Using local stubs for event capture."
    )
    IMPORTED_SECA = False
    SECA_SHARED_EVENTS = {}  # Local fallback


try:
    from events_log_data_prep import (
        get_mock_shift_events as eldp_get_events,  # From events_log_data_prep
    )

    IMPORTED_ELDP = True
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported from noah_shift_events_log_display_mvp."
    )
except ImportError as e:
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] WARN: Failed to import from noah_shift_events_log_display_mvp: {e}. Using local stubs for event fetching."
    )
    IMPORTED_ELDP = False


try:
    from todo_list_manager import (
        MOCK_TASKS_DB as TLM_TASKS_DB,  # For direct inspection if needed
    )
    from todo_list_manager import add_task as tlm_add_task
    from todo_list_manager import get_all_tasks as tlm_get_all_tasks
    from todo_list_manager import update_task_status as tlm_update_task_status

    IMPORTED_TLM = True
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported from noah_plan_of_care_todo_mvp."
    )
except ImportError as e:
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] WARN: Failed to import from noah_plan_of_care_todo_mvp: {e}. Using local stubs for ToDo manager."
    )
    IMPORTED_TLM = False
    TLM_TASKS_DB = []  # Local fallback


# --- Agent Interface Stubs (now acting as a Facade layer) ---


def call_data_aggregation_firestore(patient_id: str) -> dict:
    """Fetches patient profile. Uses Patient Summary Agent's mock data if available."""
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Calling Data Aggregation (Firestore) for patient_id: {patient_id}"
    )
    if IMPORTED_PSA:
        # psa_get_profile is actually direct dict access in the original script
        profile = PSA_PROFILES.get(patient_id)
    else:
        profile = PSA_PROFILES.get(patient_id)  # Uses local fallback PSA_PROFILES

    if profile:
        print(f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Found profile.")
        return {"status": "success", "data": profile}
    else:
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Profile not found for patient_id: {patient_id}"
        )
        return {"status": "error", "message": "Patient profile not found"}


def call_data_aggregation_alloydb_events(patient_id: str, filters: dict = None) -> dict:
    """Fetches events. Uses Events Log Display Prep's function, which reads from Shift Event Capture's shared store."""
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Calling Data Aggregation (AlloyDB Events) for patient_id: {patient_id}, filters: {filters}"
    )
    if IMPORTED_ELDP:
        events = eldp_get_events(
            patient_id, filter_criteria=filters
        )  # This function returns the list directly
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Found {len(events)} events via events_log_data_prep."
        )
        return {"status": "success", "data": events}
    else:
        # Fallback to a very simple local mock if ELDP didn't import
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] FACADE_FALLBACK: Using local event store for patient_id: {patient_id}."
        )
        events = SECA_SHARED_EVENTS.get(
            patient_id, []
        )  # Access local fallback of SECA_SHARED_EVENTS
        if filters and "event_type" in filters:  # Minimal filtering for fallback
            events = [
                event
                for event in events
                if event.get("event_type") == filters["event_type"]
            ]
        return {"status": "success", "data": events}


def call_patient_summary_agent(
    patient_profile: dict, patient_events: list, summary_type: str
) -> dict:
    """Calls the patient summary agent's core logic if available."""
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Calling Patient Summary Agent for patient: {patient_profile.get('name', 'N/A')}, summary_type: {summary_type}"
    )
    if IMPORTED_PSA:
        # The imported psa_generate_summary needs context_data.
        # The RAG query part is embedded in patient_summary_agent.py's generate_summary_with_llm
        # via query_vertex_ai_search. For this facade, we assume that internal call happens.
        # We'd need to ensure the MOCK_CLINICAL_KB is available to the imported function.
        # For now, let's assume `psa_generate_summary` can access its own clinical KB.
        # The `psa_query_vertex_ai_search` is called *inside* `psa_generate_summary_with_llm` in the original script,
        # so we just prepare the main inputs for `psa_generate_summary`.

        # Construct context_data as expected by the imported function
        # We might need a simplified RAG call here or assume the LLM stub handles it.
        # For this refactor, `psa_generate_summary` uses its own `query_vertex_ai_search`
        context_data = {
            "patient_profile": patient_profile,
            "event_logs": patient_events,
            "rag_results": [],  # Or call `psa_query_vertex_ai_search` if we want to be more explicit
        }
        summary_text = psa_generate_summary(context_data, summary_type)
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Summary generated via patient_summary_agent."
        )
        return {"status": "success", "summary_text": summary_text}
    else:
        # Fallback to original simpler stub if import failed
        mock_summary = f"--- Mock Fallback {summary_type} for {patient_profile.get('name', 'N/A')} ---\nEvents: {len(patient_events)}"
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] FACADE_FALLBACK: Generated local summary."
        )
        return {"status": "success", "summary_text": mock_summary}


def call_shift_event_capture_agent(
    patient_id: str, event_details: dict, event_type: str, source_override: str = None
) -> dict:
    """Logs an event using the shift event capture agent's core logic if available."""
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Calling Shift Event Capture Agent for patient_id: {patient_id}"
    )
    if IMPORTED_SECA:
        # seca_log_event is the core function from shift_event_capture.py
        # It handles adding timestamp, validation, and storing to SHARED_MOCK_EVENTS_DB
        logged_event_data = seca_log_event(
            patient_id,
            event_type,
            event_details,
            source_override=source_override,
            validate=True,
        )
        if logged_event_data:  # It returns the event data upon successful logging (or None if validation fails)
            print(
                f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Event logged via shift_event_capture_agent. Event ID (from shared store): {logged_event_data.get('event_id')}"
            )
            return {"status": "success", "log_entry": logged_event_data}
        else:
            print(
                f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Event logging failed via shift_event_capture_agent (e.g. validation)."
            )
            return {
                "status": "error",
                "message": "Event logging failed in shift_event_capture_agent",
            }
    else:
        # Fallback
        log_id = f"log_fallback_{datetime.datetime.utcnow().timestamp()}"
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] FACADE_FALLBACK: Event {log_id} (simulated local log)."
        )
        # Manually add to local SECA_SHARED_EVENTS if needed for fallback testing consistency
        fallback_event = {
            "event_id": log_id,
            "patient_id": patient_id,
            "event_type": event_type,
            "details": event_details,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        if patient_id not in SECA_SHARED_EVENTS:
            SECA_SHARED_EVENTS[patient_id] = []
        SECA_SHARED_EVENTS[patient_id].append(fallback_event)
        return {
            "status": "success",
            "log_entry": {
                "log_id": log_id,
                "status": "successfully_logged_mock_fallback",
            },
        }


def call_todo_list_manager(action: str, payload: dict) -> dict:
    """Interacts with the To-Do list manager's core logic if available."""
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] FACADE: Calling To-Do List Manager. Action: {action}"
    )
    if IMPORTED_TLM:
        if action == "add_task":
            # `tlm_add_task` expects description, priority, and optionally patient_id
            task = tlm_add_task(
                description=payload.get("description"),
                priority=payload.get("priority"),
                patient_id=payload.get("patient_id", "general"),
            )
            return {"status": "success", "task": task}
        elif action == "get_all_tasks":
            tasks = tlm_get_all_tasks(patient_id_filter=payload.get("patient_id"))
            return {"status": "success", "tasks": tasks}
        elif action == "update_task_status":
            task = tlm_update_task_status(
                payload.get("task_id"), payload.get("new_status")
            )
            if task:
                return {"status": "success", "task": task}
            else:
                return {
                    "status": "error",
                    "message": f"Task {payload.get('task_id')} not found or update failed",
                }
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    else:
        # Fallback
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] FACADE_FALLBACK: Using local ToDo store for action: {action}."
        )
        if action == "add_task":
            task_id = f"task_fallback_{datetime.datetime.utcnow().timestamp()}"
            new_task = {"task_id": task_id, **payload, "status": "Pending"}
            TLM_TASKS_DB.append(new_task)
            return {"status": "success", "task": new_task}
        elif action == "get_all_tasks":
            return {"status": "success", "tasks": list(TLM_TASKS_DB)}
        # Simplified fallback for update
        return {
            "status": "error",
            "message": "ToDo update fallback not fully implemented",
        }


if __name__ == "__main__":
    print("--- Agent Interface Facade Demo ---")

    # Ensure some events are logged first if testing event-dependent calls
    print("\n0. Pre-populating some events via Shift Event Capture Facade:")
    call_shift_event_capture_agent(
        "patient001",
        {"sign_name": "Heart Rate", "value": 78, "unit": "bpm"},
        "vital_sign",
        source_override="DemoSetup",
    )
    call_shift_event_capture_agent(
        "patient001",
        {"text_observation": "Patient seems comfortable."},
        "observation",
        source_override="DemoSetup",
    )
    call_shift_event_capture_agent(
        "patient002",
        {"description": "Morning meds given."},
        "intervention",
        source_override="DemoSetup",
    )

    print("\n1. Testing Firestore Profile Fetch (via Facade):")
    profile_resp1 = call_data_aggregation_firestore("patient001")
    # print(json.dumps(profile_resp1, indent=2))
    call_data_aggregation_firestore("patient_nonexistent")

    print(
        "\n2. Testing AlloyDB Events Fetch (via Facade, should use shared event store):"
    )
    events_resp1 = call_data_aggregation_alloydb_events("patient001")
    # print(json.dumps(events_resp1, indent=2))
    events_resp2 = call_data_aggregation_alloydb_events(
        "patient002", filters={"event_type": "intervention"}
    )
    # print(json.dumps(events_resp2, indent=2))

    print("\n3. Testing Patient Summary Agent (via Facade):")
    if (
        profile_resp1.get("status") == "success"
        and events_resp1.get("status") == "success"
    ):
        call_patient_summary_agent(
            patient_profile=profile_resp1["data"],
            patient_events=events_resp1["data"],
            summary_type="daily_update",
        )

    print("\n4. Testing Shift Event Capture Agent (via Facade, adds to shared store):")
    call_shift_event_capture_agent(
        "patient001",
        event_details={"text_observation": "Patient reporting mild headache."},
        event_type="observation",
    )
    # Verify it's in the shared store by fetching again
    events_resp_after_log = call_data_aggregation_alloydb_events("patient001")
    print(
        f"  Events for patient001 after new log: {len(events_resp_after_log.get('data', []))} (check last event in output if imports work)"
    )
    # print(json.dumps(events_resp_after_log, indent=2))

    print("\n5. Testing To-Do List Manager (via Facade):")
    call_todo_list_manager(
        action="add_task",
        payload={
            "description": "Check patient001 pain level",
            "priority": "High",
            "patient_id": "patient001",
        },
    )
    call_todo_list_manager(
        action="add_task",
        payload={
            "description": "Restock general supplies",
            "priority": "Medium",
            "patient_id": "general",
        },
    )

    all_tasks_response = call_todo_list_manager(action="get_all_tasks", payload={})
    # print("All tasks:", json.dumps(all_tasks_response, indent=2))

    if all_tasks_response.get("status") == "success" and all_tasks_response.get(
        "tasks"
    ):
        # Find a task for patient001 to update
        task_to_update_id = None
        for task in all_tasks_response["tasks"]:
            if task.get("patient_id") == "patient001":
                task_to_update_id = task["task_id"]
                break
        if task_to_update_id:
            call_todo_list_manager(
                action="update_task_status",
                payload={"task_id": task_to_update_id, "new_status": "Completed"},
            )
        else:
            print("  No task found for patient001 to demonstrate update.")

    patient001_tasks = call_todo_list_manager(
        action="get_all_tasks", payload={"patient_id": "patient001"}
    )
    print("Patient001 tasks:", json.dumps(patient001_tasks, indent=2))

    print("\n--- Demo Completed ---")
