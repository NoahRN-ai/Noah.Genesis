import json
import datetime
import uuid
import os
import sys

# --- Shared Mock Event Store ---
# This will be populated by store_event_in_alloydb
# Keyed by patient_id, value is a list of event dicts
SHARED_MOCK_EVENTS_DB = {}

# --- Event Schemas ---
EVENT_SCHEMAS = {}

# For cross-script import if events_log_data_prep.py is in a different root
# This might need adjustment based on how the execution environment handles paths.
# Assuming they might be siblings in a larger 'noah_agents' directory for import.
# If running scripts individually from their own directories, this path might need to be relative like '../../noah_shift_event_capture_agent_mvp'
# For this subtask, we'll try a direct import path assuming a common root or adjusted PYTHONPATH.
# If direct import fails, this part will be re-evaluated.

def add_to_shared_events(patient_id: str, event_data: dict):
    """Helper to add event to the shared store, ensuring patient_id key exists."""
    if patient_id not in SHARED_MOCK_EVENTS_DB:
        SHARED_MOCK_EVENTS_DB[patient_id] = []
    SHARED_MOCK_EVENTS_DB[patient_id].append(event_data)

def load_event_schemas(schema_file_path="event_schemas.json"):
    """Loads event schemas from the specified JSON file."""
    global EVENT_SCHEMAS
    try:
        with open(schema_file_path, 'r') as f:
            EVENT_SCHEMAS = json.load(f)
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Event schemas loaded successfully from {schema_file_path}")
    except FileNotFoundError:
        print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR: Schema file {schema_file_path} not found. No schema validation will be performed.")
        EVENT_SCHEMAS = {}
    except json.JSONDecodeError:
        print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR: Error decoding JSON from {schema_file_path}. No schema validation will be performed.")
        EVENT_SCHEMAS = {}

def validate_event_details(event_type: str, event_details: dict) -> bool:
    """
    Validates event_details against the loaded schema for the given event_type.
    Checks only for required keys. More complex validation can be added.
    """
    if not EVENT_SCHEMAS:
        # print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: No schemas loaded, skipping validation for event type '{event_type}'.")
        return True # Skip validation if schemas aren't loaded

    schema = EVENT_SCHEMAS.get(event_type)
    if not schema:
        print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: No schema found for event type '{event_type}'. Skipping validation.")
        return True # Allow events not in schema, or handle as error

    required_keys = schema.get("required_keys", [])
    missing_keys = [key for key in required_keys if key not in event_details]

    if missing_keys:
        print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR: Event validation failed for type '{event_type}'. Missing keys: {missing_keys}. Event: {event_details}")
        return False

    # Potentially add more validation here (e.g., type checking, value constraints)
    # For now, just checking presence of required keys.

    return True

