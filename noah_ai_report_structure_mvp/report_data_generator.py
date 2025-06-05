import json
import datetime
import sys
import os

# --- Attempt to import functions from patient_summary_agent.py ---
IMPORTED_PATIENT_SUMMARY_AGENT_FUNCTIONS = False
try:
    current_script_path = os.path.dirname(os.path.realpath(__file__))
    # Path to noah_patient_summary_agent_mvp directory
    summary_agent_dir = os.path.join(os.path.dirname(current_script_path), "noah_patient_summary_agent_mvp")

    if summary_agent_dir not in sys.path:
        sys.path.insert(0, summary_agent_dir)

    from patient_summary_agent import (
        get_mock_patient_data as psa_get_mock_patient_data,
        get_mock_event_logs as psa_get_mock_event_logs, # For context if needed by LLM
        query_vertex_ai_search as psa_query_vertex_ai_search,
        generate_summary_with_llm as psa_generate_summary_with_llm,
        MOCK_PATIENT_PROFILES as PSA_MOCK_PATIENT_PROFILES, # Accessing its mock data
        MOCK_EVENT_LOGS as PSA_MOCK_EVENT_LOGS,
        MOCK_CLINICAL_KB as PSA_MOCK_CLINICAL_KB
    )
    IMPORTED_PATIENT_SUMMARY_AGENT_FUNCTIONS = True
    print(f"[{datetime.datetime.utcnow().isoformat()}] INFO: Successfully imported functions from patient_summary_agent.py.")
except ImportError as e:
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: Could not import from patient_summary_agent.py: {e}.")
    print(f"[{datetime.datetime.utcnow().isoformat()}] WARN: report_data_generator.py will use its own local mocks for patient profiles and RAG summary.")
    # Define local fallbacks if import fails
    PSA_MOCK_PATIENT_PROFILES = {
        "patientA123": {"patientId": "patientA123", "name": "Eleanor Vance (Local Fallback)", "dob": "1958-03-12", "principalProblem": "CHF", "allergies": ["Penicillin"]},
        "patientB456": {"patientId": "patientB456", "name": "Marcus Cole (Local Fallback)", "dob": "1972-11-25", "principalProblem": "Pneumonia", "allergies": []}
    }
    PSA_MOCK_EVENT_LOGS = {} # Not strictly needed if RAG focuses on problem
    PSA_MOCK_CLINICAL_KB = []


# --- Consolidated Mock Data Stores & Access Functions ---
# Use patient_summary_agent's mock data if available, otherwise use local fallbacks.

