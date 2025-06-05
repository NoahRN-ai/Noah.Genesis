import json
import datetime
from dateutil import parser as dateutil_parser # Using dateutil.parser for robust ISO date parsing

# --- Mock Event Data Store ---
MOCK_PATIENT_EVENTS = {
    "patientX789": [
        {
            "event_id": "evt001", "timestamp": "2024-07-21T08:00:00Z", "patient_id": "patientX789",
            "event_type": "vital_sign", "source": "BedsideMonitor",
            "details": {"sign_name": "Heart Rate", "value": 72, "unit": "bpm"}
        },
        {
            "event_id": "evt002", "timestamp": "2024-07-21T08:00:00Z", "patient_id": "patientX789",
            "event_type": "vital_sign", "source": "BedsideMonitor",
            "details": {"sign_name": "Blood Pressure", "value": "120/80", "unit": "mmHg"}
        },
        {
            "event_id": "evt003", "timestamp": "2024-07-21T08:05:00Z", "patient_id": "patientX789",
            "event_type": "observation", "source": "manual_text",
            "details": {"text_observation": "Patient awake and alert, reports feeling rested."}
        },
        {
            "event_id": "evt004", "timestamp": "2024-07-21T09:15:00Z", "patient_id": "patientX789",
            "event_type": "intervention", "source": "NurseInput_Intervention",
            "details": {"description": "Administered Paracetamol 1g PO for headache.", "medication_administered": {"name": "Paracetamol", "dosage": "1g", "route": "PO"}}
        },
        {
            "event_id": "evt005", "timestamp": "2024-07-21T10:00:00Z", "patient_id": "patientX789",
            "event_type": "general_note", "source": "voice_transcription_note",
            "details": {"note_content": "Discussed plan of care with patient and family. All questions answered."}
        },
        {
            "event_id": "evt006", "timestamp": "2024-07-21T12:00:00Z", "patient_id": "patientX789",
            "event_type": "vital_sign", "source": "BedsideMonitor",
            "details": {"sign_name": "Temperature", "value": 37.1, "unit": "Celsius"}
        },
        {
            "event_id": "evt007", "timestamp": "2024-07-21T13:30:00Z", "patient_id": "patientX789",
            "event_type": "observation", "source": "manual_text",
            "details": {"text_observation": "Patient ambulated in hallway x2 with steady gait."}
        },
        {
            "event_id": "evt008", "timestamp": "2024-07-21T14:00:00Z", "patient_id": "patientX789",
            "event_type": "alert_notification", "source": "LabSystem",
            "details": {"alert_type": "CriticalLabValue", "message": "Potassium 3.0 mEq/L (Low)", "priority": "High"}
        }
    ],
    "patientY123": [
        # Add more events for another patient if needed for testing
    ]
}

def get_mock_shift_events(patient_id: str, filter_criteria: dict = None) -> list:
    """
    Returns a list of mock event dictionaries for a given patient_id.
    Simulates basic filtering based on filter_criteria.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DB_FETCH: Getting shift events for {patient_id} with filters: {filter_criteria}")
    patient_events = MOCK_PATIENT_EVENTS.get(patient_id, [])
    if not patient_events:
        return []

    filtered_events = patient_events
    if filter_criteria:
        # Filter by event_type
        if "event_type" in filter_criteria and filter_criteria["event_type"]:
            filtered_events = [
                event for event in filtered_events
                if event.get("event_type") == filter_criteria["event_type"]
            ]

        # Filter by time_range (start and/or end)
        # Expects time_range: {"start": "ISO_DATETIME_STR", "end": "ISO_DATETIME_STR"}
        time_range = filter_criteria.get("time_range")
        if time_range:
            start_time_str = time_range.get("start")
            end_time_str = time_range.get("end")

            start_time = dateutil_parser.isoparse(start_time_str) if start_time_str else None
            end_time = dateutil_parser.isoparse(end_time_str) if end_time_str else None

            if start_time:
                filtered_events = [
                    event for event in filtered_events
                    if dateutil_parser.isoparse(event.get("timestamp")) >= start_time
                ]
            if end_time:
                filtered_events = [
                    event for event in filtered_events
                    if dateutil_parser.isoparse(event.get("timestamp")) <= end_time
                ]

        # Add more filters here if needed (e.g., by source, by specific detail key/value)

    # Sort events by timestamp (descending - newest first, common for logs)
    filtered_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DB_FETCH: Returning {len(filtered_events)} events after filtering.")
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
    test_patient_id = "patientX789"

    print(f"--- Testing Event Log for Patient: {test_patient_id} ---")

    print("\n1. Get all events (no filter):")
    all_events = get_mock_shift_events(test_patient_id)
    if all_events:
        for event in all_events:
            print(f"  - Raw: {event}")
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print("  No events found.")

    print("\n2. Filter by event_type = 'vital_sign':")
    vital_signs_filter = {"event_type": "vital_sign"}
    vital_sign_events = get_mock_shift_events(test_patient_id, filter_criteria=vital_signs_filter)
    if vital_sign_events:
        for event in vital_sign_events:
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print("  No vital sign events found with this filter.")

    print("\n3. Filter by time_range (events on or after 09:00):")
    time_filter_start = {"time_range": {"start": "2024-07-21T09:00:00Z"}}
    late_events = get_mock_shift_events(test_patient_id, filter_criteria=time_filter_start)
    if late_events:
        for event in late_events:
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print("  No events found in this time range.")

    print("\n4. Filter by time_range (events between 08:00 and 10:00 inclusive):")
    time_filter_range = {"time_range": {"start": "2024-07-21T08:00:00Z", "end": "2024-07-21T10:00:00Z"}}
    mid_events = get_mock_shift_events(test_patient_id, filter_criteria=time_filter_range)
    if mid_events:
        for event in mid_events:
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print("  No events found in this time range.")

    print("\n5. Filter by event_type = 'observation' AND time_range (after 12:00):")
    combined_filter = {
        "event_type": "observation",
        "time_range": {"start": "2024-07-21T12:00:00Z"}
    }
    combined_events = get_mock_shift_events(test_patient_id, filter_criteria=combined_filter)
    if combined_events:
        for event in combined_events:
            print(f"    Formatted: {format_event_for_display(event)}")
    else:
        print("  No events found with this combined filter.")

    print("\n--- Testing with a patient with no events ---")
    no_events_patient = "patientNonExistent"
    no_events = get_mock_shift_events(no_events_patient)
    if not no_events:
        print(f"  Correctly returned no events for {no_events_patient}")

    print("\n--- Demo Completed ---")
