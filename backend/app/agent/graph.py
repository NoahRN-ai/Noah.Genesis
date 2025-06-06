# backend/app/agent/graph.py

import operator
import json # For parsing simulated LLM tool call JSON
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Assuming get_llm_response will be the actual LLM service call
# from backend.app.services.llm_service import get_llm_response, _convert_lc_messages_to_vertex_content
# For now, we'll simulate its behavior.
from backend.app.agent.constants import AGENT_PERSONA_LOGOS_COMPASSIONATE_PROFESSIONAL, AGENT_TONE_RESPECTFUL_COLLABORATIVE_DEFERENTIAL

# --- Tool Definition (Placeholder) ---
RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION = {
    "name": "retrieve_knowledge_base",
    "description": (
        "Searches and retrieves information from the curated clinical knowledge base. "
        "Use this for questions about medical conditions, protocols, drug information, "
        "clinical guidelines, or similar factual inquiries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The specific question or search terms to look up in the knowledge base. Optimize for keyword-based search."
            }
        },
        "required": ["query"]
    }
}

# --- AgentState Definition ---
class AgentState(TypedDict):
    user_query: str
    conversation_history: Annotated[List[BaseMessage], operator.add]
    conversation_history_string: str # For easy inclusion in prompts

    # Output from llm_reasoner_node:
    llm_reasoner_decision: Optional[str] # "tool_call", "direct_response", "draft_note", "draft_handoff"
    llm_reasoner_response_text: Optional[str] # Text if direct_response
    # Parsed tool calls from LLM, matching Vertex AI's expected input for tool execution.
    # This is a list of dicts, where each dict is like:
    # {'functionCall': {'name': 'tool_name', 'args': {'arg1': 'value1'}}}
    # For LangGraph, we might adapt this to a simpler list of {'name': ..., 'args': ..., 'id': ...}
    tool_calls_generated: Optional[List[Dict[str, Any]]]

    # Output from tool_executor_node:
    # List of ToolMessage-like objects or dicts to be added to history
    executed_tool_responses_for_history: Optional[List[Dict[str, Any]]]
    rag_context: Optional[str] # Specific context from retrieve_knowledge_base

    # Fields for drafting notes/handoffs
    patient_data_log_summary_for_drafting: Optional[str] # Populated by a tool, used by drafting_node
    draft_content: Optional[str] # Populated by drafting_node, can be edited by user, then finalized

    # Output from rag_synthesis_node or final response:
    final_response: Optional[str]