def store_event_in_alloydb(event_data: dict):
    """
    Placeholder for storing event data in AlloyDB.
    Simulates writing to the EventLogs table.
    The actual `event_data` should align with `alloydb_schemas.sql` from Step 1:
    `eventId`, `patientId`, `eventType`, `timestamp`, `value` (JSONB/TEXT), `source`.
    """
    # The log_event function will prepare a structure that's close to this.
    # We might need a transformation step here if log_event's output isn't a direct match.

    # Structure for SHARED_MOCK_EVENTS_DB should be consistent with what
    # events_log_data_prep.py expects.
    # The `log_event` function already structures `full_event_data` with:
    # "timestamp", "patient_id", "event_type", "details", "source"
    # We'll add a unique "event_id" here as well.

    # Make a copy to avoid modifying the dict passed to this function if it's reused
    shared_event_record = event_data.copy()
    shared_event_record["event_id"] = str(uuid.uuid4())


    # Add to SHARED_MOCK_EVENTS_DB
    patient_id = shared_event_record.get("patient_id")
    if patient_id:
        add_to_shared_events(patient_id, shared_event_record)
        print(f"[{datetime.datetime.utcnow().isoformat()}] SIMULATE_DB_WRITE (SHARED_MOCK_EVENTS_DB): Event {shared_event_record['event_id']} for patient {patient_id} logged.")
        print(f"  Current SHARED_MOCK_EVENTS_DB for {patient_id}: {SHARED_MOCK_EVENTS_DB[patient_id][-1]}") # Print last added event
    else:
        # Handle events without a patient_id (e.g., system alerts not tied to a patient)
        # For now, we'll add them to a "general_events" key or similar if needed,
        # or decide that all events must have a patient_id for this shared store.
        # For this iteration, let's assume patient_id is generally present for patient-centric events.
        # If an event truly has no patient_id, it might be logged elsewhere or handled differently.
        # For system alerts that might have an optional patient_id, the calling function should decide.
        if shared_event_record.get("event_type") == "alert_notification" and not patient_id:
            # Example: store system-wide alerts under a specific key
            system_alerts_key = "_system_alerts"
            add_to_shared_events(system_alerts_key, shared_event_record)
            print(f"[{datetime.datetime.utcnow().isoformat()}] SIMULATE_DB_WRITE (SHARED_MOCK_EVENTS_DB): System Alert {shared_event_record['event_id']} logged under '{system_alerts_key}'.")
        else:
            print(f"[{datetime.datetime.utcnow().isoformat()}] WARN_DB_WRITE: Event {shared_event_record['event_id']} lacks patient_id and is not a general system alert. Not added to SHARED_MOCK_EVENTS_DB by default.")


    # The original print to simulate AlloyDB write can remain for conceptual clarity
    # but the primary storage for this subtask's goal is SHARED_MOCK_EVENTS_DB.
    # To avoid confusion, let's make it clear this is now primarily about the shared mock store.
    # print(f"[{datetime.datetime.utcnow().isoformat()}] SIMULATE_DB_WRITE (AlloyDB - EventLogs):")
    # print(json.dumps(db_record, indent=2)) # This was the old db_record structure

    # In a real implementation:
    # conn = get_alloydb_connection()
    # cursor = conn.cursor()
    # cursor.execute("INSERT INTO EventLogs (eventId, patientId, eventType, timestamp, value, source) VALUES (%s, %s, %s, %s, %s, %s)",
    #                (db_record['eventId'], db_record['patientId'], db_record['eventType'],
    #                 db_record['timestamp'], db_record['value'], db_record['source']))
    # conn.commit()

def transcribe_voice_input(mock_audio_blob: str) -> str:
    """
    Placeholder for calling a Speech-to-Text service.
    Takes a mock audio blob identifier and returns mock transcribed text.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] SIMULATE_STT: Transcribing mock audio blob: {mock_audio_blob}")
    if "pain" in mock_audio_blob.lower():
        return "Patient reports increasing pain in the left knee, rated 7 out of 10."
    elif "medication" in mock_audio_blob.lower():
        return "Administered 500 milligrams of Paracetamol PO for fever."
    elif "family" in mock_audio_blob.lower():
        return "Patient's family called requesting an update, provided general status."
    else:
        return "Unclear audio input, transcription placeholder."

def log_event(patient_id: str, event_type: str, event_details: dict, source_override: str = None, validate: bool = True):
    """
    Core event logging function.
    Adds timestamp, merges data, optionally validates, and calls storage placeholder.
    """
    if validate and EVENT_SCHEMAS.get(event_type): # Only validate if schema exists for this type
        if not validate_event_details(event_type, event_details):
            print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Event logging aborted due to validation failure for event type '{event_type}'.")
            return

    full_event_data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "patient_id": patient_id,
        "event_type": event_type,
        "details": event_details # Nests original event_details under 'details'
    }

    # Determine the 'source' for the AlloyDB record
    # If event_details has a 'source' (like in 'observation'), use it.
    # If source_override is provided (like for voice), use it.
    # Default to a generic source based on event_type or "Application".
    if source_override:
        full_event_data["source"] = source_override
    elif "source" in event_details:
         full_event_data["source"] = event_details["source"]
    else:
        full_event_data["source"] = f"ApplicationInput_{event_type}"


    print(f"[{datetime.datetime.utcnow().isoformat()}] LOGGING_EVENT: Type: {event_type}, Patient: {patient_id}")
    store_event_in_alloydb(full_event_data)
    return full_event_data


# --- Helper functions for specific event types ---

def log_vital_sign(patient_id: str, sign_name: str, value: any, unit: str):
    """Logs a vital sign event."""
    details = {
        "sign_name": sign_name,
        "value": value,
        "unit": unit
    }
    return log_event(patient_id, "vital_sign", details, source_override="ClinicalDevice_ManualEntry")

def log_intervention(patient_id: str, description: str, medication: dict = None, procedure: str = None):
    """Logs an intervention event."""
    details = {
        "description": description
    }
    if medication:
        details["medication_administered"] = medication
    if procedure:
        details["procedure_performed"] = procedure
    return log_event(patient_id, "intervention", details, source_override="NurseInput_Intervention")

def log_observation(patient_id: str, text_observation: str, source: str = "manual_text"):
    """Logs a text observation."""
    details = {
        "text_observation": text_observation,
        "source": source # This source is part of the event_details for observation schema
    }
    # The source for the DB record will be taken from details.source here
    return log_event(patient_id, "observation", details)


def log_general_note(patient_id: str, note_content: str, source: str = "manual_text_note"):
    """Logs a general text note."""
    details = {
        "note_content": note_content
    }
    return log_event(patient_id, "general_note", details, source_override=source)

def log_general_note_from_voice(patient_id: str, mock_audio_blob: str):
    """Transcribes voice input and logs it as a general note."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Initiating voice note for patient {patient_id} using {mock_audio_blob}")
    transcribed_text = transcribe_voice_input(mock_audio_blob)
    if transcribed_text:
        return log_general_note(patient_id, transcribed_text, source="voice_transcription_note")
    else:
        print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR: Transcription failed or returned empty for {mock_audio_blob}. Note not logged.")
        return None

