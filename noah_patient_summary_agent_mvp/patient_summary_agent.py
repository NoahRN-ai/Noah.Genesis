import datetime
import json

from flask import Flask, jsonify, request

# --- Mock Data Stores ---
MOCK_PATIENT_PROFILES = {
    "patient123": {
        "patientId": "patient123",
        "name": "Johnathan Doe",
        "dob": "1985-01-15",
        "mrn": "MRN007P123",
        "allergies": ["Penicillin", "Contrast Dye"],
        "isolationPrecautions": "Contact",
        "codeStatus": "Full Code",
        "admissionDate": "2024-07-15T10:00:00Z",
        "principalProblem": "Sepsis",
        "emergencyContact": {"name": "Jane Doe", "phone": "555-1234"},
    },
    "patient456": {
        "patientId": "patient456",
        "name": "Alice Wonderland",
        "dob": "1992-06-22",
        "mrn": "MRN008P456",
        "allergies": ["None known"],
        "isolationPrecautions": "Standard",
        "codeStatus": "DNR/DNI",
        "admissionDate": "2024-07-18T14:30:00Z",
        "principalProblem": "Pneumonia",
        "emergencyContact": {"name": "Mad Hatter", "phone": "555-5678"},
    },
}

MOCK_EVENT_LOGS = {
    "patient123": [
        {
            "eventId": "evt001",
            "patientId": "patient123",
            "eventType": "VitalSignChange",
            "timestamp": "2024-07-20T08:00:00Z",
            "value": {
                "temp_c": 39.1,
                "hr_bpm": 115,
                "bp_sys": 90,
                "bp_dia": 50,
                "spo2_pct": 91,
            },
            "source": "BedsideMonitor",
        },
        {
            "eventId": "evt002",
            "patientId": "patient123",
            "eventType": "MedicationAdministered",
            "timestamp": "2024-07-20T08:30:00Z",
            "value": {"medication": "BroadSpectrumAntibiotic IV", "dose": "2g"},
            "source": "EMAR",
        },
        {
            "eventId": "evt003",
            "patientId": "patient123",
            "eventType": "LabResult",
            "timestamp": "2024-07-20T09:00:00Z",
            "value": {"test": "Lactate", "result": "4.5 mmol/L", "abnormal": True},
            "source": "LIS",
        },
        {
            "eventId": "evt004",
            "patientId": "patient123",
            "eventType": "NurseInput",
            "timestamp": "2024-07-20T10:00:00Z",
            "value": {
                "note": "Patient verbalized feeling very weak. Family at bedside."
            },
            "source": "ManualInput",
        },
    ],
    "patient456": [
        {
            "eventId": "evt005",
            "patientId": "patient456",
            "eventType": "VitalSignChange",
            "timestamp": "2024-07-20T09:00:00Z",
            "value": {
                "temp_c": 38.2,
                "hr_bpm": 98,
                "bp_sys": 130,
                "bp_dia": 75,
                "spo2_pct": 93,
                "rr_rpm": 22,
            },
            "source": "BedsideMonitor",
        },
        {
            "eventId": "evt006",
            "patientId": "patient456",
            "eventType": "MedicationAdministered",
            "timestamp": "2024-07-20T09:15:00Z",
            "value": {"medication": "Levofloxacin PO", "dose": "750mg"},
            "source": "EMAR",
        },
        {
            "eventId": "evt007",
            "patientId": "patient456",
            "eventType": "NurseInput",
            "timestamp": "2024-07-20T11:00:00Z",
            "value": {
                "note": "Productive cough, sputum greenish. Encouraged deep breathing exercises."
            },
            "source": "ManualInput",
        },
    ],
}

# Load mock clinical knowledge base
try:
    with open("mock_clinical_kb.json") as f:
        MOCK_CLINICAL_KB = json.load(f)
except FileNotFoundError:
    print("WARN: mock_clinical_kb.json not found. RAG will return empty results.")
    MOCK_CLINICAL_KB = []

# --- Agent Functions ---


def get_mock_patient_data(patient_id: str) -> dict:
    """Simulates fetching patient profile data from a data store like Firestore."""
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Fetching patient data for ID: {patient_id}"
    )
    return MOCK_PATIENT_PROFILES.get(patient_id)