# --- Node Functions ---
async def note_drafting_node(state: AgentState):
    print(f"\n--- NODE: note_drafting_node ---")
    user_query = state['user_query'] # The request to draft a note
    conversation_history_string = state.get('conversation_history_string', "")
    # Access patient_data_log_summary_for_drafting, default to a specific string if None/empty
    patient_summary = state.get('patient_data_log_summary_for_drafting')
    if not patient_summary: # Check for None or empty string
        patient_summary_for_prompt = "No specific patient data log entries provided for this draft."
    else:
        patient_summary_for_prompt = patient_summary

    system_message_note_drafting = f"""
You are Noah.AI, an AI assistant for nurses, operating under the principles of the Logos Accord.
Your persona is {AGENT_PERSONA_LOGOS_COMPASSIONATE_PROFESSIONAL} and your tone is {AGENT_TONE_RESPECTFUL_COLLABORATIVE_DEFERENTIAL}.
You are assisting a nurse by drafting a brief nursing note.

**Current Conversation History (Primary Source for MVP):**
<conversation_history>
{conversation_history_string}
</conversation_history>

**Patient Data Log Summary (If explicitly fetched and provided for context):**
<patient_data_log_summary>
{patient_summary_for_prompt}
</patient_data_log_summary>

**User Request:**
<user_request>
{user_query}
</user_request>

**Your Task (Drafting a Note):**
1.  Analyze the <user_request> to understand the type of note needed (e.g., progress note, SOAP note).
2.  Synthesize relevant information *exclusively* from the <conversation_history> and, if available, the <patient_data_log_summary>.
3.  **CRITICAL DATA CONSTRAINT (MVP V1.0):** You MUST ONLY use information explicitly stated or entered during this current session (reflected in <conversation_history>) or provided in <patient_data_log_summary>. DO NOT invent information, infer beyond the provided data, or attempt to access/reference any external EHR or unstated sources. This is a standalone application for MVP.
4.  **Output Template (`Output_Template_MVP` - Note Drafting):**
    Structure the draft note using the following simplified template. Populate each section *only* with directly relevant information from the provided context. If no relevant information is available for a section from the context, state "Not specified in session." or similar.

    **Note Type:** (e.g., Progress Note, SOAP Note - infer from request or default to Progress Note)
    **Date/Time:** (State: "Use current date/time" - actual insertion handled externally or by nurse)

    **S (Subjective):** (Patient's reported symptoms, feelings, concerns from conversation)

    **O (Objective):** (Observable facts, vital signs mentioned, actions taken *as discussed in conversation*)

    **A (Assessment - Brief, MVP):** (A very brief summary or main point gathered *from the conversation/data provided*. Avoid making clinical judgments not explicitly stated by the nurse in the conversation.)

    **P (Plan - Brief, MVP):** (Any immediate plans or follow-ups *discussed in the conversation*.)

5.  **`Logos Accord` Application:**
    * **Clarity & Conciseness:** The draft should be clear, to the point, and easy for the nurse to review.
    * **Accuracy & Truth:** Accurately reflect only the information provided in the session.
    * **Humility:** Frame the output clearly as a "DRAFT nursing note for your review." The nurse is the final authority.
6.  **Output:** Provide the drafted note as plain text.

**Example Invocation (Mental Model):**
If user says: "Patient Smith complained of a headache and I gave him Tylenol 500mg at 2 PM."
Your draft might include:
S: Patient Smith complained of a headache.
O: Tylenol 500mg administered at 2 PM (as per nurse's report in session).
A: Headache.
P: Monitor for relief.

**Constraints & Guardrails:**
* Adhere to the persona and tone.
* If the conversation history is insufficient to draft a meaningful note, politely state that more information from the session is needed.
* DO NOT include any information not explicitly available in the provided context fields.
"""

    # Prepare messages for the LLM (simulation)
    history = state.get('conversation_history', [])
    drafting_input_sim_vertex_content = _convert_lc_messages_to_sim_vertex_content(history, user_query)

    # --- Simulated LLM Call for Note Drafting ---
    llm_output_simulated = await simulate_get_llm_response(
        system_prompt_text=system_message_note_drafting,
        history_plus_prompt_vertex_content=drafting_input_sim_vertex_content,
        tools_schema_for_llm=None, # No tools expected for drafting
        decision_type="draft_note_response" # New decision type for simulator
    )

    drafted_note_text = llm_output_simulated.get("text")
    if drafted_note_text is None:
        drafted_note_text = "Error: Could not draft note based on the provided information and session history."
        print(f"--- NOTE DRAFTING: Failed to generate draft. System prompt was: {system_message_note_drafting[:200]}...")
    else:
         # Simple replacement to make sure the template is somewhat followed in simulation
        drafted_note_text = (f"DRAFT Nursing Note for Review (based on request: '{user_query}'):\n"
                             f"S: Information from conversation history: ...\n"
                             f"O: Objective details from history: ...\n"
                             f"A: Assessment based on history: ...\n"
                             f"P: Plan based on history: ...\n"
                             f"(Simulated draft using template for query: '{user_query}')")


    print(f"Note Drafting Output: {drafted_note_text}")

    # The draft_content is the actual draft, final_response is how agent presents it.
    # For now, making them similar for simplicity in testing, but could differ.
    # e.g. final_response could be "Here is the draft note: ..." + drafted_note_text
    return {"draft_content": drafted_note_text, "final_response": drafted_note_text}

