import datetime
import json
from dateutil import parser as dateutil_parser # For parsing ISO dates if needed for filtering

# --- Mock Data Stores & Simplified Stubs ---

MOCK_PATIENT_PROFILES = {
    "patient789": {
        "patientId": "patient789",
        "name": "Alice Johnson",
        "dob": "1965-09-23",
        "mrn": "MRN78910",
        "allergies": ["Sulfa Drugs"],
        "principalProblem": "Post-operative recovery (Appendectomy)",
        "admissionDate": "2024-07-20T10:00:00Z",
        "room_no": "401"
    }
}

MOCK_SHIFT_EVENTS = {
    "patient789": [
        {"timestamp": "2024-07-22T08:00:00Z", "event_type": "vital_sign", "details": {"sign_name": "Pain Score", "value": "2/10", "unit": ""}},
        {"timestamp": "2024-07-22T09:15:00Z", "event_type": "intervention", "details": {"description": "Administered Acetaminophen 1g PO for mild pain."}},
        {"timestamp": "2024-07-22T10:30:00Z", "event_type": "observation", "details": {"text_observation": "Patient ambulated to bathroom with SBA, tolerated well."}},
        {"timestamp": "2024-07-22T12:00:00Z", "event_type": "vital_sign", "details": {"sign_name": "Temperature", "value": 37.0, "unit": "C"}},
        {"timestamp": "2024-07-22T14:00:00Z", "event_type": "general_note", "details": {"note_content": "Incision site clean, dry, and intact. No signs of infection."}},
        # Older events to test filtering
        {"timestamp": "2024-07-21T20:00:00Z", "event_type": "observation", "details": {"text_observation": "Patient resting comfortably."}},
        {"timestamp": "2024-07-21T18:00:00Z", "event_type": "vital_sign", "details": {"sign_name": "BP", "value": "130/75", "unit": "mmHg"}},
    ]
}

def get_patient_profile_stub(patient_id: str) -> dict:
    """Simulates fetching patient profile."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB_FETCH_PROFILE: For patient_id: {patient_id}")
    return MOCK_PATIENT_PROFILES.get(patient_id, {})

def get_recent_events_stub(patient_id: str, shift_duration_hours: int = 12) -> list:
    """
    Simulates fetching recent events for a patient from the last X hours.
    Events are assumed to be sorted newest first in the mock store for simplicity if filtering were more complex.
    For this stub, we'll filter based on the provided shift_duration_hours.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB_FETCH_EVENTS: For patient_id: {patient_id}, last {shift_duration_hours} hours.")
    all_patient_events = MOCK_SHIFT_EVENTS.get(patient_id, [])
    if not all_patient_events:
        return []

    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) # Ensure 'now' is offset-aware
    cutoff_time = now - datetime.timedelta(hours=shift_duration_hours)

    recent_events = [
        event for event in all_patient_events
        if dateutil_parser.isoparse(event["timestamp"]) >= cutoff_time
    ]
    # Typically, events are already sorted chronologically or reverse chronologically from DB.
    # Here, ensure they are sorted for consistent summary generation if needed (newest first for this example)
    recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB_FETCH_EVENTS: Found {len(recent_events)} recent events.")
    return recent_events

def call_patient_summary_agent_for_handoff_stub(profile: dict, events: list) -> str:
    """
    Simulates calling the Patient Summary Agent to get a concise shift summary.
    """
    patient_name = profile.get("name", "Unknown Patient")
    print(f"[{datetime.datetime.utcnow().isoformat()}] STUB_AI_SUMMARY: Generating handoff summary for {patient_name}.")

    summary_parts = [
        f"Patient: {patient_name}, {profile.get('dob')}. Admitted: {profile.get('admissionDate', 'N/A')} for {profile.get('principalProblem', 'N/A')}.",
        f"Allergies: {', '.join(profile.get('allergies', ['None Known']))}."
    ]
    if events:
        summary_parts.append("Key events this shift:")
        for event in events[:3]: # Include top 3 recent events for brevity
            event_time = dateutil_parser.isoparse(event["timestamp"]).strftime("%H:%M")
            if event["event_type"] == "vital_sign":
                summary_parts.append(f"  - {event_time}: Vital: {event['details']['sign_name']} {event['details']['value']} {event['details']['unit']}")
            elif event["event_type"] == "observation":
                summary_parts.append(f"  - {event_time}: Obs: {event['details']['text_observation'][:50]}...")
            elif event["event_type"] == "intervention":
                 summary_parts.append(f"  - {event_time}: Intervention: {event['details']['description'][:50]}...")
            else:
                summary_parts.append(f"  - {event_time}: {event['event_type'].replace('_',' ').title()}: {str(event['details'])[:50]}...")
    else:
        summary_parts.append("No significant events logged in the recent period for summary.")

    return "\n".join(summary_parts)