def get_mock_event_logs(patient_id: str) -> list:
    """Simulates fetching event log data for a patient from a data store like AlloyDB."""
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Fetching event logs for ID: {patient_id}"
    )
    return MOCK_EVENT_LOGS.get(patient_id, [])


def query_vertex_ai_search(patient_data: dict, query: str) -> list:
    """Placeholder for querying Vertex AI Search (or a similar RAG system).
    Simulates retrieving relevant documents/snippets from a clinical knowledge base.
    """
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Querying RAG (Vertex AI Search simulation) for patient {patient_data.get('patientId')} with query: '{query}'"
    )

    retrieved_docs = []
    query_terms = query.lower().split()

    if not MOCK_CLINICAL_KB:
        print(
            f"[{datetime.datetime.utcnow().isoformat()}] WARN: Mock clinical knowledge base is empty."
        )
        return []

    for doc in MOCK_CLINICAL_KB:
        # Simple keyword matching for simulation
        doc_title_lower = doc.get("title", "").lower()
        doc_content_lower = doc.get("content", "").lower()
        doc_keywords = [kw.lower() for kw in doc.get("keywords", [])]

        if any(
            term in doc_title_lower or term in doc_content_lower or term in doc_keywords
            for term in query_terms
        ):
            retrieved_docs.append(
                {
                    "document_id": doc.get("id"),
                    "title": doc.get("title"),
                    "snippet": doc.get("content")[:150] + "...",  # Short snippet
                }
            )

    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: RAG simulation retrieved {len(retrieved_docs)} documents."
    )
    return retrieved_docs


def generate_summary_with_llm(context_data: dict, summary_type: str) -> str:
    """Placeholder for calling a Large Language Model (MedGemma/Gemini).
    Simulates generating a clinical summary based on context.
    """
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Generating LLM summary (simulation). Type: {summary_type}"
    )
    patient_profile = context_data.get("patient_profile", {})
    event_logs = context_data.get("event_logs", [])
    rag_results = context_data.get("rag_results", [])

    summary_parts = []
    summary_parts.append(
        f"--- AI-Generated Summary ({summary_type.replace('_', ' ').title()}) ---"
    )
    summary_parts.append(
        f"Patient: {patient_profile.get('name', 'N/A')} (ID: {patient_profile.get('patientId', 'N/A')})"
    )
    summary_parts.append(
        f"DOB: {patient_profile.get('dob', 'N/A')}, MRN: {patient_profile.get('mrn', 'N/A')}"
    )
    summary_parts.append(
        f"Admission Date: {patient_profile.get('admissionDate', 'N/A')}"
    )
    summary_parts.append(
        f"Principal Problem: {patient_profile.get('principalProblem', 'N/A')}"
    )
    summary_parts.append(
        f"Allergies: {', '.join(patient_profile.get('allergies', ['N/A']))}"
    )
    summary_parts.append(f"Code Status: {patient_profile.get('codeStatus', 'N/A')}")

    summary_parts.append("\nKey Recent Events:")
    if event_logs:
        for event in event_logs[:3]:  # Show a few recent events
            summary_parts.append(
                f"  - {event.get('timestamp')}: {event.get('eventType')} - {json.dumps(event.get('value'))}"
            )
    else:
        summary_parts.append("  - No recent events found.")

    summary_parts.append("\nRelevant Clinical Information (Simulated RAG):")
    if rag_results:
        for doc in rag_results[:2]:  # Show a couple of RAG results
            summary_parts.append(f"  - {doc.get('title')}: {doc.get('snippet')}")
    else:
        summary_parts.append(
            "  - No specific clinical guidance retrieved by RAG simulation."
        )

    # Tailor based on summary_type
    if summary_type == "nursing_note":
        summary_parts.append("\nNursing Focus:")
        summary_parts.append(
            "  - Monitor vital signs closely, especially [relevant vital for principal problem]."
        )
        summary_parts.append(
            "  - Administer medications as prescribed and observe for effects/side effects."
        )
        summary_parts.append("  - Patient comfort and safety measures in place.")
    elif summary_type == "handoff_report":
        summary_parts.append("\nKey Points for Handoff:")
        summary_parts.append(
            f"  - Patient is {patient_profile.get('name')} admitted for {patient_profile.get('principalProblem')}."
        )
        summary_parts.append(
            "  - Current status: [Simulated assessment - e.g., Stable but requires monitoring]."
        )
        summary_parts.append(
            "  - Pending tasks: [e.g., Follow up on morning labs, consult with specialist]."
        )
        summary_parts.append(
            "  - Key concerns: [e.g., Potential for deterioration, pain management]."
        )

    summary_parts.append("\n--- End of AI-Generated Summary ---")

    # Actual LLM call would be something like:
    # prompt = f"Generate a {summary_type} for patient {patient_profile.get('name')}..."
    # response = llm_client.generate(prompt, context=context_data)
    # return response.text

    return "\n".join(summary_parts)


