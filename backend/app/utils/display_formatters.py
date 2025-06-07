import json
import datetime
from typing import Dict, Any # Ensure typing imports are present

# Attempt to import dateutil.parser, which is a common library for robust date parsing.
# If not available in the execution environment, a standard library alternative might be needed,
# or this signals a dependency to be added.
try:
    from dateutil import parser as dateutil_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN (display_formatters): python-dateutil not found. Timestamp parsing will be basic.")

def format_event_for_display(event_data: Dict[str, Any]) -> str:
    """
    Formats a single event dictionary (presumably from AlloyDBDataService.list_events_for_patient)
    into a human-readable string summary.
    (Adapted from events_log_data_prep.py)
    """
    if not isinstance(event_data, dict):
        return "Invalid event data format: not a dictionary."

    ts_str = event_data.get("timestamp", "No Timestamp")
    time_display = ts_str # Default if parsing fails or dateutil not available

    if DATEUTIL_AVAILABLE:
        try:
            dt_obj = dateutil_parser.isoparse(ts_str)
            time_display = dt_obj.strftime("%H:%M") # Format to show only time
        except ValueError:
            print(f"[{datetime.datetime.utcnow().isoformat()}] WARN (display_formatters): Could not parse timestamp '{ts_str}' with dateutil.")
            # Keep ts_str as is, or use basic parsing if possible
            try: # Basic ISO parsing attempt if dateutil fails
                dt_obj_basic = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                time_display = dt_obj_basic.strftime("%H:%M")
            except ValueError:
                pass # Keep original ts_str if all parsing fails
    else: # Basic parsing if dateutil is not available
        try:
            dt_obj_basic = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            time_display = dt_obj_basic.strftime("%H:%M")
        except ValueError: # If basic parsing fails, keep original string
            pass


    event_type_original = event_data.get("eventType", "Unknown Event") # From AlloyDB field name
    event_type_display = event_type_original.replace("_", " ").title()

    # 'value' field from AlloyDB EventLogs table contains the original event_details
    details = event_data.get("value", {})
    if not isinstance(details, dict): # Ensure details is a dict, could be JSON string from DB
        try:
            details = json.loads(details) if isinstance(details, str) else {}
        except json.JSONDecodeError:
            details = {}

    summary = f"[{time_display}] {event_type_display}: "

    # Formatting based on eventType, using the structure from 'value' (original details)
    if event_type_original == "vital_sign": # Matches eventType in event_schemas.json
        summary += f"{details.get('sign_name', 'N/A')} {details.get('value', 'N/A')} {details.get('unit', '')}"
    elif event_type_original == "observation":
        summary += details.get('text_observation', 'No details.')
    elif event_type_original == "intervention":
        desc = details.get('description', 'No description.')
        med = details.get('medication_administered')
        if med and isinstance(med, dict):
            desc += f" (Medication: {med.get('name', 'N/A')} {med.get('dosage', '')} {med.get('route', '')})"
        summary += desc
    elif event_type_original == "general_note":
        summary += details.get('note_content', 'No content.')
    elif event_type_original == "alert_notification":
        summary += f"[{details.get('priority', 'N/A')}] {details.get('message', 'No message.')} (Type: {details.get('alert_type', 'N/A')})"
    else:
        summary += json.dumps(details) if details else "No specific details."

    return summary.strip()

# Example usage (optional, for testing this utility directly)
if __name__ == "__main__":
    print("--- Testing display_formatters.py ---")
    example_event_vital = {
        "eventId": "evt1", "patientId": "p1", "eventType": "vital_sign",
        "timestamp": "2024-07-23T10:30:00Z",
        "value": {"sign_name": "Heart Rate", "value": 78, "unit": "bpm"},
        "source": "Monitor"
    }
    example_event_obs = {
        "eventId": "evt2", "patientId": "p1", "eventType": "observation",
        "timestamp": "2024-07-23T10:35:00Z",
        "value": {"text_observation": "Patient resting comfortably.", "source": "Nurse"},
        "source": "NurseManual"
    }
    malformed_event = {"foo": "bar"}

    print(f"Formatted Vital Sign: {format_event_for_display(example_event_vital)}")
    print(f"Formatted Observation: {format_event_for_display(example_event_obs)}")
    print(f"Formatted Malformed: {format_event_for_display(malformed_event)}")
    if DATEUTIL_AVAILABLE:
        print("dateutil.parser is available.")
    else:
        print("dateutil.parser is NOT available. Install python-dateutil for robust date parsing.")
