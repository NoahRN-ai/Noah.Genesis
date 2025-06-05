# LangGraph Orchestration Concepts for Noah Agents

This document outlines how LangGraph principles could be applied to orchestrate the interactions between the various Noah MVP agents. The agent functionalities are stubbed in `agent_interfaces.py`, and example interaction flows are demonstrated in `conceptual_workflows.py`.

## Core Idea

LangGraph allows us to define agentic workflows as stateful graphs. Each step in our workflow can be a "node," and the "edges" define how data flows and which node comes next. This is a powerful paradigm for building complex, multi-step AI applications where different specialized agents or tools need to collaborate.

## 1. Defining Nodes

Each of the core functions defined in `agent_interfaces.py` can be mapped to a node in a LangGraph graph. These nodes represent a specific piece of work or a call to an external agent/tool.

*   **`node_fetch_profile`**: Wraps `call_data_aggregation_firestore(patient_id)`.
    *   Input: `patient_id` (from graph state).
    *   Output: `patient_profile` (added to graph state).
*   **`node_fetch_events`**: Wraps `call_data_aggregation_alloydb_events(patient_id, filters)`.
    *   Input: `patient_id`, `filters` (from graph state or predefined).
    *   Output: `patient_events` (added to graph state).
*   **`node_generate_summary`**: Wraps `call_patient_summary_agent(patient_profile, patient_events, summary_type)`.
    *   Input: `patient_profile`, `patient_events` (from graph state), `summary_type` (from graph state or predefined).
    *   Output: `generated_summary` (added to graph state).
*   **`node_log_event`**: Wraps `call_shift_event_capture_agent(patient_id, event_details, event_type)`.
    *   Input: `patient_id`, `event_details`, `event_type` (from graph state or user input).
    *   Output: `log_confirmation` (added to graph state).
*   **`node_manage_todo`**: Wraps `call_todo_list_manager(action, payload)`.
    *   Input: `action`, `payload` (from graph state or user input).
    *   Output: `todo_result` (e.g., new task details, list of tasks, added to graph state).

Each node function in LangGraph would typically take the current `state` dictionary as input and return a dictionary representing the changes to the state.

## 2. Defining Edges & Graph Structure

The workflows defined in `conceptual_workflows.py` illustrate the dependencies and data flow, which inform how edges are defined.

### Example Graph: `run_patient_intake_workflow`

This workflow translates quite directly to a sequential graph:

1.  **`START`**: Entry point of the graph.
2.  **`node_fetch_profile`**:
    *   **Edge:** `START` -> `node_fetch_profile`.
    *   **Conditional Edges (Error Handling):** If `node_fetch_profile` returns an error (e.g., patient not found), an edge could lead to an `error_handling_node` or directly to `END` with an error state.
3.  **`node_fetch_events`**:
    *   **Edge:** `node_fetch_profile` -> `node_fetch_events` (if profile fetch was successful).
    *   This edge implies that `patient_id` from the state (populated by `node_fetch_profile` or initial input) is available.
4.  **`node_generate_summary`**:
    *   **Edge:** `node_fetch_events` -> `node_generate_summary`.
    *   This implies that `patient_profile` and `patient_events` are now in the state.
5.  **`END`**: Exit point of the graph. The final state contains all collected data and the generated summary.

### More Complex Graphs: Conditional Edges

For more dynamic workflows, LangGraph supports conditional edges. For example, after logging an event with `node_log_event`:

*   A conditional edge could decide whether to regenerate a patient summary (`node_generate_summary`) based on the type or severity of the logged event.
*   Or, it could decide to add a follow-up task using `node_manage_todo`.

The "next node" is determined by a function that inspects the current state.

## 3. State Management

The graph's state is a central piece that gets passed around and updated by each node. For the Noah application, the state could be a Pydantic model or a simple dictionary containing fields like:

```python
# Example State (conceptual)
class NoahWorkflowState(TypedDict):
    patient_id: str | None
    patient_profile: dict | None
    patient_events: list | None
    current_event_details: dict | None # For logging new events
    current_event_type: str | None
    todo_action: str | None
    todo_payload: dict | None
    generated_summary: str | None
    last_operation_status: str | None # 'success', 'error'
    error_message: str | None
    # ... other relevant data points
```

Nodes would read from this state (e.g., `patient_id` to fetch data) and write back their results (e.g., `patient_profile` after fetching it).

## 4. Benefits of Using LangGraph

*   **Modularity:** Each agent/tool call is a self-contained node.
*   **Explicit State:** State is managed explicitly, making it easier to track data flow and debug.
*   **Flexibility:** Easily define sequential, branching, or even looping workflows.
*   **Persistence & Resuming:** LangGraph offers mechanisms for persisting graph states, allowing workflows to be paused and resumed.
*   **Visualization:** (Often possible with LangGraph setups) Graphs can be visualized, making complex workflows easier to understand.
*   **Tool Integration:** LangGraph is designed to integrate well with "tools" (which our agent stubs represent).

## 5. Conceptual `run_log_new_observation_workflow` with LangGraph

1.  **`START`**: Input: `patient_id`, `observation_text`. These are added to the initial state.
2.  **`node_log_event`**:
    *   Reads `patient_id` and `observation_text` from state.
    *   Calls `call_shift_event_capture_agent`.
    *   Updates state with `log_confirmation`.
3.  **`node_fetch_profile` (for summary update - optional branch)**:
    *   Reads `patient_id` from state.
    *   Updates state with `patient_profile`.
4.  **`node_fetch_events` (for summary update - optional branch)**:
    *   Reads `patient_id` from state.
    *   Updates state with `patient_events` (which should ideally reflect the newly logged event if the underlying data source is updated, or could be manually updated in the state for simulation).
5.  **`node_generate_summary` (optional branch)**:
    *   Reads `patient_profile`, `patient_events` from state.
    *   Updates state with `generated_summary`.
6.  **`END`**.

This workflow could have a conditional edge after `node_log_event` to decide if the summary update branch (steps 3-5) is necessary or should be skipped.

## Conclusion

LangGraph provides a robust and flexible framework for orchestrating the various agents and tools within the Noah ecosystem. By defining clear nodes, managing state effectively, and using conditional edges, complex and intelligent workflows can be constructed to automate clinical information processing and task management. The stubs in `agent_interfaces.py` and the flows in `conceptual_workflows.py` provide a solid foundation for building such a LangGraph-powered system.