def log_alert_notification(message: str, alert_type: str, priority: str, patient_id: str = None, source_system: str = "ApplicationInternal"):
    """Logs an alert notification."""
    details = {
        "alert_type": alert_type,
        "message": message,
        "priority": priority,
        "source_system": source_system
    }
    # patient_id is optional for alerts, so pass it directly to log_event
    # The source for the DB record will be set by log_event using source_override
    return log_event(patient_id, "alert_notification", details, source_override=f"AlertSystem_{source_system}")


if __name__ == "__main__":
    print("-" * 30)
    print("Initializing Shift Event Capture Agent (MVP)...")
    load_event_schemas() # Load schemas on startup
    print("-" * 30)

    patient_id_example = "PATIENT_789"
    patient_id_example_2 = "PATIENT_101"

    print(f"\n--- Logging events for Patient: {patient_id_example} ---")

    # Log a vital sign
    log_vital_sign(patient_id_example, sign_name="Heart Rate", value=78, unit="bpm")
    print("---")
    log_vital_sign(patient_id_example, sign_name="Blood Pressure", value="120/80", unit="mmHg") # Example with string value
    print("---")

    # Log an intervention
    log_intervention(patient_id_example,
                     description="Administered pain medication.",
                     medication={"name": "Morphine", "dosage": "5mg", "route": "IV"})
    print("---")
    log_intervention(patient_id_example,
                     description="Assisted patient with ambulation to hallway and back.",
                     procedure="Ambulation Assistance")
    print("---")

    # Log a manual text observation
    log_observation(patient_id_example,
                    text_observation="Patient reports feeling nauseous after medication.",
                    source="manual_text")
    print("---")

    # Log a general note from text
    log_general_note(patient_id_example,
                     note_content="Patient's family visited and expressed concerns about discharge planning.")
    print("---")

    # Log a general note from simulated voice input
    log_general_note_from_voice(patient_id_example, mock_audio_blob="patient_reports_pain_in_knee.wav")
    print("---")
    log_general_note_from_voice(patient_id_example_2, mock_audio_blob="doctor_ordered_new_medication_for_fever.wav")
    print("---")


    print(f"\n--- Logging System Alerts (not patient-specific or patient-specific) ---")
    # Log a system alert (not patient-specific)
    log_alert_notification(message="Low disk space on server XYZ.",
                           alert_type="SystemMaintenance",
                           priority="Medium",
                           source_system="InfrastructureMonitoring")
    print("---")
    # Log a patient-specific alert
    log_alert_notification(patient_id=patient_id_example_2,
                           message="Critical potassium level: 5.8 mmol/L",
                           alert_type="CriticalLabValue",
                           priority="High",
                           source_system="LabInformationSystem")
    print("---")

    # Example of a call that might fail validation (if schemas were stricter or a key is missed)
    print("\n--- Example of an event that might fail validation (if description was required and missing) ---")
    # This will pass with current schema as only 'description' is required for intervention.
    # If we made 'medication_administered' required and didn't pass it, it would fail.
    log_event(patient_id_example, "intervention", {"procedure_performed": "Test procedure only"})
    print("---")

    # Example of an event type not in schema (will be logged with a warning if validation is on for all)
    print("\n--- Example of an event type not present in event_schemas.json ---")
    log_event(patient_id_example, "custom_event_type", {"custom_field": "value123"}, validate=True) # 'validate' is true by default
    print("---")


    print("\nShift Event Capture Agent (MVP) example usage completed.")
    print("-" * 30)
