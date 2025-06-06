import pytest
import sys
import os
from unittest.mock import patch, MagicMock

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import agent_interfaces as agents
import conceptual_workflows

MOCK_PSA_PROFILES = {
    "patient001": {"patientId": "patient001", "name": "John Doe (Test)", "principalProblem": "Pneumonia", "allergies": ["None"]},
    "patient002": {"patientId": "patient002", "name": "Jane Smith (Test)", "principalProblem": "CHF", "allergies": ["Penicillin"]},
    "patient_error_case": {"patientId": "patient_error_case", "name": "Error Case (Test)", "principalProblem": "Unknown", "allergies": []}
}

MOCK_SECA_SHARED_EVENTS = {}

MOCK_TLM_TASKS_DB = []

@pytest.fixture(autouse=True)
def isolate_mock_data_stores(monkeypatch):
    current_test_profiles = MOCK_PSA_PROFILES.copy()
    current_test_events = {}
    for k, v_list in MOCK_SECA_SHARED_EVENTS.items():
        current_test_events[k] = [item.copy() for item in v_list]
    current_test_tasks = [item.copy() for item in MOCK_TLM_TASKS_DB]

    monkeypatch.setattr(agents, 'PSA_PROFILES', current_test_profiles)
    monkeypatch.setattr(agents, 'SECA_SHARED_EVENTS', current_test_events)
    monkeypatch.setattr(agents, 'TLM_TASKS_DB', current_test_tasks)

    if hasattr(agents, 'psa_get_profile') and hasattr(agents.psa_get_profile, '__module__'):
        if agents.IMPORTED_PSA:
            try:
                from noah_patient_summary_agent_mvp import patient_summary_agent
                monkeypatch.setattr(patient_summary_agent, 'MOCK_PATIENT_PROFILES', current_test_profiles)
            except ImportError:
                pass

    if hasattr(agents, 'seca_log_event') and hasattr(agents.seca_log_event, '__module__'):
        if agents.IMPORTED_SECA:
            try:
                from noah_shift_event_capture_agent_mvp import shift_event_capture
                monkeypatch.setattr(shift_event_capture, 'SHARED_MOCK_EVENTS_DB', current_test_events)
            except ImportError:
                pass

    if hasattr(agents, 'tlm_add_task') and hasattr(agents.tlm_add_task, '__module__'):
        if agents.IMPORTED_TLM:
            try:
                from noah_plan_of_care_todo_mvp import todo_list_manager
                monkeypatch.setattr(todo_list_manager, 'MOCK_TASKS_DB', current_test_tasks)
            except ImportError:
                pass

    yield

@pytest.fixture
def mock_agent_calls():
    with patch.object(agents, 'call_data_aggregation_firestore', autospec=True) as mock_firestore, \
         patch.object(agents, 'call_data_aggregation_alloydb_events', autospec=True) as mock_alloydb, \
         patch.object(agents, 'call_patient_summary_agent', autospec=True) as mock_summary, \
         patch.object(agents, 'call_shift_event_capture_agent', autospec=True) as mock_event_capture, \
         patch.object(agents, 'call_todo_list_manager', autospec=True) as mock_todo:

        mock_firestore.return_value = {"status": "success", "data": {}}
        mock_alloydb.return_value = {"status": "success", "data": []}
        mock_summary.return_value = {"status": "success", "summary_text": "Mocked summary."}
        mock_event_capture.return_value = {"status": "success", "log_entry": {"event_id": "mock_event_123"}}
        mock_todo.return_value = {"status": "success", "task": {"task_id": "mock_task_123"}}

        yield {
            "firestore": mock_firestore,
            "alloydb": mock_alloydb,
            "summary": mock_summary,
            "event_capture": mock_event_capture,
            "todo": mock_todo,
        }

def test_example_workflow_call(mock_agent_calls):
    patient_id = "patient001"
    conceptual_workflows.run_patient_intake_workflow(patient_id)

    mock_agent_calls["firestore"].assert_called_once_with(patient_id)

def test_run_patient_intake_workflow_success(mock_agent_calls):
    patient_id = "patient001"
    mock_profile_data = {"patientId": patient_id, "name": "John Test", "age": 30}
    mock_events_data = [{"event_id": "event1", "description": "Checked in"}]
    mock_summary_text = "This is an intake summary."

    mock_agent_calls["firestore"].return_value = {"status": "success", "data": mock_profile_data}
    mock_agent_calls["alloydb"].return_value = {"status": "success", "data": mock_events_data}
    mock_agent_calls["summary"].return_value = {"status": "success", "summary_text": mock_summary_text}

    # Capture print output to check for logged messages if necessary, though less robust
    # For now, focus on mock calls and arguments
    conceptual_workflows.run_patient_intake_workflow(patient_id)

    mock_agent_calls["firestore"].assert_called_once_with(patient_id)
    mock_agent_calls["alloydb"].assert_called_once_with(patient_id)
    mock_agent_calls["summary"].assert_called_once_with(
        patient_profile=mock_profile_data,
        patient_events=mock_events_data,
        summary_type="intake_assessment"
    )