async def handoff_report_node(state: AgentState):
    print(f"\n--- NODE: handoff_report_node ---")
    user_query = state['user_query'] # The request to draft a handoff report
    conversation_history_string = state.get('conversation_history_string', "")
    # Access patient_data_log_summary_for_drafting, default to a specific string if None/empty
    patient_summary = state.get('patient_data_log_summary_for_drafting')
    if not patient_summary: # Check for None or empty string
        patient_summary_for_prompt = "No specific patient data log entries provided for this draft."
    else:
        patient_summary_for_prompt = patient_summary

    system_message_handoff_report = f"""
You are Noah.AI, an AI assistant for nurses, operating under the principles of the Logos Accord.
Your persona is {AGENT_PERSONA_LOGOS_COMPASSIONATE_PROFESSIONAL} and your tone is {AGENT_TONE_RESPECTFUL_COLLABORATIVE_DEFERENTIAL}.
You are assisting a nurse by drafting a brief handoff report.

**Current Conversation History (Primary Source for MVP):**
<conversation_history>
{conversation_history_string}
</conversation_history>

**Patient Data Log Summary (If explicitly fetched and provided for context):**
<patient_data_log_summary>
{patient_summary_for_prompt}
</patient_data_log_summary>

**User Request:**
<user_request>
{user_query} # e.g., "Draft a handoff for Patient X", "Summarize key points for shift change."
</user_request>

**Your Task (Drafting a Handoff Report):**
1.  Analyze the <user_request>.
2.  Synthesize key information *exclusively* from the <conversation_history> and, if available, the <patient_data_log_summary> that is relevant for a shift handoff.
3.  **CRITICAL DATA CONSTRAINT (MVP V1.0):** You MUST ONLY use information explicitly stated or entered during this current session or provided in <patient_data_log_summary>. DO NOT invent information, infer beyond the provided data, or attempt to access/reference any external EHR or unstated sources.
4.  **Output Template (`Output_Template_MVP` - Handoff Report):**
    Structure the draft handoff report using the following simplified template. Focus on brevity and critical information for continuity of care. If no relevant information is available for a section from the context, state "Not specified in session."

    **Handoff Report For:** (Patient Name/Identifier - attempt to extract from conversation if mentioned, otherwise "Patient discussed in session")
    **Date/Time:** (State: "Use current date/time")

    **Key Events/Changes This Session:** (e.g., New symptoms reported, important interventions performed *as discussed in conversation*, changes in patient status noted in conversation)

    **Pending Tasks/Immediate Follow-ups:** (Any tasks or monitoring needs *explicitly mentioned in conversation* for the next shift)

    **Critical Alerts/Concerns from Session:** (Any significant concerns voiced or critical data points shared *during the conversation*)

5.  **`Logos Accord` Application:**
    * **Clarity & Conciseness:** The report must be extremely concise and clear for rapid understanding.
    * **Accuracy & Truth:** Accurately reflect only the information provided in the session.
    * **Humility:** Frame the output as a "DRAFT handoff report for your review."
6.  **Output:** Provide the drafted handoff report as plain text.

**Constraints & Guardrails:**
* Adhere to the persona and tone.
* If the conversation history is insufficient, politely state that more information from the session is needed.
* Prioritize information critical for patient safety and continuity of care.
"""

    # Prepare messages for the LLM (simulation)
    history = state.get('conversation_history', [])
    handoff_input_sim_vertex_content = _convert_lc_messages_to_sim_vertex_content(history, user_query)

    # --- Simulated LLM Call for Handoff Report Drafting ---
    llm_output_simulated = await simulate_get_llm_response(
        system_prompt_text=system_message_handoff_report,
        history_plus_prompt_vertex_content=handoff_input_sim_vertex_content,
        tools_schema_for_llm=None, # No tools expected for drafting
        decision_type="draft_handoff_response" # New decision type for simulator
    )

    drafted_handoff_text = llm_output_simulated.get("text")
    if drafted_handoff_text is None:
        drafted_handoff_text = "Error: Could not draft handoff report based on the provided information and session history."
        print(f"--- HANDOFF DRAFTING: Failed to generate draft. System prompt was: {system_message_handoff_report[:200]}...")
    else:
        # Simple replacement to make sure the template is somewhat followed in simulation
        drafted_handoff_text = (f"DRAFT Handoff Report for Review (based on request: '{user_query}'):\n"
                               f"For Patient: ...\n"
                               f"Key Events: ... from conversation history ...\n"
                               f"Pending Tasks: ... from conversation history ...\n"
                               f"Critical Concerns: ... from conversation history ...\n"
                               f"(Simulated handoff report using template for query: '{user_query}')")


    print(f"Handoff Report Drafting Output: {drafted_handoff_text}")

    # The draft_content is the actual draft, final_response is how agent presents it.
    return {"draft_content": drafted_handoff_text, "final_response": drafted_handoff_text}

