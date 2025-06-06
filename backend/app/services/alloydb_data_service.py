import json
import datetime
from typing import Dict, Any, List # Added List for type hints
import uuid
import os

# Path to the schemas - adjust if service location changes relative to config
# Assuming services are in backend/app/services and config is in backend/app/config
SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "event_schemas.json")

class AlloyDBDataService:
    def __init__(self):
        self.event_schemas = {}
        self._load_event_schemas()

    def _load_event_schemas(self, schema_file_path=SCHEMA_FILE_PATH):
        """Loads event schemas from the specified JSON file."""
        try:
            with open(schema_file_path, 'r') as f:
                self.event_schemas = json.load(f)
            print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (AlloyDBService): Event schemas loaded successfully from {schema_file_path}")
        except FileNotFoundError:
            print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR (AlloyDBService): Schema file {schema_file_path} not found.")
            self.event_schemas = {}
        except json.JSONDecodeError:
            print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR (AlloyDBService): Error decoding JSON from {schema_file_path}.")
            self.event_schemas = {}

    def _validate_event_details(self, event_type: str, event_details: Dict[str, Any]) -> bool:
        """
        Validates event_details against the loaded schema for the given event_type.
        (Adapted from shift_event_capture.py)
        """
        if not self.event_schemas:
            print(f"[{datetime.datetime.utcnow().isoformat()}] WARN (AlloyDBService): Schemas not loaded. Skipping validation for type '{event_type}'.")
            return True # Skip validation if schemas aren't loaded

        schema = self.event_schemas.get(event_type)
        if not schema:
            print(f"[{datetime.datetime.utcnow().isoformat()}] WARN (AlloyDBService): No schema for event type '{event_type}'. Skipping validation.")
            return True

        required_keys = schema.get("required_keys", [])
        missing_keys = [key for key in required_keys if key not in event_details]

        if missing_keys:
            print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR (AlloyDBService): Event validation failed for type '{event_type}'. Missing keys: {missing_keys}. Event: {json.dumps(event_details)}")
            return False
        return True

    async def log_structured_event(self, patient_id: str, event_type: str, event_details: Dict[str, Any], source_override: str = None, validate: bool = True):
        """
        Processes and (simulates) storing a structured event to AlloyDB.
        (Logic combined from shift_event_capture.log_event and store_event_in_alloydb)
        TODO: Implement actual AlloyDB insertion logic.
        """
        if validate and self.event_schemas.get(event_type): # Only validate if schema exists for the type
            if not self._validate_event_details(event_type, event_details):
                print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (AlloyDBService): Event logging aborted for patient {patient_id}, type '{event_type}' due to validation failure.")
                return {"status": "error", "message": "Event validation failed"}

        # Determine the 'source' for the record
        db_source = source_override
        if not db_source:
            if "source" in event_details: # If original details had a source (e.g. for 'observation' type)
                db_source = event_details["source"]
            else:
                db_source = f"ApplicationInput_{event_type}" # Default source

        db_event_record = {
            "eventId": str(uuid.uuid4()), # Auto-generate eventId
            "patientId": patient_id,
            "eventType": event_type,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z", # Timestamp for DB record
            "value": event_details, # This is the JSONB field content
            "source": db_source
        }

        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (AlloyDBService): Simulating DB write for structured event for patientId: {patient_id}")
        print(f"  Event Data (to be stored in AlloyDB EventLogs): {json.dumps(db_event_record, indent=2)}")

        # Placeholder for actual AlloyDB interaction:
        # try:
        #   with get_alloydb_connection() as conn:
        #     with conn.cursor() as cur:
        #       cur.execute(
        #         "INSERT INTO EventLogs (eventId, patientId, eventType, timestamp, value, source) VALUES (%s, %s, %s, %s, %s, %s)",
        #         (db_event_record['eventId'], db_event_record['patientId'], db_event_record['eventType'],
        #          db_event_record['timestamp'], json.dumps(db_event_record['value']), db_event_record['source'])
        #       )
        #       conn.commit()
        #   print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Event {db_event_record['eventId']} for {patient_id} successfully logged to AlloyDB.")
        #   return {"status": "success", "eventId": db_event_record['eventId'], "message": "Event logged to AlloyDB (simulated)."}
        # except Exception as e:
        #   print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR: Failed to log event {db_event_record['eventId']} for {patient_id} to AlloyDB: {e}")
        #   return {"status": "error", "message": "Failed to log event to AlloyDB (simulated)."}

        return {"status": "success", "eventId": db_event_record['eventId'], "message": f"Event '{event_type}' for {patient_id} processed by AlloyDBDataService (simulated)."}

    async def add_core_relational_record(self, patient_id: str, record_type: str, details: Dict[str, Any]):
        """ Placeholder for writing a relational record to AlloyDB CoreRelationalRecords table. """
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (AlloyDBService): Called add_core_relational_record for patientId: {patient_id}")
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (AlloyDBService): Record Type: {record_type}, Details: {json.dumps(details)}")
        # Example AlloyDB interaction (pseudo-code from original file):
        # (Same as before)
        return {"status": "success", "message": f"Record '{record_type}' for {patient_id} added (simulated in AlloyDBDataService)."}

    # --- Helper methods for specific event types (adapted from shift_event_capture.py) ---
    async def log_vital_sign(self, patient_id: str, sign_name: str, value: Any, unit: str):
        details = {"sign_name": sign_name, "value": value, "unit": unit}
        return await self.log_structured_event(patient_id, "vital_sign", details, source_override="ClinicalDevice_ManualEntry")

    async def log_intervention(self, patient_id: str, description: str, medication: Dict[str, Any] = None, procedure: str = None):
        details = {"description": description}
        if medication: details["medication_administered"] = medication
        if procedure: details["procedure_performed"] = procedure
        return await self.log_structured_event(patient_id, "intervention", details, source_override="NurseInput_Intervention")

    async def log_observation(self, patient_id: str, text_observation: str, source: str = "manual_text"):
        # 'source' here is part of the event_details for 'observation' schema
        details = {"text_observation": text_observation, "source": source}
        return await self.log_structured_event(patient_id, "observation", details)

    async def log_general_note(self, patient_id: str, note_content: str, source: str = "manual_text_note"):
        details = {"note_content": note_content}
        return await self.log_structured_event(patient_id, "general_note", details, source_override=source)

    async def transcribe_voice_input(self, mock_audio_blob: str) -> str:
        """ Placeholder for Speech-to-Text. (Moved from shift_event_capture.py) """
        print(f"[{datetime.datetime.utcnow().isoformat()}] SIMULATE_STT (AlloyDBService): Transcribing mock audio blob: {mock_audio_blob}")
        if "pain" in mock_audio_blob.lower(): return "Patient reports increasing pain in the left knee, rated 7 out of 10."
        if "medication" in mock_audio_blob.lower(): return "Administered 500 milligrams of Paracetamol PO for fever."
        if "family" in mock_audio_blob.lower(): return "Patient's family called requesting an update, provided general status."
        return "Unclear audio input, transcription placeholder."

    async def log_general_note_from_voice(self, patient_id: str, mock_audio_blob: str):
        """ Transcribes voice and logs as a general note. (Moved from shift_event_capture.py) """
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (AlloyDBService): Initiating voice note for patient {patient_id} using {mock_audio_blob}")
        transcribed_text = await self.transcribe_voice_input(mock_audio_blob)
        if transcribed_text:
            return await self.log_general_note(patient_id, transcribed_text, source="voice_transcription_note")
        else:
            print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR (AlloyDBService): Transcription failed for {mock_audio_blob}.")
            return None

    async def log_alert_notification(self, message: str, alert_type: str, priority: str, patient_id: str = None, source_system: str = "ApplicationInternal"):
        details = {
            "alert_type": alert_type,
            "message": message,
            "priority": priority,
            "source_system": source_system
        }
        # patient_id is optional for alerts, log_structured_event needs to handle None patient_id if applicable for the event_type
        # For schema validation, if patient_id is sometimes not present for 'alert_notification', schema should reflect that.
        # Current schema implies patient_id is optional.
        if patient_id: # Pass patient_id only if it's provided
             return await self.log_structured_event(patient_id, "alert_notification", details, source_override=f"AlertSystem_{source_system}")
        else: # If patient_id is not provided for an alert
             # The log_structured_event method expects a patient_id.
             # This case needs clarification: should we log alerts not tied to a patient?
             # If so, log_structured_event signature or logic might need adjustment,
             # or a different logging method for system-level alerts.
             # For now, let's assume alerts are patient-specific if patient_id is given.
             # If not, we might log it differently or skip logging via this method.
             print(f"[{datetime.datetime.utcnow().isoformat()}] WARN (AlloyDBService): log_alert_notification called without patient_id. Alert not logged via patient-specific path.")
             # Simulate a non-patient specific log or return an appropriate response
             return {"status": "warning", "message": "Alert logged (simulated, no patient_id specified)."}

        async def list_events_for_patient(self, patient_id: str, limit: int = 50, order_by: str = "timestamp", descending: bool = True) -> List[Dict[str, Any]]:
            """
            Placeholder for fetching a list of events for a patient from AlloyDB EventLogs table.
            TODO: Implement actual AlloyDB query logic.
            """
            print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (AlloyDBService): Called list_events_for_patient for patientId: {patient_id} (Simulated - returning empty list)")
            # In a real implementation, this would query the AlloyDB 'EventLogs' table
            # Example pseudo-code:
            # try:
            #   with get_alloydb_connection() as conn:
            #     with conn.cursor(row_factory=dict_row_factory) as cur: # Assuming rows returned as dicts
            #       direction = "DESC" if descending else "ASC"
            #       # Ensure order_by column is safe to prevent SQL injection if dynamic
            #       safe_order_by = order_by if order_by in ["timestamp", "eventType"] else "timestamp" # Example safe columns
            #       query = f"SELECT eventId, patientId, eventType, timestamp, value, source FROM EventLogs WHERE patientId = %s ORDER BY {safe_order_by} {direction} LIMIT %s"
            #       cur.execute(query, (patient_id, limit))
            #       events = cur.fetchall()
            #       return events
            # except Exception as e:
            #   print(f"[{datetime.datetime.utcnow().isoformat()}] ERROR (AlloyDBService): Failed to list events for patient {patient_id} from AlloyDB: {e}")
            #   return []
            return []

# Example of how this service might be instantiated and used (optional, for clarity)
# This would typically be handled by a dependency injection system in a FastAPI app.
# alloydb_service = AlloyDBDataService()