# --- Flask API Endpoint ---
app = Flask(__name__)


@app.route("/summary/<patient_id>", methods=["GET"])
def get_patient_summary(patient_id):
    summary_type = request.args.get(
        "type", "handoff_report"
    )  # Default to handoff_report

    print(
        f"[{datetime.datetime.utcnow().isoformat()}] API: Received request for patient_id: {patient_id}, type: {summary_type}"
    )

    patient_data = get_mock_patient_data(patient_id)
    if not patient_data:
        return jsonify({"error": "Patient not found"}), 404

    event_logs = get_mock_event_logs(patient_id)

    # Simulate RAG query based on principal problem
    rag_query = patient_data.get("principalProblem", "general medical condition")
    rag_results = query_vertex_ai_search(patient_data, rag_query)

    context_data = {
        "patient_profile": patient_data,
        "event_logs": event_logs,
        "rag_results": rag_results,
        "current_time": datetime.datetime.utcnow().isoformat(),
    }

    generated_summary_text = generate_summary_with_llm(context_data, summary_type)

    return jsonify(
        {
            "patientId": patient_id,
            "summaryType": summary_type,
            "generatedSummary": generated_summary_text,
            "dataSources": {
                "profileFetched": True,
                "eventLogsCount": len(event_logs),
                "ragDocumentsCount": len(rag_results),
            },
        }
    )


# --- Main execution for direct script run (non-Flask server) ---
def run_direct_simulation(patient_id_to_test, summary_type_to_test):
    print(
        f"\n--- Running Direct Simulation for Patient ID: {patient_id_to_test}, Summary Type: {summary_type_to_test} ---"
    )
    patient_data = get_mock_patient_data(patient_id_to_test)
    if not patient_data:
        print(f"ERROR: Patient with ID '{patient_id_to_test}' not found in mock data.")
        return

    event_logs = get_mock_event_logs(patient_id_to_test)

    rag_query = patient_data.get("principalProblem", "general medical condition")
    rag_results = query_vertex_ai_search(patient_data, rag_query)

    context_data = {
        "patient_profile": patient_data,
        "event_logs": event_logs,
        "rag_results": rag_results,
        "current_time": datetime.datetime.utcnow().isoformat(),
    }

    generated_summary_text = generate_summary_with_llm(
        context_data, summary_type_to_test
    )

    print("\n--- Generated Summary (Direct Run) ---")
    print(generated_summary_text)
    print("--- End of Direct Run Summary ---")


if __name__ == "__main__":
    # To run the Flask server:
    # 1. Make sure Flask is installed (`pip install Flask`).
    # 2. Uncomment the line below and run `python patient_summary_agent.py`.
    # app.run(debug=True, port=5000)

    # To run a direct simulation without starting the Flask server:
    print("Starting direct simulation (Flask server is NOT started by default)...")
    run_direct_simulation("patient123", "handoff_report")
    print("-" * 50)
    run_direct_simulation("patient456", "nursing_note")
    print("-" * 50)
    run_direct_simulation(
        "patient_nonexistent", "handoff_report"
    )  # Test non-existent patient
    print(
        "\nTo start the Flask API server, uncomment 'app.run(debug=True, port=5000)' in the script and run again."
    )