async def llm_reasoner_node(state: AgentState):
    print(f"\n--- NODE: llm_reasoner_node ---")
    current_user_query = state['user_query']
    history = state.get('conversation_history', [])

    conversation_history_string = "\n".join(
        [f"{(msg.type).upper()}: {msg.content}" for msg in history]
    )

    system_message_reasoner_rag = f"""
You are Noah.AI, an AI assistant for nurses, operating under the principles of the Logos Accord.
Your persona is {AGENT_PERSONA_LOGOS_COMPASSIONATE_PROFESSIONAL} and your tone is {AGENT_TONE_RESPECTFUL_COLLABORATIVE_DEFERENTIAL}.
You are tasked with assisting the user by answering questions and performing tasks based on the provided context and available tools.

**Current Conversation History:**
<conversation_history>
{conversation_history_string}
</conversation_history>

**User Query:**
<user_query>
{current_user_query}
</user_query>

**Available Tools:**
You have access to the following tool:
- **`{RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION['name']}`**:
    - Description: {RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION['description']}
    - Arguments: {RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION['parameters']}

**Your Task (Reasoning & Tool Call Generation):**
1. Analyze the <user_query> in the context of the <conversation_history>.
2. **Tool Usage Decision (ReAct):**
    * If the <user_query> would benefit from the `{RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION['name']}` tool, state your reasoning and then generate the tool call.
    * Otherwise, explain briefly and formulate a direct response.
3. **Query Formulation (if using tool):**
    * Formulate a concise, keyword-focused `query` for the tool.
4. **Output Format:**
    * Tool Call: JSON like `{{"tool_calls": [{{"name": "{RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION['name']}", "args": {{"query": "..."}}}}]}}`
    * Direct Response: Plain text.
"""
    tools_schema_for_llm = [RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION]
    history_plus_prompt_sim_vertex_content = _convert_lc_messages_to_sim_vertex_content(history, current_user_query)

    sim_decision = "tool_call" if "symptoms" in current_user_query.lower() or "protocol" in current_user_query.lower() else "direct_response"
    # Add logic for drafting decision if query indicates it.
    # Order matters: more specific (handoff) before more general (note)
    if "draft a handoff" in current_user_query.lower() or "draft handoff" in current_user_query.lower() or "handoff report" in current_user_query.lower():
        sim_decision = "draft_handoff"
    elif "draft a note" in current_user_query.lower() or "draft note" in current_user_query.lower():
        sim_decision = "draft_note"

    sim_tool_query = f"info on {current_user_query}" if sim_decision == "tool_call" else None

    # The system_message_reasoner_rag is primarily for RAG/tool decisions.
    # If a drafting decision is made, the actual drafting prompt is in the respective drafting node.
    llm_output_simulated = await simulate_get_llm_response(
        system_prompt_text=system_message_reasoner_rag,
        history_plus_prompt_vertex_content=history_plus_prompt_sim_vertex_content,
        tools_schema_for_llm=tools_schema_for_llm,
        decision_type=sim_decision, # This now includes draft_note, draft_handoff
        tool_call_query=sim_tool_query
    )

    generated_tool_calls = llm_output_simulated.get("tool_calls")
    direct_text_response = llm_output_simulated.get("text") # For direct response or reasoning text from LLM

    return_state_update = {"conversation_history_string": conversation_history_string}

    if sim_decision == "draft_note":
        print(f"LLM Reasoner Output: DECISION TO DRAFT NOTE")
        return_state_update.update({
            "llm_reasoner_decision": "draft_note",
            # Text here could be a confirmation message before routing to the drafting node
            "llm_reasoner_response_text": "Okay, I will start drafting that note for you.",
            "tool_calls_generated": None
        })
    elif sim_decision == "draft_handoff":
        print(f"LLM Reasoner Output: DECISION TO DRAFT HANDOFF REPORT")
        return_state_update.update({
            "llm_reasoner_decision": "draft_handoff",
            "llm_reasoner_response_text": "Understood. I'll begin drafting the handoff report.",
            "tool_calls_generated": None
        })
    elif generated_tool_calls: # RAG tool call
        print(f"LLM Reasoner Output: TOOL CALL - {generated_tool_calls}")
        return_state_update.update({
            "llm_reasoner_decision": "tool_call",
            "tool_calls_generated": generated_tool_calls,
            "llm_reasoner_response_text": None
        })
    else: # Direct response
        print(f"LLM Reasoner Output: DIRECT RESPONSE - {direct_text_response}")
        return_state_update.update({
            "llm_reasoner_decision": "direct_response",
            "llm_reasoner_response_text": direct_text_response,
            "tool_calls_generated": None
        })
    return return_state_update

