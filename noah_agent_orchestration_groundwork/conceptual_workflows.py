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
    events_response = agents.call_data_aggregation_alloydb_events(patient_id)
    # Assuming for this workflow, we proceed even if no events are found, but check status
    if events_response.get("status") == "error":
        print(f"  [WORKFLOW_WARN] Could not fetch patient events: {events_response.get('message')}. Proceeding with summary generation.")
        patient_events = []
    else:
        patient_events = events_response.get("data", [])
    print(f"  [WORKFLOW_STEP_2] Patient Events fetched: {len(patient_events)} events found.")
    # For brevity, not printing all events here.

    # Step 3: Generate intake summary
    summary_response = agents.call_patient_summary_agent(
        patient_profile=patient_profile,
        patient_events=patient_events,
        summary_type="intake_assessment"
    )
    if summary_response.get("status") == "error":
        print(f"  [WORKFLOW_ERROR] Could not generate patient summary: {summary_response.get('message')}")
    else:
        intake_summary = summary_response.get("summary_text", "No summary generated.")
        print(f"  [WORKFLOW_STEP_3] Intake Summary generated:\n{intake_summary}")

    print("--- Patient Intake Workflow Completed ---")

def run_log_new_observation_workflow(patient_id: str, observation_text: str, source: str = "manual_text_entry"):
    """
    Simulates logging a new observation and potentially updating a summary.
    """
    print(f"\n--- Starting Log New Observation Workflow for patient_id: {patient_id} ---")
    print(f"  Observation: '{observation_text}' from source: '{source}'")

    # Step 1: Log the observation
    event_details = {"text_observation": observation_text, "source": source}
    log_response = agents.call_shift_event_capture_agent(
        patient_id=patient_id,
        event_details=event_details,
        event_type="observation"
    )

    if log_response.get("status") == "error":
        print(f"  [WORKFLOW_ERROR] Failed to log observation: {log_response.get('message')}")
        print("--- Log New Observation Workflow Ended (with error) ---")
        return

    print(f"  [WORKFLOW_STEP_1] Observation (simulated) logged: {log_response.get('log_entry', {}).get('log_id')}")

    # Step 2: (Conceptual) Fetch updated data and regenerate summary
    print("  [WORKFLOW_STEP_2_CONCEPTUAL] Simulating fetching updated data and regenerating summary...")

    profile_response = agents.call_data_aggregation_firestore(patient_id)
    patient_profile = profile_response.get("data", {})

    # Fetch events again - in a real system, the new event would be included
    events_response = agents.call_data_aggregation_alloydb_events(patient_id)
    patient_events = events_response.get("data", [])
    # Manually add the new observation to the list for this conceptual step
    if log_response.get("status") == "success":
         # Create a mock event structure similar to what call_data_aggregation_alloydb_events would return
        new_mock_event = {
            "timestamp": log_response["log_entry"].get("timestamp", datetime.datetime.utcnow().isoformat() + "Z"),
            "event_type": log_response["log_entry"].get("event_type"),
            "details": log_response["log_entry"].get("details")
        }
        patient_events.append(new_mock_event)


    if patient_profile:
        updated_summary_response = agents.call_patient_summary_agent(
            patient_profile=patient_profile,
            patient_events=patient_events,
            summary_type="progress_note_update"
        )
        if updated_summary_response.get("status") == "success":
            print(f"  [WORKFLOW_STEP_2_CONCEPTUAL] Updated Summary (simulated):\n{updated_summary_response.get('summary_text')}")
        else:
            print(f"  [WORKFLOW_WARN] Could not regenerate summary after logging event.")
    else:
        print(f"  [WORKFLOW_WARN] Could not fetch profile to regenerate summary.")

    print("--- Log New Observation Workflow Completed ---")

def run_add_todo_task_workflow(patient_id: str, task_description: str, priority: str):
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