def get_mock_patient_profile(patient_id: str) -> dict:
    """
    Fetches patient profile data. Uses imported data from patient_summary_agent if available.
    This function in report_data_generator.py will now also add fields expected by Section II,
    if they are not present in the profile from patient_summary_agent.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DB_FETCH (Report Gen): Getting patient profile for {patient_id}")
    if IMPORTED_PATIENT_SUMMARY_AGENT_FUNCTIONS:
        # Fetch core profile from patient_summary_agent's data
        base_profile = psa_get_mock_patient_data(patient_id) # This is actually direct dict access in psa
        if not base_profile: # psa_get_mock_patient_data in summary agent returns None if not found
             base_profile = PSA_MOCK_PATIENT_PROFILES.get(patient_id, {}) # Ensure we get a dict
    else:
        # Fallback to local mock if import failed
        base_profile = PSA_MOCK_PATIENT_PROFILES.get(patient_id, {})

    # Augment with additional fields needed for Section II, if not already present
    # These are specific to how report_data_generator structures its Section II.
    # This simulates fetching from different parts of an EMR or composing data.
    extended_profile_details = {
        "patientA123": {
            "room_no": "301A", "isolationPrecautions": "Contact Precautions", "codeStatus": "Full Code",
            "admissionDate": "2024-07-10",
            "consulting_physicians": ["Dr. Emily Carter (Cardiology)", "Dr. Ben Stern (Nephrology)"],
            "emergencyContact": {"name": "Samuel Vance (Son)", "phone": "555-0101"}
        },
        "patientB456": {
            "room_no": "302B", "isolationPrecautions": "Standard", "codeStatus": "DNR/DNI",
            "admissionDate": "2024-07-15",
            "consulting_physicians": ["Dr. Anya Sharma (Pulmonology)"],
            "emergencyContact": {"name": "Lena Cole (Wife)", "phone": "555-0202"}
        }
    }
    # Merge base_profile with extended_details. Extended details can override if needed for Section II.
    # Or, more carefully, only add if keys are missing from base_profile.
    # For MVP, let's assume a simple merge, with extended_profile_details providing specific Section II fields.
    final_profile = {**base_profile, **extended_profile_details.get(patient_id, {})}
    # Ensure essential keys from base_profile are not lost if not in extended_profile_details
    for key in ["patientId", "name", "dob", "mrn", "allergies", "principalProblem"]:
        if key not in final_profile and key in base_profile:
            final_profile[key] = base_profile[key]

    return final_profile


MOCK_FIRESTORE_DATA = { # Keep this local for "About Me", "Our Goals", etc.
    "patientA123": {
        "about_me": "Retired librarian, enjoys reading and classical music. Lives with her son. Values clear communication.",
        "our_goals": "Manage CHF symptoms, improve mobility, and return home with support.",
        "social_history_highlights": "Widowed, non-smoker, occasional wine. Strong family support."
    },
    "patientB456": {
        "about_me": "Software developer, avid cyclist. Eager to get back to work and activities.",
        "our_goals": "Resolve pneumonia, improve respiratory function, and manage fever.",
        "social_history_highlights": "Married, non-smoker, exercises regularly. Generally healthy lifestyle."
    }
}


def get_mock_firestore_data(patient_id: str, data_key: str) -> dict: # Renamed from original to avoid conflict
    """Simulates fetching specific data (e.g., 'About Me') for a patient from Firestore."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DB_FETCH (Report Gen): Getting Firestore data for {patient_id}, key: {data_key}")
    patient_data = MOCK_FIRESTORE_DATA.get(patient_id, {})
    return patient_data.get(data_key, f"No '{data_key}' data found for {patient_id}")