def test_run_patient_intake_workflow_profile_fetch_fails(mock_agent_calls, capsys):
    patient_id = "patient_error_case"
    error_message = "Simulated Firestore error"

    # Configure firestore mock to return an error
    mock_agent_calls["firestore"].return_value = {"status": "error", "message": error_message}

    conceptual_workflows.run_patient_intake_workflow(patient_id)

    mock_agent_calls["firestore"].assert_called_once_with(patient_id)
    # Ensure subsequent calls were NOT made
    mock_agent_calls["alloydb"].assert_not_called()
    mock_agent_calls["summary"].assert_not_called()

    # Verify error message was printed (optional, but good for this kind of workflow)
    # captured = capsys.readouterr()
    # assert error_message in captured.out # Check if the workflow prints the error
    # The conceptual_workflows.py prints '  [WORKFLOW_ERROR] Could not fetch patient profile: {message}'
    # So we check for that pattern
    # For now, we will rely on the calls not being made as primary verification
    # and assume the print statement in conceptual_workflows.py is correct.
    # If more robust error checking is needed, the workflow could return a status.

def test_run_log_new_observation_workflow_success(mock_agent_calls):
    patient_id = "patient002"
    observation_text = "Patient is feeling better today."
    source = "nurse_report"

    mock_logged_event_id = "event_log_456"
    mock_profile_data = {"patientId": patient_id, "name": "Jane Test"}
    # Simulate that the event fetch after logging includes the new event
    # The conceptual_workflow.py checks if the new event is present in re-fetched events,
    # so the mock for alloydb should reflect this.
    mock_initial_events_data = [{"event_id": "event_old_1", "description": "Old event"}]
    mock_event_logged_details = {
        "event_id": mock_logged_event_id,
        "patient_id": patient_id,
        "event_type": "observation",
        "details": {"text_observation": observation_text, "source": source},
        "source_override": source
    }
    mock_events_after_logging = mock_initial_events_data + [mock_event_logged_details]
    mock_updated_summary = "Summary includes new observation."

    # Configure mocks
    mock_agent_calls["event_capture"].return_value = {"status": "success", "log_entry": {"event_id": mock_logged_event_id, "details": mock_event_logged_details}}
    # Firestore is called after event capture
    mock_agent_calls["firestore"].return_value = {"status": "success", "data": mock_profile_data}
    # AlloyDB is called after event capture, should return updated events
    mock_agent_calls["alloydb"].return_value = {"status": "success", "data": mock_events_after_logging}
    mock_agent_calls["summary"].return_value = {"status": "success", "summary_text": mock_updated_summary}

    conceptual_workflows.run_log_new_observation_workflow(patient_id, observation_text, source)

    # Verify calls
    mock_agent_calls["event_capture"].assert_called_once_with(
        patient_id=patient_id,
        event_details={"text_observation": observation_text, "source": source},
        event_type="observation",
        source_override=source
    )
    # Check that profile and events are fetched after successful logging
    mock_agent_calls["firestore"].assert_called_once_with(patient_id)
    mock_agent_calls["alloydb"].assert_called_once_with(patient_id) # This is called after event_capture

    # Verify summary agent is called with the profile and the *updated* events
    mock_agent_calls["summary"].assert_called_once_with(
        patient_profile=mock_profile_data,
        patient_events=mock_events_after_logging, # Crucial check
        summary_type="progress_note_update"
    )

def test_run_log_new_observation_workflow_logging_fails(mock_agent_calls, capsys):
    patient_id = "patient002"
    observation_text = "This observation will fail to log."
    source = "system_error_sim"
    error_message = "Simulated event capture error"

    mock_agent_calls["event_capture"].return_value = {"status": "error", "message": error_message}

    conceptual_workflows.run_log_new_observation_workflow(patient_id, observation_text, source)

    # Verify event_capture was called
    mock_agent_calls["event_capture"].assert_called_once_with(
        patient_id=patient_id,
        event_details={"text_observation": observation_text, "source": source},
        event_type="observation",
        source_override=source
    )

    # Ensure subsequent calls for summary generation were NOT made
    mock_agent_calls["firestore"].assert_not_called()
    mock_agent_calls["alloydb"].assert_not_called()
    mock_agent_calls["summary"].assert_not_called()

    # captured = capsys.readouterr()
    # assert error_message in captured.out # As before, direct print check is optional

def test_run_add_todo_task_workflow_success(mock_agent_calls):
    patient_id = "patient001"
    task_description = "Follow up on lab results."
    priority = "High"

    mock_created_task = {"task_id": "task_789", "description": task_description, "priority": priority, "patient_id": patient_id, "status": "Pending"}
    mock_agent_calls["todo"].return_value = {"status": "success", "task": mock_created_task}

    conceptual_workflows.run_add_todo_task_workflow(patient_id, task_description, priority)

    expected_payload = {
        "description": task_description,
        "priority": priority,
        "patient_id": patient_id
    }
    mock_agent_calls["todo"].assert_called_once_with(action="add_task", payload=expected_payload)

def test_run_add_todo_task_workflow_add_fails(mock_agent_calls, capsys):
    patient_id = "patient001"
    task_description = "This task will fail to add."
    priority = "Medium"
    error_message = "Simulated ToDo manager error"

    mock_agent_calls["todo"].return_value = {"status": "error", "message": error_message}

    conceptual_workflows.run_add_todo_task_workflow(patient_id, task_description, priority)

    expected_payload = {
        "description": task_description,
        "priority": priority,
        "patient_id": patient_id
    }
    mock_agent_calls["todo"].assert_called_once_with(action="add_task", payload=expected_payload)

    # captured = capsys.readouterr()
    # assert error_message in captured.out # Optional: check for error print

if __name__ == "__main__":
    print("Run tests using 'pytest noah_agent_orchestration_groundwork/tests/test_agent_orchestration_workflows.py'")