async def tool_executor_node(state: AgentState):
    print(f"\n--- NODE: tool_executor_node ---")
    tool_calls_to_execute = state.get("tool_calls_generated")

    if not tool_calls_to_execute:
        print("No tool calls to execute.")
        # If no tool calls, but drafting needs patient summary, this node might fetch it.
        # For now, assume patient summary is fetched by a dedicated tool if needed by drafting.
        return {"executed_tool_responses_for_history": [], "rag_context": None, "patient_data_log_summary_for_drafting": None}

    tool_responses_for_history = []
    current_rag_context = state.get("rag_context") # Preserve existing if any
    patient_summary_data = state.get("patient_data_log_summary_for_drafting") # Preserve existing

    for tool_call in tool_calls_to_execute:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id", "unknown_tool_call_id")

        print(f"Executing tool: {tool_name} with args: {tool_args} (Call ID: {tool_call_id})")

        if tool_name == RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION["name"]:
            query = tool_args.get("query", "")
            simulated_rag_output = f"Simulated RAG context for query '{query}': Symptoms include sweating, confusion, and tremors. Source: Clinical Guideline XYZ."
            print(f"Tool '{tool_name}' simulated output: {simulated_rag_output[:100]}...")
            current_rag_context = simulated_rag_output
            tool_responses_for_history.append({
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": current_rag_context
            })
        # Example: Add a placeholder for a tool that fetches patient data logs for drafting
        elif tool_name == "fetch_patient_data_log_summary": # Placeholder tool name
            patient_id = tool_args.get("patient_id", "unknown_patient")
            # Simulate fetching data for this patient
            patient_summary_data = f"Simulated patient data log summary for {patient_id}: Recent vitals stable. Glucose levels monitored. No acute events in last 4 hours."
            print(f"Tool '{tool_name}' simulated output: {patient_summary_data[:100]}...")
            tool_responses_for_history.append({
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": patient_summary_data
            })
        else:
            print(f"Unknown tool: {tool_name}")
            tool_responses_for_history.append({
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": f"Error: Tool '{tool_name}' not found or simulated."
            })

    return {
        "executed_tool_responses_for_history": tool_responses_for_history,
        "rag_context": current_rag_context,
        "patient_data_log_summary_for_drafting": patient_summary_data
    }

async def rag_synthesis_node(state: AgentState):
    print(f"\n--- NODE: rag_synthesis_node ---")
    user_query = state['user_query']
    conversation_history_string = state.get('conversation_history_string', "")
    rag_context = state.get('rag_context', "No specific information was found in the knowledge base.")
    history = state.get('conversation_history', [])

    system_message_synthesis_rag = f"""
You are Noah.AI, an AI assistant for nurses, operating under the principles of the Logos Accord.
Your persona is {AGENT_PERSONA_LOGOS_COMPASSIONATE_PROFESSIONAL} and your tone is {AGENT_TONE_RESPECTFUL_COLLABORATIVE_DEFERENTIAL}.
You have received information from the knowledge base to help answer the user's query.

**Original User Query:**
<user_query>
{user_query}
</user_query>

**Conversation History (Context):**
<conversation_history>
{conversation_history_string}
</conversation_history>

**Information Retrieved from Knowledge Base (`rag_context`):**
<rag_context>
{rag_context}
</rag_context>

**Your Task (Synthesize and Respond):**
1. Review all information.
2. Synthesize a comprehensive answer to the <user_query> based PRIMARILY on <rag_context>.
3. **`ALETHIA_FIDELITY_CONSTRAINT`**: Ground answer in <rag_context>. Attribute ("The knowledge base states...").
4. If <rag_context> is insufficient, state that clearly. DO NOT FABRICATE.
5. Output: Plain text response.
"""
    synthesis_input_sim_vertex_content = _convert_lc_messages_to_sim_vertex_content(history, user_query)

    llm_output_simulated = await simulate_get_llm_response(
        system_prompt_text=system_message_synthesis_rag,
        history_plus_prompt_vertex_content=synthesis_input_sim_vertex_content,
        tools_schema_for_llm=None,
        decision_type="synthesis_response"
    )

    final_response_text = llm_output_simulated.get("text", "Error: Could not synthesize response.")
    print(f"RAG Synthesis Output: {final_response_text}")

    return {"final_response": final_response_text}