# --- RAG Integration using imported functions ---
def fetch_patient_history_summary_from_rag(patient_id: str) -> dict:
    """
    Uses imported functions from patient_summary_agent.py to simulate RAG
    and generate a history-focused summary.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] RAG_CALL (Report Gen): Fetching history summary for {patient_id} via Patient Summary Agent logic.")

    if not IMPORTED_PATIENT_SUMMARY_AGENT_FUNCTIONS:
        print(f"[{datetime.datetime.utcnow().isoformat()}] RAG_CALL_WARN: Patient Summary Agent functions not imported. Using local RAG fallback.")
        # Fallback to original MOCK_RAG_HISTORY_SUMMARIES if import failed
        original_mock_rag = { # Keep a copy of the original simple mock for this fallback
            "patientA123": {"past_medical_history": "Hypertension (10 years), Type 2 Diabetes (5 years).", "surgical_history": "Appendectomy (1985)."},
            "patientB456": {"past_medical_history": "Asthma (childhood).", "surgical_history": "None."}
        }
        return original_mock_rag.get(patient_id, {
            "past_medical_history": "Fallback: No RAG data.",
            "surgical_history": "Fallback: No RAG data."
        })

    # 1. Get patient data (profile) using the imported function's data source
    # patient_data_for_rag = psa_get_mock_patient_data(patient_id) # This is direct dict access in psa
    patient_data_for_rag = PSA_MOCK_PATIENT_PROFILES.get(patient_id, {})
    if not patient_data_for_rag:
        return {"past_medical_history": "Patient profile not found for RAG.", "surgical_history": ""}

    # 2. Formulate a query for RAG (e.g., based on principal problem or general history)
    # The RAG in patient_summary_agent is more about finding relevant clinical KB for the *current problem*.
    # For *history*, the RAG query might be different or we might use a different part of the LLM summary.
    # Let's assume the "principalProblem" is a good starting point for a RAG query for relevant history context.
    rag_query = f"Key historical context for {patient_data_for_rag.get('principalProblem', 'current condition')}"

    # 3. Call the imported RAG query function
    # Note: psa_query_vertex_ai_search in patient_summary_agent.py uses its own MOCK_CLINICAL_KB
    # and patient_data_for_rag (which is MOCK_PATIENT_PROFILES from its own scope)
    # We need to ensure it can be called correctly here.
    # The `patient_data` param in `psa_query_vertex_ai_search` is `patient_data_for_rag` here.
    rag_results = psa_query_vertex_ai_search(patient_data_for_rag, rag_query) # Uses PSA_MOCK_CLINICAL_KB

    # 4. Get events for context (optional, but good for a comprehensive LLM call)
    # event_logs_for_rag = psa_get_mock_event_logs(patient_id) # Also direct dict access in psa
    event_logs_for_rag = PSA_MOCK_EVENT_LOGS.get(patient_id, [])


    # 5. Construct context for the LLM, focusing on generating PMH/PSH
    # The `generate_summary_with_llm` from patient_summary_agent is quite broad.
    # We might want a more targeted prompt here if we were calling a real LLM.
    # For this simulation, we'll call it and try to extract relevant parts, or make a specific type.
    context_for_llm = {
        "patient_profile": patient_data_for_rag,
        "event_logs": event_logs_for_rag, # Could be empty if not relevant for pure history
        "rag_results": rag_results
    }

    # Request a specific type of summary if the LLM stub supports it, or parse from a general one.
    # Let's assume "history_recap" is a conceptual summary type.
    llm_summary_response = psa_generate_summary_with_llm(context_for_llm, summary_type="history_recap")

    # For this MVP, we'll parse the llm_summary_response string for PMH/PSH.
    # This is a simplification; a real LLM call would be structured for this.
    # Let's assume the llm_summary_response might contain sections like "Past Medical History:"
    # For this stub, we'll just use the RAG results more directly or a simplified summary.

    # Simplified approach for this step:
    # Assume RAG results give us some keywords, and LLM crafts it.
    # The current psa_generate_summary_with_llm doesn't explicitly break out PMH/PSH.
    # So, let's construct a mock PMH/PSH from the RAG results for now.
    pmh_parts = []
    psh_parts = []
    if rag_results:
        for doc in rag_results:
            # Crude check if title seems like PMH or PSH for this mock
            if "protocol" in doc.get("title","").lower() or "management" in doc.get("title","").lower():
                 pmh_parts.append(doc.get("title"))
            else:
                psh_parts.append(doc.get("title")) # Simplistic, just to show linkage

    return {
        "past_medical_history": f"Relevant conditions (simulated RAG via Patient Summary Agent): {', '.join(pmh_parts) if pmh_parts else 'None specified by RAG.'}. Based on query: '{rag_query}'",
        "surgical_history": f"Procedures (simulated RAG via Patient Summary Agent): {', '.join(psh_parts) if psh_parts else 'None specified by RAG.'}"
    }


# --- Data Population Functions for Each Section ---

def populate_section_i_system_overview() -> dict:
    """Populates data for Section I: System Overview."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] REPORT_GEN: Populating Section I - System Overview")
    now = datetime.datetime.utcnow()
    return {
        "current_date_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "shift_info": f"{now.strftime('%A, %B %d, %Y')} - Day Shift (07:00 - 19:00)", # Example shift
        "reporting_nurse": "Sarah Miller, RN",
        "receiving_nurses": ["John Davis, RN", "Maria Rodriguez, RN"],
        "unit_census_overview": "Unit: Medical-Surgical Ward A | Capacity: 20 | Current Census: 18 | Admissions Expected: 2 | Discharges Expected: 1",
        "urgent_unit_alerts": [
            "Room 305: Patient awaiting urgent lab results (Critical Potassium).",
            "Unit: Low stock of IV pumps, request submitted to central supply."
        ]
    }