# --- Text-to-Speech Placeholder ---

def call_tts_service_stub(text_to_speak: str, language_code: str = "en-US", patient_id: str = "default") -> str:
    """
    Simulates a call to a Text-to-Speech (TTS) service.
    Prints the text and returns a mock audio file reference.
    """
    print(f"\n[{datetime.datetime.utcnow().isoformat()}] STUB_TTS_CALL: Synthesizing audio for language: {language_code}")
    print(f"  Text to synthesize: \"{text_to_speak[:100]}...\" (length: {len(text_to_speak)})") # Print a snippet

    mock_audio_filename = f"handoff_audio_{patient_id}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.mp3"
    print(f"  Mock audio reference generated: {mock_audio_filename}")
    return mock_audio_filename

# --- Main Handoff Data Generation Function ---

def generate_handoff_data(patient_id: str, manual_top_priorities: list[str], manual_params_to_monitor: list[str]) -> dict:
    """
    Generates the data structure for a patient handoff report.
    """
    print(f"\n[{datetime.datetime.utcnow().isoformat()}] HANDOFF_GEN: Starting for patient_id: {patient_id}")

    # 1. Fetch patient profile
    profile = get_patient_profile_stub(patient_id)
    if not profile:
        print(f"[{datetime.datetime.utcnow().isoformat()}] HANDOFF_GEN_ERROR: Profile not found for {patient_id}.")
        return {"error": "Patient profile not found"}

    # 2. Fetch recent events (e.g., last 12 hours)
    recent_events = get_recent_events_stub(patient_id, shift_duration_hours=12)

    # 3. Generate AI summary
    ai_summary = call_patient_summary_agent_for_handoff_stub(profile, recent_events)

    # 4. Construct text for TTS (AI summary + key manual points)
    tts_text_parts = [f"Handoff for {profile.get('name', 'this patient')}.", ai_summary]
    if manual_top_priorities:
        tts_text_parts.append("Key priorities are:")
        for priority in manual_top_priorities:
            tts_text_parts.append(priority + ".")
    if manual_params_to_monitor:
        tts_text_parts.append("Parameters to monitor closely include:")
        for param in manual_params_to_monitor:
            tts_text_parts.append(param + ".")

    full_tts_text = " ".join(tts_text_parts)

    # 5. Call TTS service stub
    voice_audio_ref = call_tts_service_stub(full_tts_text, patient_id=patient_id)

    # 6. Construct the handoff data dictionary
    handoff_data = {
        "patient_id": patient_id,
        "patient_name": profile.get("name", "N/A"), # Added for UI convenience
        "room_no": profile.get("room_no", "N/A"),   # Added for UI convenience
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "ai_generated_shift_summary": ai_summary,
        "top_priorities_for_incoming_nurse": manual_top_priorities,
        "parameters_to_monitor_closely": manual_params_to_monitor,
        "voice_handoff_available": True if voice_audio_ref else False,
        "voice_handoff_audio_ref": voice_audio_ref
    }

    print(f"[{datetime.datetime.utcnow().isoformat()}] HANDOFF_GEN: Data generation complete for {patient_id}.")
    return handoff_data

if __name__ == "__main__":
    test_patient_id = "patient789"

    print("--- Handoff Summary Generator Demo ---")

    # Example manual inputs from the outgoing nurse
    example_priorities = [
        "Monitor for any signs of post-operative infection (fever, increased pain at incision site).",
        "Ensure adequate pain relief, reassess pain score Q4H and PRN.",
        "Encourage ambulation at least TID."
    ]
    example_params_to_monitor = [
        "Temperature (report if > 38.0 C).",
        "Pain score.",
        "Incision site appearance (redness, swelling, discharge)."
    ]

    # Generate handoff data
    handoff_report_data = generate_handoff_data(
        patient_id=test_patient_id,
        manual_top_priorities=example_priorities,
        manual_params_to_monitor=example_params_to_monitor
    )

    print("\n--- Generated Handoff Data ---")
    print(json.dumps(handoff_report_data, indent=2))

    # Test case for a patient not found
    print("\n--- Testing with a non-existent patient ---")
    non_existent_patient_handoff = generate_handoff_data(
        "patient_unknown",
        ["Test priority"],
        ["Test param"]
    )
    print(json.dumps(non_existent_patient_handoff, indent=2))

    print("\n--- Demo Completed ---")
