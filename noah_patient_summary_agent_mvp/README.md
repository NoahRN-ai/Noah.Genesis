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
        *   **Direct Run Capability:** Includes an `if __name__ == "__main__":` block that allows running a simulation directly by calling functions if Flask server is not desired for a quick test.

2.  **`mock_clinical_kb.json`**
    *   **Purpose:** A JSON file containing a few sample clinical knowledge base "documents".
    *   **Content:** Each entry has an `id`, `title`, `content` (a brief description of a clinical topic like Sepsis, Pneumonia), and `keywords`. This file is used by the `query_vertex_ai_search` function to simulate RAG retrieval.

3.  **`requirements.txt`**
    *   **Purpose:** Lists the Python dependencies required for this project.
    *   **Content:** Includes `Flask` for running the API endpoint.

## How to Run the Agent

1.  **Install Dependencies:**
    Open your terminal, navigate to the `noah_patient_summary_agent_mvp` directory, and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Script:**
    You have two options to run the agent:

    *   **Option A: Run the Flask API Server:**
        To start the API server, open `patient_summary_agent.py`, uncomment the line `app.run(debug=True, port=5000)` (it's near the end of the file), and then run the script:
        ```bash
        python patient_summary_agent.py
        ```
        The server will start, typically on `http://localhost:5000`.

    *   **Option B: Run a Direct Simulation (No API Server):**
        If you don't want to start the Flask server and just want to see the simulation output in the console, you can run the script as is (with the `app.run(...)` line commented out):
        ```bash
        python patient_summary_agent.py
        ```
        This will execute the example simulations defined in the `if __name__ == "__main__":` block.

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