def populate_section_ii_patient_identification(patient_id: str) -> dict:
    """Populates data for Section II: Patient Identification."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] REPORT_GEN: Populating Section II - Patient ID for {patient_id}")
    profile = get_mock_patient_profile(patient_id)
    if not profile:
        return {"error": f"Patient ID {patient_id} not found."}

    return {
        "room_no": profile.get("room_no", "N/A"),
        "patient_name_dob_mrn": f"{profile.get('name', 'N/A')} | DOB: {profile.get('dob', 'N/A')} | MRN: {profile.get('mrn', 'N/A')}",
        "isolation_precautions": profile.get("isolationPrecautions", "None"),
        "code_status": profile.get("codeStatus", "N/A"),
        "allergies": ", ".join(profile.get("allergies", ["None listed"])),
        "admitted_on_problem": f"Admitted on: {profile.get('admissionDate', 'N/A')} for {profile.get('principalProblem', 'N/A')}",
        "consulting_physicians": ", ".join(profile.get("consulting_physicians", ["None listed"])),
        "emergency_contact": f"{profile.get('emergencyContact', {}).get('name', 'N/A')} ({profile.get('emergencyContact', {}).get('phone', 'N/A')})"
    }

def populate_section_iii_patient_history(patient_id: str) -> dict:
    """Populates data for Section III: Patient History."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] REPORT_GEN: Populating Section III - Patient History for {patient_id}")

    rag_summary = fetch_patient_history_summary_from_rag(patient_id)
    about_me_data = get_mock_firestore_data(patient_id, "about_me")
    our_goals_data = get_mock_firestore_data(patient_id, "our_goals")
    social_history_data = get_mock_firestore_data(patient_id, "social_history_highlights")

    return {
        "relevant_past_medical_history": rag_summary.get("past_medical_history", "N/A"),
        "significant_surgical_history": rag_summary.get("surgical_history", "N/A"),
        "social_history_highlights": social_history_data,
        "about_me": about_me_data,
        "our_goals": our_goals_data
    }

# --- Input Handling Placeholders ---

def save_to_firestore(patient_id: str, data_key: str, content: dict):
    """
    Simulates saving data (e.g., "About Me", "Our Goals") to Firestore.
    In a real scenario, this would interact with the Firestore client.
    """
    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DB_SAVE (Firestore): Saving data for patient {patient_id}")
    print(f"  Data Key: {data_key}")
    print(f"  Content: {json.dumps(content, indent=2)}")

    # Simulate updating the mock store if desired for more dynamic examples
    if patient_id in MOCK_FIRESTORE_DATA:
        MOCK_FIRESTORE_DATA[patient_id][data_key] = content.get(data_key, content) # Adapt based on content structure
    else:
        MOCK_FIRESTORE_DATA[patient_id] = {data_key: content.get(data_key, content)}
    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DB_SAVE: Data for {patient_id} - {data_key} (simulated) saved/updated.")