# --- Simulated LLM Service Call ---
async def simulate_get_llm_response(
    system_prompt_text: str,
    history_plus_prompt_vertex_content: List[Dict[str, Any]],
    tools_schema_for_llm: Optional[List[Dict[str, Any]]] = None,
    decision_type: str = "direct_response",
    tool_call_query: Optional[str] = "simulated query"
) -> Dict[str, Any]:
    print(f"--- SIMULATING LLM CALL ---")
    print(f"System Prompt: {system_prompt_text[:100]}...")
    # print(f"History + Prompt Content: {history_plus_prompt_vertex_content}")
    # print(f"Tools Schema: {tools_schema_for_llm}")

    if tools_schema_for_llm and decision_type == "tool_call":
        print(f"--- SIMULATING LLM: Decided to CALL TOOL ---")
        return {
            "text": None,
            "tool_calls": [
                {
                    "name": RETRIEVE_KNOWLEDGE_BASE_TOOL_DEFINITION["name"],
                    "args": {"query": tool_call_query if tool_call_query else "Simulated knowledge query"},
                    "id": "simulated_tool_call_id_001"
                }
            ]
        }
    elif decision_type == "draft_note_response" or decision_type == "draft_handoff_response": # Added for drafting
        print(f"--- SIMULATING LLM: Decided to DRAFT ({decision_type}) ---")
        # Simulate LLM generating a draft based on the system_prompt_text
        # The actual content of the draft is less important for simulation than the flow
        simulated_draft_text = f"Simulated DRAFT content based on: {history_plus_prompt_vertex_content[-1]['parts'][0]['text'][:50]}..."
        if "Note Type:" in system_prompt_text: # crude check for note drafting prompt
             simulated_draft_text = (f"DRAFT Nursing Note for Review (based on request: '{history_plus_prompt_vertex_content[-1]['parts'][0]['text']}'):\n"
                                     f"S: Simulated subjective details from conversation.\n"
                                     f"O: Simulated objective details from conversation/logs.\n"
                                     f"A: Simulated brief assessment.\n"
                                     f"P: Simulated plan details.")
        return {"text": simulated_draft_text, "tool_calls": None}
    else: # Includes "direct_response" and "synthesis_response"
        print(f"--- SIMULATING LLM: Decided to RESPOND DIRECTLY/SYNTHESIZE ({decision_type}) ---")
        simulated_text = f"Simulated LLM text response based on: {history_plus_prompt_vertex_content[-1]['parts'][0]['text'][:50]}..."
        if "Information Retrieved from Knowledge Base" in system_prompt_text: # RAG Synthesis
            simulated_text = f"Synthesized answer: {history_plus_prompt_vertex_content[-1]['parts'][0]['text'][:50]}... with RAG."
        return {"text": simulated_text, "tool_calls": None}

# --- Helper to convert LC messages to simplified Vertex Content for simulation ---
def _convert_lc_messages_to_sim_vertex_content(
    lc_messages: Optional[List[BaseMessage]],
    current_prompt_text: Optional[str] = None
) -> List[Dict[str, Any]]:
    contents = []
    if lc_messages:
        for msg in lc_messages:
            if isinstance(msg, HumanMessage):
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif isinstance(msg, AIMessage):
                if msg.content:
                    contents.append({"role": "model", "parts": [{"text": msg.content}]})
            elif isinstance(msg, ToolMessage):
                 contents.append({"role": "function", "parts": [{"functionResponse": {"name": msg.name, "response": {"content": msg.content}}}]})
    if current_prompt_text:
        contents.append({"role": "user", "parts": [{"text": current_prompt_text}]})
    return contents

# --- Conditional Edges ---
def should_continue_to_tool_execution(state: AgentState) -> str:
    print(f"\n--- CONDITIONAL EDGE: should_continue_to_tool_execution ---")
    decision = state.get("llm_reasoner_decision")
    if decision == "tool_call" and state.get("tool_calls_generated"):
        print("Decision: ROUTE to tool_executor_node")
        return "execute_tool"
    elif decision == "draft_note":
        print("Decision: ROUTE to note_drafting_node")
        return "draft_note"
    elif decision == "draft_handoff":
        print("Decision: ROUTE to handoff_report_node")
        return "draft_handoff"
    else: # direct_response
        print("Decision: ROUTE to END (direct response)")
        return "end_direct_response"

