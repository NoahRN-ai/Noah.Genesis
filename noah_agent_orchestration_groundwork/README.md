# Noah Agent Orchestration Groundwork (MVP)

This directory lays the conceptual groundwork for orchestrating the various MVP agents and modules developed for the Noah AI-Powered Shift Report system. It focuses on defining agent interfaces that act as facades to the actual agent logic (simulated via Python imports), illustrating basic interaction flows, and exploring how a formal orchestration layer (like LangGraph) could be applied.

## File Index

1.  **`agent_interfaces.py`**
    *   **Purpose:** This Python script defines a set of functions that act as a **facade** or a centralized interface to the core functionalities of the other MVP agent scripts.
    *   **Functionality:**
        *   It attempts to import actual functions and data stores (like `SHARED_MOCK_EVENTS_DB`) from the other agent MVP directories (e.g., `noah_patient_summary_agent_mvp`, `noah_shift_event_capture_agent_mvp`, etc.).
        *   If imports are successful, the facade functions in this script will call the imported "real" agent logic.
        *   If imports fail (e.g., due to path issues or the way the tool environment executes scripts), these functions fall back to simpler, local mock behavior.
    *   **Key "Interface" Functions:**
        *   `call_data_aggregation_firestore(patient_id)`: Fetches patient profiles (tries to use `patient_summary_agent`'s mocks).
        *   `call_data_aggregation_alloydb_events(patient_id, filters)`: Fetches events (tries to use `events_log_data_prep`'s functions, which in turn access the shared event store from `shift_event_capture`).
        *   `call_patient_summary_agent(profile, events, summary_type)`: Generates patient summaries (tries to use `patient_summary_agent`'s logic).
        *   `call_shift_event_capture_agent(patient_id, details, event_type)`: Logs new events (tries to use `shift_event_capture`'s logic, updating the shared event store).
        *   `call_todo_list_manager(action, payload)`: Manages To-Do tasks (tries to use `todo_list_manager`'s functions).
    *   The script includes print statements to indicate whether it's using imported functions or local fallbacks.

2.  **`conceptual_workflows.py`**
    *   **Purpose:** This script demonstrates how the facade functions from `agent_interfaces.py` can be combined to create high-level workflows, simulating more realistic inter-agent communication.
    *   **Content:**
        *   Imports functions from `agent_interfaces.py`.
        *   Defines example workflows:
            *   `run_patient_intake_workflow(patient_id)`: Simulates fetching patient data and generating an intake summary.
            *   `run_log_new_observation_workflow(patient_id, observation_text)`: Simulates logging an observation, then re-fetching data (which should include the new observation if shared data is working) and regenerating a patient summary.
            *   `run_add_todo_task_workflow(patient_id, task_description, priority)`: Simulates adding a task to the to-do list.
        *   The `if __name__ == "__main__":` block executes these example workflows. The output will show the sequence of calls and demonstrate the data flow, ideally reflecting the shared data and integrated agent calls.

3.  **`langgraph_concepts.md`**
    *   **Purpose:** (No change in this step) A markdown document that explores how LangGraph could be used to formalize and manage the orchestration of Noah agents.
    *   **Content:**
        *   **Nodes:** Explains how each function in `agent_interfaces.py` can be mapped to a node in a LangGraph graph.
        *   **Edges:** Describes how the sequences of calls in `conceptual_workflows.py` imply edges (dependencies and data flow) between these nodes.
        *   **State Management:** Briefly discusses what a shared graph state might look like for the Noah application (e.g., holding `patient_id`, fetched `patient_profile`, `patient_events`, etc.).
        *   **Example Graph:** Provides a conceptual representation of the `run_patient_intake_workflow` as a simple LangGraph graph.
        *   Discusses benefits like modularity, explicit state, flexibility, and tool integration.
    *   This file is purely for design and conceptual explanation, not for runnable LangGraph code.

## Overall Goal and Next Steps

The primary goal of this subtask is to:
*   **Abstract Agent Capabilities:** Define clear, callable interfaces for each agent's core function.
*   **Illustrate Interactions:** Show how these agents might work together in simple sequences to achieve common clinical tasks.
*   **Explore Formal Orchestration:** Introduce the idea of using a framework like LangGraph to build more robust, manageable, and scalable multi-agent workflows.

This groundwork is crucial for moving from individual MVP agents to an integrated system. Future steps would involve:
*   Replacing the stubs in `agent_interfaces.py` with actual calls to the implemented agent services/scripts.
*   Implementing the conceptual LangGraph graphs, defining the state, nodes, and edges more formally.
*   Developing a more sophisticated orchestration layer that can handle complex logic, error recovery, and potentially user interactions within workflows.