if __name__ == "__main__":
    mock_patient_id_1 = "patientA123"
    mock_patient_id_2 = "patientB456"
    mock_patient_id_nonexistent = "patientC789"

    print("--- Generating Report Data (MVP Demo) ---")

    print("\n--- Section I: System Overview ---")
    section_i_data = populate_section_i_system_overview()
    print(json.dumps(section_i_data, indent=2))

    print(f"\n--- Section II: Patient Identification for {mock_patient_id_1} ---")
    section_ii_data_1 = populate_section_ii_patient_identification(mock_patient_id_1)
    print(json.dumps(section_ii_data_1, indent=2))

    print(f"\n--- Section II: Patient Identification for {mock_patient_id_nonexistent} ---")
    section_ii_data_nonexistent = populate_section_ii_patient_identification(mock_patient_id_nonexistent)
    print(json.dumps(section_ii_data_nonexistent, indent=2))


    print(f"\n--- Section III: Patient History for {mock_patient_id_1} ---")
    section_iii_data_1 = populate_section_iii_patient_history(mock_patient_id_1)
    print(json.dumps(section_iii_data_1, indent=2))

    print(f"\n--- Section III: Patient History for {mock_patient_id_2} ---")
    section_iii_data_2 = populate_section_iii_patient_history(mock_patient_id_2)
    print(json.dumps(section_iii_data_2, indent=2))

    print("\n--- Simulating Input and Saving 'About Me' for Patient A123 ---")
    new_about_me_content = {
        "about_me": "Loves gardening and spending time with her grandchildren. Prefers to be called 'Ellie'.",
        "last_updated_by": "Nurse Jane (RN)",
        "updated_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    save_to_firestore(mock_patient_id_1, "about_me", new_about_me_content)

    print("\n--- Verifying Updated 'About Me' for Patient A123 (Section III) ---")
    section_iii_data_1_updated = populate_section_iii_patient_history(mock_patient_id_1)
    print(json.dumps(section_iii_data_1_updated, indent=2))

    print("\n--- Section V: Systems Assessment ---")
    section_v_data_1 = populate_section_v_systems_assessment(mock_patient_id_1)
    print(json.dumps(section_v_data_1, indent=2))

    print("\n--- Demo Completed ---")

# --- Section V Specific Mock Data & Population Functions ---

MOCK_LAB_RESULTS = {
    "patientA123": {
        "abnormal_results": [
            "K+ 3.1 mmol/L (Low)",
            "BNP 1250 pg/mL (High)",
            "Creatinine 1.8 mg/dL (High)"
        ],
        "pending_results": ["Troponin Q6H (2nd set pending)", "Full Coag Panel"]
    },
    "patientB456": {
        "abnormal_results": ["WBC 15.5 x10^9/L (High)", "CRP 85 mg/L (High)"],
        "pending_results": ["Sputum Culture & Sensitivity", "Blood Culture x2"]
    }
}

MOCK_IV_ACCESS_DETAILS = {
    "patientA123": [
        {"site": "Left Forearm", "type": "PIV 20G", "patency": "Flushes well", "s_s_infection": "None noted", "dressing_change_due": "2024-07-22"},
        {"site": "Right Internal Jugular", "type": "Triple Lumen CVC", "patency": "All ports patent", "s_s_infection": "Slight redness at insertion", "dressing_change_due": "2024-07-25"}
    ],
    "patientB456": [
        {"site": "Right Antecubital", "type": "PIV 22G", "patency": "Sluggish return", "s_s_infection": "None noted", "dressing_change_due": "2024-07-21"}
    ]
}


def get_mock_lab_results(patient_id: str) -> dict:
    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DATA_FETCH: Getting lab results for {patient_id}")
    return MOCK_LAB_RESULTS.get(patient_id, {"abnormal_results": [], "pending_results": []})

def get_mock_iv_access_details(patient_id: str) -> list:
    print(f"[{datetime.datetime.utcnow().isoformat()}] MOCK_DATA_FETCH: Getting IV access details for {patient_id}")
    return MOCK_IV_ACCESS_DETAILS.get(patient_id, [])


def populate_neuro_assessment(patient_id: str) -> dict:
    # Data could be partly from profile, partly from flowsheets/observations
    profile = get_mock_patient_profile(patient_id)
    assessment = {
        "loc": "Alert and Oriented x3",
        "gcs": "15 (E4 V5 M6)", # Could be calculated or entered
        "pupils": "PERRLA, 3mm",
        "sedation_goal_rass": "RASS 0 (Alert and Calm)", # Target for ICU patients
        "cam_icu": "Negative", # Delirium screening
        "restraints": "None", # Type if any, reason, checks
        "motor_strength": "Moves all extremities equally, grips strong bilaterally",
        "notes": "No focal neurological deficits noted. Follows commands."
    }
    if patient_id == "patientA123":
        assessment["notes"] = "Patient reports slight dizziness on standing. Neuro checks Q4H."
    return assessment

def populate_pulmonary_assessment(patient_id: str) -> dict:
    assessment = {
        "airway": "Patent, self-ventilating", # E.g., ETT size/depth, Trach size
        "oxygen_delivery": "Nasal Cannula",
        "oxygen_flow_rate_fio2": "2 L/min", # Or FiO2 if on vent
        "respiratory_rate": "18 breaths/min",
        "spo2": "96%",
        "breath_sounds": "Clear bilaterally anteriorly, diminished bases posteriorly", # Input field
        "cough_sputum": "Non-productive cough occasionally",
        "abg_vbg_highlights": "pH 7.38, PaCO2 42, PaO2 85, HCO3 24 (Recent ABG)", # Mock
        "ventilator_settings": "N/A", # Detailed if on ventilator
        "sat_sbt_status": "N/A" # Spontaneous Awakening/Breathing Trial
    }
    if patient_id == "patientB456":
        assessment["breath_sounds"] = "Coarse crackles in bilateral lower lobes."
        assessment["spo2"] = "93% on 2L NC"
        assessment["cough_sputum"] = "Productive cough, yellow sputum."
    return assessment

def populate_cardiovascular_assessment(patient_id: str) -> dict:
    assessment = {
        "heart_rhythm_rate": "Sinus Rhythm, Rate 75 bpm", # From monitor/assessment
        "bp_map": "120/80 mmHg (MAP 93 mmHg)", # From monitor/assessment
        "hemodynamics_pac": "N/A", # E.g., CVP, PAP, CO if available
        "peripheral_pulses": "Radial +2 bilaterally, Pedal +1 bilaterally",
        "capillary_refill": "<3 seconds upper and lower extremities",
        "edema": "Trace edema bilateral lower extremities", # Location, severity
        "active_vasoactive_drips": "None", # E.g., Norepinephrine 5 mcg/min
        "telemetry": "Monitored, no ectopy noted in last 4 hours."
    }
    if patient_id == "patientA123":
        assessment["heart_rhythm_rate"] = "Atrial Fibrillation, Rate 88 bpm (controlled)"
        assessment["bp_map"] = "110/70 mmHg (MAP 83 mmHg)"
        assessment["edema"] = "+1 pitting edema bilateral ankles and shins."
        assessment["active_vasoactive_drips"] = "Furosemide 20mg IV BID" # Not vasoactive, but relevant med.
    return assessment

def populate_gi_assessment(patient_id: str) -> dict:
    assessment = {
        "diet_tube_feedings": "Regular Diet, tolerating well", # Type, rate, flush, residuals if TF
        "bowel_sounds": "Active in all 4 quadrants", # Input field
        "abdomen_assessment": "Soft, non-tender, non-distended", # Input field
        "last_bm": "Today AM (Soft, brown)", # Date, consistency
        "nausea_vomiting": "Denies nausea or vomiting",
        "gi_output": "N/A", # Ostomy, NG tube output
        "blood_sugar_monitoring": "ACCU checks ACHS. Last BS: 110 mg/dL",
        "misc_gi_notes": "Patient prefers small, frequent meals."
    }
    if patient_id == "patientA123":
        assessment["diet_tube_feedings"] = "Cardiac Diet, 2L Fluid Restriction"
        assessment["last_bm"] = "Yesterday PM (Formed)"
    return assessment

def populate_gu_assessment(patient_id: str) -> dict:
    assessment = {
        "urine_output_method": "Voiding independently", # E.g., Foley, Purewick
        "urine_output_amount_24hr": "1800 mL / 24hr (approx)", # Or last 8hr shift
        "urine_characteristics": "Clear, yellow", # Color, clarity, odor
        "renal_labs_summary": "BUN 18 mg/dL, Creatinine 1.0 mg/dL (Stable)", # Mock
        "dialysis_access": "No dialysis access."
    }
    if patient_id == "patientA123":
        profile = get_mock_patient_profile(patient_id) # To get admission date for context
        assessment["renal_labs_summary"] = f"BUN 25 mg/dL, Creatinine 1.8 mg/dL (Elevated, baseline {profile.get('principalProblem')})" # Mock
        assessment["urine_output_amount_24hr"] = "1200 mL / 24hr (on Furosemide)"
    return assessment

def populate_skin_mobility_assessment(patient_id: str) -> dict:
    assessment = {
        "braden_score": "19 (Low Risk)", # Score and risk level
        "skin_assessment_findings": "Skin warm, dry, intact. No redness or breakdown noted.", # Text area, or link to digital body map
        "wound_care_orders": "None", # Specific orders
        "pressure_injury_prevention": "Turn Q2H, HOB elevated 30 degrees, support surfaces in use.",
        "mobility_status": "Ambulates independently with steady gait.", # Bedrest, SBA, PT involvement
        "fall_interventions": "Bed low, call light in reach, non-slip socks.",
        "spinal_precautions": "None",
        "bath_type_schedule": "Shower daily AM (self)",
        "weight_monitoring": "Standing weight daily AM. Last: 70kg."
    }
    if patient_id == "patientA123":
        assessment["braden_score"] = "16 (Moderate Risk)"
        assessment["skin_assessment_findings"] = "Dry skin noted on lower legs. Heels intact. Small ecchymosis on left forearm."
        assessment["pressure_injury_prevention"] = "Float heels, Mepilex to sacrum, turn Q2H."
        assessment["mobility_status"] = "Ambulates with rolling walker, SBA due to fatigue."
    return assessment

def populate_iv_access_assessment(patient_id: str) -> dict:
    iv_sites = get_mock_iv_access_details(patient_id)
    return {
        "iv_sites_and_types": iv_sites, # List of dicts
        "central_line_necessity": "Not applicable" if not any("CVC" in site.get("type","") for site in iv_sites) else "Daily review for necessity, indication: medication admin",
        "notes": "Monitor right IJ CVC site for increased redness." if patient_id == "patientA123" else "Ensure PIVs are dated."
    }

def populate_fluids_infusions_assessment(patient_id: str) -> dict:
    assessment = {
        "continuous_infusions": "None", # Med, rate, dose, concentration
        "ivf_maintenance_bolus": "Saline lock for PRN medications.", # Type, rate
        "blood_products_overview": "No blood products administered or pending.", # Type, volume, reactions
        "po_intake_estimate": "Good, approx 1500mL in last 24hr.",
        "fluid_balance_24hr": "+300 mL (I:2000 O:1700)" # Calculated or from flowsheet
    }
    if patient_id == "patientA123":
        assessment["ivf_maintenance_bolus"] = "0.9% Normal Saline @ 30 mL/hr KVO via CVC."
        assessment["fluid_balance_24hr"] = "-200 mL (I:1500 O:1700) - Diuresing as planned."
    return assessment

def populate_pain_assessment(patient_id: str) -> dict:
    assessment = {
        "pain_score_current": "0/10 (Denies pain)", # Current score, scale used
        "pain_location_character": "N/A",
        "pain_goal": "Maintain pain <= 3/10",
        "non_pharmacological_interventions": "Repositioning, distraction.",
        "pharmacological_interventions": "PRN Acetaminophen 500mg available.",
        "effectiveness_of_interventions": "Pain well managed currently."
    }
    if patient_id == "patientB456": # Pneumonia patient might have pleuritic pain
        assessment["pain_score_current"] = "3/10 on deep inspiration"
        assessment["pain_location_character"] = "Right chest, sharp"
        assessment["pharmacological_interventions"] = "Scheduled Acetaminophen 650mg Q6H. Last dose 06:00."
    return assessment

def populate_laboratory_diagnostics_assessment(patient_id: str) -> dict:
    labs = get_mock_lab_results(patient_id)
    return {
        "abnormal_lab_test_results": labs.get("abnormal_results", []), # List of strings
        "pending_labs_tests": labs.get("pending_results", []), # List of strings
        "recent_imaging_highlights": "Chest X-Ray (yesterday): Bilateral lower lobe infiltrates consistent with pneumonia." if patient_id == "patientB456" else "Chest X-Ray (today): Mild pulmonary congestion, improved from admission.",
        "other_diagnostics_notes": "ECG (today): Atrial Fibrillation, rate 88. No acute ST changes." if patient_id == "patientA123" else "Awaiting sputum culture results before antibiotic adjustment."
    }


def populate_section_v_systems_assessment(patient_id: str) -> dict:
    """Populates data for Section V: Systems Assessment by calling sub-functions."""
    print(f"[{datetime.datetime.utcnow().isoformat()}] REPORT_GEN: Populating Section V - Systems Assessment for {patient_id}")

    if not get_mock_patient_profile(patient_id): # Check if patient exists
        return {"error": f"Patient ID {patient_id} not found, cannot generate Section V."}

    return {
        "neurological": populate_neuro_assessment(patient_id),
        "pulmonary": populate_pulmonary_assessment(patient_id),
        "cardiovascular": populate_cardiovascular_assessment(patient_id),
        "gi_gastrointestinal": populate_gi_assessment(patient_id),
        "gu_genitourinary": populate_gu_assessment(patient_id),
        "skin_mobility": populate_skin_mobility_assessment(patient_id),
        "iv_access_lines": populate_iv_access_assessment(patient_id),
        "fluids_infusions_intake": populate_fluids_infusions_assessment(patient_id),
        "pain_comfort": populate_pain_assessment(patient_id),
        "laboratory_diagnostics": populate_laboratory_diagnostics_assessment(patient_id)
    }
