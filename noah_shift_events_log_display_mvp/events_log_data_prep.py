import json
import datetime
from dateutil import parser as dateutil_parser # Using dateutil.parser for robust ISO date parsing
import sys
import os

# --- Attempt to import SHARED_MOCK_EVENTS_DB from shift_event_capture.py ---
# This assumes a directory structure where noah_shift_event_capture_agent_mvp
# is a sibling to noah_shift_events_log_display_mvp, or that PYTHONPATH is set up.
try:
    # Construct the path to the directory containing noah_shift_event_capture_agent_mvp
    # This goes up one level from noah_shift_events_log_display_mvp, then into noah_shift_event_capture_agent_mvp
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # parent_dir = os.path.dirname(current_dir)
    # target_dir = os.path.join(parent_dir, "noah_shift_event_capture_agent_mvp")

    # Simplified path assuming current working directory is the root of all these MVP folders
    # Or, that the execution environment handles this structure.
    # For a robust solution in a real project, a shared library or proper packaging is needed.

    # Let's assume for this subtask, the tool's execution environment might have a flat structure
    # or specific way it handles imports. If this direct import path doesn't work,
    # we might need to fall back to a local copy for demonstration.

    # Option 1: Try direct import assuming it's discoverable
    # from noah_shift_event_capture_agent_mvp import shift_event_capture
    # SHARED_MOCK_EVENTS_DB = shift_event_capture.SHARED_MOCK_EVENTS_DB

    # Option 2: More robust path manipulation if scripts are in distinct folders
    # Get the directory of the current script
    current_script_path = os.path.dirname(os.path.realpath(__file__))
    # Path to the directory of the script we want to import from
    # This assumes `noah_shift_event_capture_agent_mvp` is a sibling directory
    # to `noah_shift_events_log_display_mvp`
    sibling_script_dir = os.path.join(os.path.dirname(current_script_path), "noah_shift_event_capture_agent_mvp")

    if sibling_script_dir not in sys.path:
        sys.path.insert(0, sibling_script_dir)
        # print(f"DEBUG: Added to sys.path: {sibling_script_dir}")

    # Now try to import (this might still fail if the tool environment is very sandboxed)
    # For simplicity in this tool environment, if direct import is an issue,
    # I will define a local copy of SHARED_MOCK_EVENTS_DB and proceed.
    # The core logic change is to use *a* SHARED_MOCK_EVENTS_DB, not its specific import mechanism here.

    # Let's try to import the module first, then access the variable
    import shift_event_capture
    IMPORTED_SHARED_MOCK_EVENTS_DB = shift_event_capture.SHARED_MOCK_EVENTS_DB
    print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported SHARED_MOCK_EVENTS_DB from shift_event_capture.py")

except ImportError as e:
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: Could not import SHARED_MOCK_EVENTS_DB from shift_event_capture.py: {e}")
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: Using a local mock store for events_log_data_prep.py. Data will not be shared from event capture for this run.")
    IMPORTED_SHARED_MOCK_EVENTS_DB = { # Local fallback for demonstration if import fails
        "patientX789": [
            {"event_id": "local_evt001", "timestamp": "2024-07-21T08:00:00Z", "patient_id": "patientX789", "event_type": "vital_sign", "source": "BedsideMonitor", "details": {"sign_name": "Heart Rate", "value": 75, "unit": "bpm"}},
            {"event_id": "local_evt003", "timestamp": "2024-07-21T08:05:00Z", "patient_id": "patientX789", "event_type": "observation", "source": "manual_text", "details": {"text_observation": "Patient resting (local data)."}}
        ]
    }
except AttributeError as e:
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: SHARED_MOCK_EVENTS_DB not found in imported shift_event_capture module: {e}")
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: Using a local mock store. Ensure SHARED_MOCK_EVENTS_DB is defined in shift_event_capture.py.")
    IMPORTED_SHARED_MOCK_EVENTS_DB = { # Local fallback
         "patientX789": [
            {"event_id": "attr_err_evt001", "timestamp": "2024-07-21T08:00:00Z", "patient_id": "patientX789", "event_type": "vital_sign", "source": "BedsideMonitor", "details": {"sign_name": "Heart Rate", "value": 70, "unit": "bpm"}}
        ]
    }