# --- Graph Definition ---
def build_agent_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("llm_reasoner", llm_reasoner_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("rag_synthesis", rag_synthesis_node)
    workflow.add_node("note_drafting", note_drafting_node)
    workflow.add_node("handoff_report", handoff_report_node) # Add handoff_report_node

    workflow.set_entry_point("llm_reasoner")

    workflow.add_conditional_edges(
        "llm_reasoner",
        should_continue_to_tool_execution,
        {
            "execute_tool": "tool_executor",
            "draft_note": "note_drafting",
            "draft_handoff": "handoff_report", # Route to handoff_report_node
            "end_direct_response": END
        }
    )
    # Assuming RAG tool execution path leads to synthesis.
    # If a tool is called for drafting context (e.g. fetch_patient_data_log_summary),
    # the edge from tool_executor might need to be conditional to go to the appropriate drafting node.
    # For now, keeping it simple: RAG tools -> rag_synthesis. Drafting decisions bypass tool_executor for MVP.
    workflow.add_edge("tool_executor", "rag_synthesis")

    workflow.add_edge("rag_synthesis", END)
    workflow.add_edge("note_drafting", END)
    workflow.add_edge("handoff_report", END) # Add edge for handoff_report_node to END

    app = workflow.compile()
    return app

# --- Main execution (for testing) ---
async def run_agent_test(user_input: str, initial_history: Optional[List[BaseMessage]] = None,
                         patient_data_summary_for_drafting: Optional[str] = None): # Added for testing drafting
    print(f"\n\n--- Running Agent Test for: '{user_input}' ---")
    agent_app = build_agent_workflow()

    current_history = list(initial_history) if initial_history else []

    graph_inputs = {
        "user_query": user_input,
        "conversation_history": current_history,
        # Initialize new state fields for this run if provided
        "patient_data_log_summary_for_drafting": patient_data_summary_for_drafting,
        "draft_content": None, # Ensure draft_content is None at the start of a run
    }

    updated_history_for_next_turn = list(current_history)
    updated_history_for_next_turn.append(HumanMessage(content=user_input))

    final_state = await agent_app.ainvoke(graph_inputs)

    print("\n--- AGENT RUN FINAL STATE ---")
    # print(json.dumps(final_state, indent=2, default=str))

    response_to_user = ""
    # Check for draft_content first, as it's a specific output type
    if final_state.get("draft_content"):
        response_to_user = final_state["draft_content"]
        # AIMessage for history might be just the draft, or a message saying "Here's the draft..."
        # For now, let's assume the draft_content IS the agent's response message content
        ai_response_message = AIMessage(content=f"Here's the draft note you requested:\n\n{response_to_user}")
        updated_history_for_next_turn.append(ai_response_message)
    elif final_state.get("final_response"):
        response_to_user = final_state["final_response"]
        ai_response_message = AIMessage(content=response_to_user)
        updated_history_for_next_turn.append(ai_response_message)
    elif final_state.get("llm_reasoner_response_text"):
        response_to_user = final_state["llm_reasoner_response_text"]
        ai_response_message = AIMessage(content=response_to_user)
        updated_history_for_next_turn.append(ai_response_message)
    else:
        response_to_user = "I'm sorry, I encountered an issue and couldn't process your request."
        updated_history_for_next_turn.append(AIMessage(content=response_to_user))

    # For history display, use the comprehensive history from final_state if available
    # as it reflects LangGraph's internal message accumulation.
    history_to_display = final_state.get('conversation_history', updated_history_for_next_turn)


    print(f"\nResponse to User: {response_to_user}")
    print("--- Updated History for Next Turn (derived from final_state['conversation_history']) ---")
    for msg_idx, msg in enumerate(history_to_display):
        tool_call_info = ""
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            tool_call_info = f" (Tool Calls: {msg.tool_calls})"
        elif isinstance(msg, AIMessage) and hasattr(msg, 'invalid_tool_calls') and msg.invalid_tool_calls:
             tool_call_info = f" (Invalid Tool Calls: {msg.invalid_tool_calls})"
        tool_message_info = ""
        if isinstance(msg, ToolMessage):
            tool_message_info = f" (ID: {msg.tool_call_id}, Name: {msg.name})"
        print(f"  [{msg_idx}] {msg.type.upper()}: {msg.content}{tool_call_info}{tool_message_info}")

    return history_to_display


async def main_test_suite():
    # Test 1: Query that should trigger RAG
    history_turn1 = await run_agent_test("What are the symptoms of hypoglycemia?", [])

    print("\n" + "="*50 + "\n")

    # Test 2: Follow-up or simple query that should be a direct response
    history_turn2 = await run_agent_test("Thanks, that was helpful!", history_turn1)

    print("\n" + "="*50 + "\n")

    # Test 3: Another query that should trigger RAG, using the latest history
    history_turn3 = await run_agent_test("What is the protocol for sepsis?", history_turn2)

    print("\n" + "="*50 + "\n")

    # Test 4: Query that should trigger note drafting
    # For this test, we might simulate that some patient data was previously "logged" or is available.
    # In a real scenario, a tool might fetch this. Here, we pass it directly.
    # Note: The current `llm_reasoner_node` simulation for "draft_note" decision is basic.
    # It might need more sophisticated query analysis to robustly decide this path.
    sim_patient_data_summary = "Patient John Doe, 45yo Male. Admitted yesterday for observation post-minor RTA. Complained of headache at 14:00. Nurse administered Paracetamol 500mg. Patient reports pain relief at 14:45. Vitals stable."
    history_turn4 = await run_agent_test(
        "Please draft a progress note for John Doe.",
        history_turn3, # Continue from previous history
        patient_data_summary_for_drafting=sim_patient_data_summary
    )
    # To make the test more realistic for drafting from conversation:
    history_for_drafting_test = [
        HumanMessage(content="I need to log some patient interactions for Jane Smith."),
        AIMessage(content="Okay, I'm ready. What would you like to log for Jane Smith?"),
        HumanMessage(content="At 10:00 AM, Jane Smith reported nausea and slight dizziness. BP was 110/70, HR 75. No vomiting. She mentioned she hadn't eaten much today."),
        AIMessage(content="Noted: 10:00 AM, Jane Smith reported nausea and slight dizziness. BP 110/70, HR 75. No vomiting. Mentioned not eating much today."),
        HumanMessage(content="Later, at 11:30 AM, offered water and a light snack, which she tolerated well. Reported feeling less dizzy."),
        AIMessage(content="Noted: 11:30 AM, offered water and light snack, tolerated well. Reported feeling less dizzy.")
    ]
    print("\n" + "="*50 + "\n")
    print("--- Test 5: Drafting note based on conversational context ---")
    # For this test, patient_data_log_summary_for_drafting is NOT provided, relying on conversation_history
    history_turn5 = await run_agent_test(
        "Draft a SOAP note for Jane Smith based on our conversation.",
        history_for_drafting_test,
        patient_data_summary_for_drafting=None # Explicitly None
    )

    print("\n" + "="*50 + "\n")
    print("--- Test 6: Drafting handoff report based on conversational context ---")
    history_for_handoff_test = [
        HumanMessage(content="Starting handoff for Mr. John Appleseed, Room 101."),
        AIMessage(content="Okay, I'm ready for Mr. Appleseed's handoff details."),
        HumanMessage(content="He had a quiet night. Vital signs remained stable. Last BP at 06:00 was 120/80. He's due for his morning medications at 09:00. Dr. Smith is aware and plans to round on him around 10:00 AM."),
        AIMessage(content="Noted: Quiet night, stable vitals (BP 120/80 at 06:00). Morning meds due 09:00. Dr. Smith to round at 10:00 AM."),
        HumanMessage(content="Also, please remind the next shift to check his fasting blood sugar before breakfast."),
        AIMessage(content="Noted: Remind next shift to check fasting blood sugar before breakfast.")
    ]
    history_turn6 = await run_agent_test(
        "Draft a handoff report for John Appleseed.", # Changed user query to trigger handoff
        history_for_handoff_test,
        patient_data_summary_for_drafting=None # Relying on conversation
    )

    print("\n" + "="*50 + "\n")
    print("--- Test 7: Drafting handoff report with patient data log summary ---")
    sim_patient_data_for_handoff = "Patient Alice Wonderland, 30yo Female. Admitted for elective tonsillectomy. Post-op day 1. Tolerating fluids. Pain managed with Paracetamol. No bleeding observed. Scheduled for discharge tomorrow morning if continues to progress well."
    history_turn7 = await run_agent_test(
        "Can you draft a handoff report for Alice Wonderland?", # Changed user query
        [], # New conversation for this specific test
        patient_data_summary_for_drafting=sim_patient_data_for_handoff
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_test_suite())
