import datetime
import json
from dateutil import parser as dateutil_parser # For parsing ISO dates if needed for filtering
import sys
import os

# --- Attempt to import functions from other agents ---
IMPORTED_SUMMARY_AGENT_MODULE = False
IMPORTED_EVENTS_LOG_MODULE = False

try:
    current_script_path = os.path.dirname(os.path.realpath(__file__))
    # Path to noah_patient_summary_agent_mvp
    summary_agent_dir = os.path.join(os.path.dirname(current_script_path), "noah_patient_summary_agent_mvp")
    if summary_agent_dir not in sys.path:
        sys.path.insert(0, summary_agent_dir)
    import patient_summary_agent
    PSA_MODULE = patient_summary_agent
    IMPORTED_SUMMARY_AGENT_MODULE = True
    print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported patient_summary_agent module.")
except ImportError as e:
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: Could not import from patient_summary_agent.py: {e}. Using local stubs for profile & summary.")
    PSA_MODULE = None # Placeholder if import fails

try:
    current_script_path = os.path.dirname(os.path.realpath(__file__))
    # Path to noah_shift_events_log_display_mvp
    events_log_dir = os.path.join(os.path.dirname(current_script_path), "noah_shift_events_log_display_mvp")
    if events_log_dir not in sys.path:
        sys.path.insert(0, events_log_dir)
    import events_log_data_prep
    ELD_MODULE = events_log_data_prep
    IMPORTED_EVENTS_LOG_MODULE = True
    print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported events_log_data_prep module.")
except ImportError as e:
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: Could not import from events_log_data_prep.py: {e}. Using local stubs for events.")
    ELD_MODULE = None # Placeholder


# --- Local Fallback Mock Data (if imports fail) ---
LOCAL_MOCK_PATIENT_PROFILES = {
    "patient789": {
        "patientId": "patient789", "name": "Alice Johnson (Local)", "dob": "1965-09-23", "mrn": "MRN78910",
        "allergies": ["Sulfa Drugs"], "principalProblem": "Post-operative recovery (Appendectomy)",
        "admissionDate": "2024-07-20T10:00:00Z", "room_no": "401"
    }
}
LOCAL_MOCK_SHIFT_EVENTS = {
    "patient789": [
        {"timestamp": "2024-07-22T13:00:00Z", "event_type": "vital_sign", "details": {"sign_name": "Pain Score", "value": "1/10", "unit": ""}},
        {"timestamp": "2024-07-22T14:15:00Z", "event_type": "observation", "details": {"text_observation": "Patient resting (local data)."}}
    ]
}

# --- Stubs using imported modules or fallbacks ---

def get_patient_profile_stub(patient_id: str) -> dict:
    """Fetches patient profile, preferably from patient_summary_agent's data."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] HANDOFF_FETCH_PROFILE: For patient_id: {patient_id}")
    if IMPORTED_SUMMARY_AGENT_MODULE:
        # Use the MOCK_PATIENT_PROFILES from the imported module
        profile = PSA_MODULE.MOCK_PATIENT_PROFILES.get(patient_id, {})
        if profile: return profile # Return if found in imported module's data
    # Fallback to local mock if import failed or patient not in imported data
    return LOCAL_MOCK_PATIENT_PROFILES.get(patient_id, {})


def get_recent_events_stub(patient_id: str, shift_duration_hours: int = 12) -> list:
    """Fetches recent events, preferably using events_log_data_prep's logic."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] HANDOFF_FETCH_EVENTS: For patient_id: {patient_id}, last {shift_duration_hours} hours.")
    if IMPORTED_EVENTS_LOG_MODULE:
        # Construct filter_criteria for get_mock_shift_events
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        start_time_iso = (now - datetime.timedelta(hours=shift_duration_hours)).isoformat()
        filters = {"time_range": {"start": start_time_iso}}
        # This function in events_log_data_prep now reads from SHARED_MOCK_EVENTS_DB (which itself might be imported or local)
        return ELD_MODULE.get_mock_shift_events(patient_id, filter_criteria=filters)
    else:
        # Fallback to local mock if import failed
        all_patient_events = LOCAL_MOCK_SHIFT_EVENTS.get(patient_id, [])
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        cutoff_time = now - datetime.timedelta(hours=shift_duration_hours)
        recent_events = [
            event for event in all_patient_events
            if dateutil_parser.isoparse(event["timestamp"]) >= cutoff_time
        ]
        recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
        return recent_events

def call_patient_summary_agent_for_handoff_stub(profile: dict, events: list) -> str:
    """Generates a handoff summary, preferably using patient_summary_agent's LLM stub."""
    patient_name = profile.get("name", "Unknown Patient")
    print(f"[{datetime.datetime.utcnow().isoformat()}] HANDOFF_AI_SUMMARY: Generating for {patient_name} using Patient Summary Agent logic.")

    if IMPORTED_SUMMARY_AGENT_MODULE:
        # We need to construct the context_data that psa_generate_summary_with_llm expects
        # For this, we might also need RAG results. Let's simulate a simple RAG query or assume no RAG for this specific handoff summary.
        rag_query_for_handoff = f"Key events and status for handoff regarding {profile.get('principalProblem', 'current stay')}"

        # Use the imported psa_query_vertex_ai_search with its own MOCK_CLINICAL_KB
        # The `patient_data` parameter for psa_query_vertex_ai_search is the profile.
        rag_results_for_handoff = PSA_MODULE.query_vertex_ai_search(profile, rag_query_for_handoff)

        context_data = {
            "patient_profile": profile,
            "event_logs": events, # These are the recent events passed in
            "rag_results": rag_results_for_handoff
        }
        # Use the imported LLM stub
        summary_str = PSA_MODULE.generate_summary_with_llm(context_data, summary_type="handoff_concise")
        return summary_str
    else:
        # Fallback to simpler local summary generation if import failed
        summary_parts = [
            f"Patient: {patient_name}, {profile.get('dob')}. Admitted: {profile.get('admissionDate', 'N/A')} for {profile.get('principalProblem', 'N/A')}.",
            f"Allergies: {', '.join(profile.get('allergies', ['None Known']))}."
        ]
        if events:
            summary_parts.append("Key events this shift (local fallback logic):")
            for event in events[:3]:
                 event_time = dateutil_parser.isoparse(event["timestamp"]).strftime("%H:%M")
                 summary_parts.append(f"  - {event_time}: {event.get('event_type','N/A')} - {str(event.get('details','N/A'))[:50]}")
        else:
            summary_parts.append("No significant events for local fallback summary.")
        return "\n".join(summary_parts)

# --- Text-to-Speech Placeholder ---
# This remains local as it's specific to the handoff agent's function

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
