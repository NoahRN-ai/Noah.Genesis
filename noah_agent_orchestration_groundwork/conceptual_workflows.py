import agent_interfaces as agents # Use a clear alias for the imported stubs
import json

def run_patient_intake_workflow(patient_id: str):
    """
    Simulates a workflow for patient intake.
    1. Fetches patient profile.
    2. Fetches recent events for the patient.
    3. Generates an intake summary.
    """
    print(f"\n--- Starting Patient Intake Workflow for patient_id: {patient_id} ---")

    # Step 1: Get patient profile
    profile_response = agents.call_data_aggregation_firestore(patient_id)
    if profile_response.get("status") == "error":
        print(f"  [WORKFLOW_ERROR] Could not fetch patient profile: {profile_response.get('message')}")
        print("--- Patient Intake Workflow Ended (with error) ---")
        return
    patient_profile = profile_response.get("data", {})
    print(f"  [WORKFLOW_STEP_1] Patient Profile fetched: {json.dumps(patient_profile, indent=2)}")

    # Step 2: Get recent events
    # This call should now reflect events potentially added by call_shift_event_capture_agent
    # if the shared event store (SECA_SHARED_EVENTS) is being used by both.
    events_response = agents.call_data_aggregation_alloydb_events(patient_id)
    if events_response.get("status") == "error":
        print(f"  [WORKFLOW_WARN] Could not fetch patient events: {events_response.get('message')}. Proceeding with summary generation.")
        patient_events = []
    else:
        patient_events = events_response.get("data", [])
    print(f"  [WORKFLOW_STEP_2] Patient Events fetched: {len(patient_events)} events found.")
    if patient_events:
        print(f"    Last event timestamp (if any): {patient_events[0].get('timestamp') if patient_events else 'N/A'}") # Events are sorted desc by default by eldp_get_events

    # Step 3: Generate intake summary
    # This call now uses the potentially more deeply integrated patient_summary_agent logic
    summary_response = agents.call_patient_summary_agent(
        patient_profile=patient_profile,
        patient_events=patient_events, # Pass the fetched events
        summary_type="intake_assessment"
    )
    if summary_response.get("status") == "error":
        print(f"  [WORKFLOW_ERROR] Could not generate patient summary: {summary_response.get('message')}")
    else:
        intake_summary = summary_response.get("summary_text", "No summary generated.")
        print(f"  [WORKFLOW_STEP_3] Intake Summary generated (via Facade):\n{intake_summary}")

    print("--- Patient Intake Workflow Completed ---")


def run_log_new_observation_workflow(patient_id: str, observation_text: str, source: str = "manual_text_entry"):
    """
    Simulates logging a new observation and then regenerating a summary,
    expecting the new observation to be part of the data for the summary.
    """
    print(f"\n--- Starting Log New Observation Workflow for patient_id: {patient_id} ---")
    print(f"  Observation: '{observation_text}' from source: '{source}'")

    # Step 1: Log the observation using the facade, which calls shift_event_capture agent's logic
    event_details = {"text_observation": observation_text, "source": source}
    log_response = agents.call_shift_event_capture_agent( # This uses seca_log_event
        patient_id=patient_id,
        event_details=event_details,
        event_type="observation",
        source_override=source # Pass source to be part of the event for storage
    )

    if log_response.get("status") == "error":
        print(f"  [WORKFLOW_ERROR] Failed to log observation: {log_response.get('message')}")
        print("--- Log New Observation Workflow Ended (with error) ---")
        return

    logged_event_id = log_response.get("log_entry", {}).get("event_id", "N/A")
    print(f"  [WORKFLOW_STEP_1] Observation logged via Facade. Event ID: {logged_event_id}")

    # Step 2: Fetch updated data (profile and events) and regenerate summary
    print("  [WORKFLOW_STEP_2] Fetching updated data and regenerating summary...")

    profile_response = agents.call_data_aggregation_firestore(patient_id) # Facade call
    patient_profile = profile_response.get("data", {})

    # Fetch events again. This call (via facade to eldp_get_events)
    # should now include the event just logged if SHARED_MOCK_EVENTS_DB is working as expected.
    events_response = agents.call_data_aggregation_alloydb_events(patient_id) # Facade call
    patient_events_updated = events_response.get("data", [])

    print(f"  [WORKFLOW_STEP_2] Events fetched after logging: {len(patient_events_updated)} events.")
    # Check if the new event is present (optional check)
    found_new_event_in_refetch = any(evt.get('event_id') == logged_event_id for evt in patient_events_updated)
    print(f"    New event ({logged_event_id}) present in re-fetched events: {found_new_event_in_refetch}")


    if patient_profile:
        updated_summary_response = agents.call_patient_summary_agent( # Facade call
            patient_profile=patient_profile,
            patient_events=patient_events_updated, # Use the re-fetched events
            summary_type="progress_note_update"
        )
        if updated_summary_response.get("status") == "success":
            print(f"  [WORKFLOW_STEP_2] Updated Summary (via Facade):\n{updated_summary_response.get('summary_text')}")
        else:
            print(f"  [WORKFLOW_WARN] Could not regenerate summary after logging event: {updated_summary_response.get('message')}")
    else:
        print(f"  [WORKFLOW_WARN] Could not fetch profile to regenerate summary.")

    print("--- Log New Observation Workflow Completed ---")


def run_add_todo_task_workflow(patient_id_for_task: str, task_description: str, priority: str):
    """
    Simulates adding a new task to the To-Do list.
    """
    print(f"\n--- Starting Add To-Do Task Workflow for patient_id: {patient_id} ---")
    print(f"  Task: '{task_description}', Priority: {priority}")

    # Step 1: Add the task
    add_task_payload = {
        "description": task_description,
        "priority": priority,
        "patient_id": patient_id # Can also be "general" or other identifiers
    }
    task_response = agents.call_todo_list_manager(action="add_task", payload=add_task_payload)

    if task_response.get("status") == "success":
        created_task = task_response.get("task", {})
        print(f"  [WORKFLOW_STEP_1] Task added successfully: {created_task.get('task_id')}")
        print(f"    Details: {json.dumps(created_task, indent=2)}")
    else:
        print(f"  [WORKFLOW_ERROR] Failed to add task: {task_response.get('message')}")

    print("--- Add To-Do Task Workflow Completed ---")

if __name__ == "__main__":
    print("===== Running Conceptual Workflows Demo =====")

    # Workflow 1: Patient Intake
    run_patient_intake_workflow(patient_id="patient001")
    run_patient_intake_workflow(patient_id="patient_nonexistent") # Test error case

    # Workflow 2: Log New Observation
    run_log_new_observation_workflow(patient_id="patient002", observation_text="Patient reports feeling better after medication.")

    # Workflow 3: Add To-Do Task
    run_add_todo_task_workflow(patient_id="patient001", task_description="Prepare discharge summary.", priority="High")
    run_add_todo_task_workflow(patient_id="general_unit", task_description="Check emergency cart supplies.", priority="Medium")

    print("\n===== Conceptual Workflows Demo Completed =====")