def get_mock_shift_events(patient_id: str, filter_criteria: dict = None) -> list:
    """
    Returns a list of event dictionaries for a given patient_id from the SHARED_MOCK_EVENTS_DB.
    Simulates basic filtering based on filter_criteria.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] DB_ACCESS: Getting shift events for {patient_id} from SHARED_MOCK_EVENTS_DB with filters: {filter_criteria}")

    # Access the (potentially imported) shared database
    # Make a copy to prevent modification of the original list during filtering
    patient_events_list = list(IMPORTED_SHARED_MOCK_EVENTS_DB.get(patient_id, []))

    if not patient_events_list:
        # Check system-wide alerts if patient-specific list is empty and no specific patient filter applied
        # or if the request is specifically for system alerts.
        if patient_id == "_system_alerts" or (not filter_criteria and not patient_events_list):
             patient_events_list = list(IMPORTED_SHARED_MOCK_EVENTS_DB.get("_system_alerts", []))
             if patient_events_list:
                 print(f"[{datetime.datetime.utcnow().isoformat()}] DB_ACCESS: Found {len(patient_events_list)} system alerts.")


    if not patient_events_list:
        print(f"[{datetime.datetime.utcnow().isoformat()}] DB_ACCESS: No events found for {patient_id}.")
        return []

    filtered_events = patient_events_list # Start with all events for the patient
    if filter_criteria:
        # Filter by event_type
        event_type_filter = filter_criteria.get("event_type")
        if event_type_filter:
            filtered_events = [
                event for event in filtered_events
                if event.get("event_type") == event_type_filter
            ]

        time_range = filter_criteria.get("time_range")
        if time_range:
            start_time_str = time_range.get("start")
            end_time_str = time_range.get("end")

            start_time = dateutil_parser.isoparse(start_time_str) if start_time_str else None
            end_time = dateutil_parser.isoparse(end_time_str) if end_time_str else None

            if start_time:
                filtered_events = [
                    event for event in filtered_events
                    if dateutil_parser.isoparse(event.get("timestamp", "1900-01-01T00:00:00Z")) >= start_time
                ]
            if end_time:
                filtered_events = [
                    event for event in filtered_events
                    if dateutil_parser.isoparse(event.get("timestamp", "9999-12-31T23:59:59Z")) <= end_time
                ]

    # Sort events by timestamp (descending - newest first, common for logs)
    filtered_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    print(f"[{datetime.datetime.utcnow().isoformat()}] DB_ACCESS: Returning {len(filtered_events)} events for {patient_id} after filtering.")
    return filtered_events

def format_event_for_display(event_data: dict) -> str:
    """
    Formats a single event dictionary into a human-readable string summary.
    """
    if not isinstance(event_data, dict):
        return "Invalid event data format."

    ts_str = event_data.get("timestamp", "No Timestamp")
    try:
        # Attempt to parse and format the time part only
        dt_obj = dateutil_parser.isoparse(ts_str)
        time_display = dt_obj.strftime("%H:%M")
    except ValueError:
        time_display = ts_str # Fallback if timestamp is not standard ISO

    event_type = event_data.get("event_type", "Unknown Event").replace("_", " ").title()
    details = event_data.get("details", {})
    summary = f"[{time_display}] {event_type}: "

    if event_type == "Vital Sign":
        summary += f"{details.get('sign_name', 'N/A')} {details.get('value', 'N/A')} {details.get('unit', '')}"
    elif event_type == "Observation":
        summary += details.get('text_observation', 'No details.')
    elif event_type == "Intervention":
        desc = details.get('description', 'No description.')
        med = details.get('medication_administered')
        if med:
            desc += f" (Medication: {med.get('name', 'N/A')} {med.get('dosage', '')} {med.get('route', '')})"
        summary += desc
    elif event_type == "General Note":
        summary += details.get('note_content', 'No content.')
    elif event_type == "Alert Notification":
        summary += f"[{details.get('priority', 'N/A')}] {details.get('message', 'No message.')} (Type: {details.get('alert_type', 'N/A')})"
    else:
        # Generic fallback for other event types
        summary += json.dumps(details) if details else "No specific details."

    return summary.strip()


if __name__ == "__main__":
    # This is a placeholder for the actual test patient ID used in shift_event_capture.py
    # The SHARED_MOCK_EVENTS_DB will be populated by running shift_event_capture.py's main block.
    # For this script to show shared data, shift_event_capture.py must have run and populated
    # the SHARED_MOCK_EVENTS_DB in the same Python session, or the import must successfully
    # load a pre-populated state (which is not how Python modules usually work unless it's persisted).

    # To make this testable standalone AND show integration if possible:
    # 1. We rely on the import succeeding.
    # 2. If shift_event_capture.py's main block hasn't run in the *same session leading to this call*,
    #    IMPORTED_SHARED_MOCK_EVENTS_DB would be empty or as defined at its module level.
    #    The print statements during import will indicate if it's using a local fallback.

    print(f"--- Testing Event Log (potentially from SHARED_MOCK_EVENTS_DB) ---")

    # Use a known patient ID that might have events from shift_event_capture.py
    # (e.g., "PATIENT_789" or "PATIENT_101" from its demo)
    test_patient_id_shared = "PATIENT_789"
    # Also test with a patient that might only be in the local fallback
    test_patient_id_local_fallback = "patientX789"


    print(f"\n--- Events for Patient ID: {test_patient_id_shared} (potentially from shared capture) ---")
    all_events_shared = get_mock_shift_events(test_patient_id_shared)
    if all_events_shared:
        for event in all_events_shared:
            # print(f"  - Raw: {event}") # Keep output cleaner for this test
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print(f"  No events found for {test_patient_id_shared} in SHARED_MOCK_EVENTS_DB.")
        print(f"  Note: Run shift_event_capture.py's main block in the same session or ensure")
        print(f"  SHARED_MOCK_EVENTS_DB is populated via other means for this to show shared data.")

    print(f"\n--- Events for Patient ID: {test_patient_id_local_fallback} (likely from local fallback if import failed) ---")
    all_events_local = get_mock_shift_events(test_patient_id_local_fallback)
    if all_events_local:
        for event in all_events_local:
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print(f"  No events found for {test_patient_id_local_fallback}.")


    print("\n--- Further filter tests (will use data available to this script) ---")
    print(f"1. Filter '{test_patient_id_shared}' by event_type = 'vital_sign':")
    vital_signs_filter = {"event_type": "vital_sign"}
    vital_sign_events = get_mock_shift_events(test_patient_id_shared, filter_criteria=vital_signs_filter)
    if vital_sign_events:
        for event in vital_sign_events:
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print(f"  No vital sign events found for {test_patient_id_shared} with this filter.")

    print(f"\n2. Filter '{test_patient_id_shared}' by time_range (e.g., after a specific time):")
    # Adjust time to be relevant if events are being captured now
    # For mock data, use a fixed time that matches its timestamps
    # Example: If shift_event_capture adds events around "2024-07-21T..."
    time_filter_start = {"time_range": {"start": "2024-07-21T09:00:00Z"}} # Use a relevant time for your test data
    if IMPORTED_SHARED_MOCK_EVENTS_DB.get(test_patient_id_shared): # If there's data
        # Dynamically adjust start time for demo if possible, or use a known timestamp from mocks
        # For now, using a fixed timestamp that should exist in shift_event_capture's demo data
        first_event_ts = IMPORTED_SHARED_MOCK_EVENTS_DB[test_patient_id_shared][0]['timestamp']
        # time_filter_start = {"time_range": {"start": first_event_ts}} # Example of dynamic filter

    late_events = get_mock_shift_events(test_patient_id_shared, filter_criteria=time_filter_start)
    if late_events:
        for event in late_events:
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print(f"  No events found for {test_patient_id_shared} in this time range.")

    print("\n3. System-wide alerts (if any were logged to _system_alerts by capture script):")
    system_alerts = get_mock_shift_events("_system_alerts")
    if system_alerts:
        for alert in system_alerts:
            print(f"    Formatted: {format_event_for_display(alert)}")
    else:
        print("  No system-wide alerts found in SHARED_MOCK_EVENTS_DB.")


    print("\n--- Demo Completed ---")
