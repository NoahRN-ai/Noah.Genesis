# Noah Patient Summary Agent (MVP)

This directory contains the MVP implementation of the Noah Patient Summary Agent. The agent is designed to generate patient summaries by simulating the retrieval of patient data, querying a clinical knowledge base (RAG simulation), and then generating a summary using a mock LLM call.

## File Index

1.  **`patient_summary_agent.py`**
    *   **Purpose:** The main Python script that orchestrates the patient summary generation process.
    *   **Content:**
        *   **Mock Data Stores:** In-memory dictionaries (`MOCK_PATIENT_PROFILES`, `MOCK_EVENT_LOGS`) to simulate fetching patient data from Firestore and event logs from AlloyDB.
        *   `get_mock_patient_data(patient_id: str)`: Fetches data from `MOCK_PATIENT_PROFILES`.
        *   `get_mock_event_logs(patient_id: str)`: Fetches data from `MOCK_EVENT_LOGS`.
        *   **Placeholder for RAG (Vertex AI Search):**
            *   `query_vertex_ai_search(patient_data: dict, query: str)`: Simulates a call to Vertex AI Search. It performs basic keyword matching against `mock_clinical_kb.json` to find relevant "documents."
        *   **Placeholder for LLM (MedGemma/Gemini):**
            *   `generate_summary_with_llm(context_data: dict, summary_type: str)`: Simulates a call to an LLM service. It constructs a textual summary based on the provided patient data, event logs, and RAG results.
        *   **API Endpoint (Flask):**
            *   `GET /summary/<patient_id>`: An HTTP endpoint that takes a `patient_id` and an optional `type` query parameter (e.g., `?type=nursing_note`). It gathers all necessary data, simulates RAG and LLM calls, and returns the generated summary as a JSON response.
    *   **Direct Run Capability:** Includes an `if __name__ == "__main__":` block that allows running a simulation directly.
    *   **Reusability for Other Agents:** Several functions within this script (e.g., `get_mock_patient_data`, `get_mock_event_logs`, `query_vertex_ai_search`, `generate_summary_with_llm`) and its mock data stores (`MOCK_PATIENT_PROFILES`, `MOCK_EVENT_LOGS`, `MOCK_CLINICAL_KB`) are designed to be importable and usable by other agent MVP scripts (like those in `noah_ai_report_structure_mvp` and `noah_handoff_summary_mvp`) to simulate deeper inter-agent communication and data sharing.

2.  **`mock_clinical_kb.json`**
    *   **Purpose:** A JSON file containing sample clinical knowledge base "documents" used by the `query_vertex_ai_search` function to simulate RAG retrieval.
    *   **Content:** Each entry includes `id`, `title`, `content`, and `keywords`.

3.  **`requirements.txt`**
    *   **Purpose:** Lists Python dependencies.
    *   **Content:** Includes `Flask` for the API endpoint.

## How to Run the Agent

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Script:**
    *   **Option A: Run the Flask API Server:**
        Uncomment `app.run(debug=True, port=5000)` in `patient_summary_agent.py` and run:
        ```bash
        python patient_summary_agent.py
        ```
        The server will start on `http://localhost:5000`.
    *   **Option B: Run a Direct Simulation (No API Server):**
        Run the script as is (with `app.run(...)` commented out):
        ```bash
        python patient_summary_agent.py
        ```
        This executes the `if __name__ == "__main__":` block simulations.

## Integration with Other Agents

As part of a larger MVP integration effort:
*   The mock data stores (`MOCK_PATIENT_PROFILES`, `MOCK_EVENT_LOGS`, `MOCK_CLINICAL_KB`) and core logic functions (`get_mock_patient_data`, `query_vertex_ai_search`, `generate_summary_with_llm`) in `patient_summary_agent.py` are intended to be imported by other agent scripts.
*   This allows other agents (e.g., for AI report structure generation or handoff summaries) to leverage this agent's data and summarization capabilities, simulating a more integrated system where agents call upon each other's services.
*   When these functions are imported, `patient_summary_agent.py` itself is not run as a separate process but provides its functions and data to the importing script.

## How to Test the API Endpoint

If you chose **Option A** above and the Flask server is running:

1.  **Open your web browser** and navigate to an endpoint like:
    *   `http://localhost:5000/summary/patient123` (for a handoff report)
    *   `http://localhost:5000/summary/patient456?type=nursing_note` (for a nursing note)

2.  **Alternatively, use a tool like `curl`** in your terminal:
    ```bash
    # For patient123 (default handoff_report)
    curl "http://localhost:5000/summary/patient123"

    # For patient456, requesting a nursing_note
    curl "http://localhost:5000/summary/patient456?type=nursing_note"

    # For a non-existent patient (will return 404)
    curl "http://localhost:5000/summary/patient_nonexistent"
    ```
    You should receive a JSON response containing the generated summary.

## Important Notes

*   **Simulations:** The calls to Vertex AI Search (RAG) and the LLM (MedGemma/Gemini) are **simulated**. The `query_vertex_ai_search` function performs a basic keyword search on the `mock_clinical_kb.json` file, and `generate_summary_with_llm` constructs a summary based on predefined templates and the mock data. No actual AI services are called.
*   **Mock Data:** All patient data, event logs, and clinical knowledge are hardcoded or read from local mock files.
*   **Error Handling:** Basic error handling (e.g., for non-existent patient IDs) is included in the API.
*   **Flask Port:** The Flask app is configured to run on port `5000` by default. If this port is in use, you can change it in the `app.run()` call in `patient_summary_agent.py`.
