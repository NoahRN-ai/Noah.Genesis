# backend/app/agents/hippocrates_agent.py
import logging
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import MemorySaver # Or other appropriate checkpointer

# from backend.app.services.llm_service import get_llm_response # May need to adapt for agent use
# from backend.app.core.config import settings # For agent-specific settings

logger = logging.getLogger(__name__)

# --- Agent State ---
class HippocratesAgentState(TypedDict):
    user_query: str
    conversation_history: List[dict] # Or use BaseMessage if converting
    research_question: str # Refined question for searching
    search_results: List[dict] # Store results from literature search
    analysis_summary: str # Summary of analyzed results
    final_response: str
    error_message: str | None

# --- Tool Placeholders ---
def medical_literature_search_tool(search_query: str, num_results: int = 5) -> List[dict]:
    """Placeholder: Simulates searching medical literature."""
    logger.info(f"Simulating medical literature search for: {search_query}")
    # In a real scenario, this would call Vertex AI Search, PubMed API, etc.
    # TODO: Replace with actual medical literature search tool integration
    return [
        {"title": "Mock Study 1 on " + search_query, "summary": "This is a mock summary.", "url": "http://example.com/study1"},
        {"title": "Mock Review 2 of " + search_query, "summary": "Another mock summary.", "url": "http://example.com/review2"},
    ]

# --- Node Functions ---
def start_research_node(state: HippocratesAgentState) -> HippocratesAgentState:
    logger.info("Hippocrates Agent: Starting research process")
    # Potentially refine user_query into a research_question
    # TODO: Add LLM call to refine user_query into a research_question
    state['research_question'] = state['user_query'] # Simple pass-through for now
    state['error_message'] = None
    return state

def conduct_medical_search_node(state: HippocratesAgentState) -> HippocratesAgentState:
    logger.info("Hippocrates Agent: Conducting medical literature search")
    try:
        search_query = state.get('research_question', state['user_query'])
        results = medical_literature_search_tool(search_query)
        state['search_results'] = results
    except Exception as e:
        logger.error(f"Error in medical search node: {e}")
        state['error_message'] = f"Failed to conduct medical search: {e}"
        state['search_results'] = []
    return state

def analyze_search_results_node(state: HippocratesAgentState) -> HippocratesAgentState:
    logger.info("Hippocrates Agent: Analyzing search results")
    if state.get('error_message'): return state # Skip if previous error

    results = state.get('search_results', [])
    if not results:
        state['analysis_summary'] = "No search results to analyze."
        return state
    # Simple analysis: concatenate summaries
    # TODO: Replace with LLM call to analyze/summarize search results
    summaries = [res.get('summary', 'No summary available.') for res in results]
    state['analysis_summary'] = "\n".join(summaries)
    return state

def synthesize_response_node(state: HippocratesAgentState) -> HippocratesAgentState:
    logger.info("Hippocrates Agent: Synthesizing final response")
    if state.get('error_message'):
        state['final_response'] = f"Sorry, an error occurred: {state['error_message']}"
        return state

    analysis = state.get('analysis_summary', "No analysis performed.")
    if not state.get('search_results'):
         state['final_response'] = "I couldn't find relevant medical literature for your query at the moment."
    else:
        # For MVP, could be a simple template. Later, an LLM call.
        # TODO: Replace with LLM call to synthesize response based on analysis and query
        # Example using an LLM call (conceptual, assuming get_llm_response can be adapted or a new one is made)
        # prompt = f"Based on the following analysis of medical literature, provide a concise answer to the query '{state['user_query']}':\n{analysis}"
        # state['final_response'] = await get_llm_response(prompt=prompt, conversation_history=[]) # Simplified call
        state['final_response'] = f"Based on my research on '{state['user_query']}':\n{analysis}\n\n(Note: This is a simplified response from the Hippocrates Agent MVP. Tools are placeholders.)"
    return state

# --- Graph Definition ---
# TODO: Add configuration for specific LLM model, system prompts, tool configurations
# This might involve a new section in `backend/app/core/config.py` or direct settings here.

workflow = StateGraph(HippocratesAgentState)

workflow.add_node("start_research", start_research_node)
workflow.add_node("conduct_search", conduct_medical_search_node)
workflow.add_node("analyze_results", analyze_search_results_node)
workflow.add_node("synthesize_response", synthesize_response_node)

workflow.set_entry_point("start_research")
workflow.add_edge("start_research", "conduct_search")
workflow.add_edge("conduct_search", "analyze_results")
workflow.add_edge("analyze_results", "synthesize_response")
workflow.add_edge("synthesize_response", END)

# Add memory for checkpoints if needed (e.g., for long-running research)
# checkpointer = MemorySaver()
# hippocrates_graph = workflow.compile(checkpointer=checkpointer)
hippocrates_graph = workflow.compile()

# --- Agent Entry Point ---
async def invoke_hippocrates_agent(user_query: str, conversation_history: List[dict] | None = None) -> str:
    logger.info(f"Invoking Hippocrates Agent for query: {user_query}")
    if conversation_history is None:
        conversation_history = []

    initial_state: HippocratesAgentState = {
        "user_query": user_query,
        "conversation_history": conversation_history,
        "research_question": "",
        "search_results": [],
        "analysis_summary": "",
        "final_response": "",
        "error_message": None,
    }

    config = {"recursion_limit": 10} # Basic config

    try:
        # Using ainvoke for asynchronous execution
        final_state_content = await hippocrates_graph.ainvoke(initial_state, config=config)

        if final_state_content and final_state_content.get('final_response'):
            logger.info(f"Hippocrates Agent final response: {final_state_content['final_response']}")
            return final_state_content['final_response']
        elif final_state_content and final_state_content.get('error_message'):
            logger.error(f"Hippocrates Agent error: {final_state_content['error_message']}")
            return final_state_content['error_message']
        else:
            logger.error("Hippocrates Agent did not produce a final response or error message.")
            return "Hippocrates Agent encountered an issue and could not provide a response."

    except Exception as e:
        logger.error(f"Error invoking Hippocrates agent graph: {e}", exc_info=True)
        return f"An unexpected error occurred while processing your request with the Hippocrates Agent: {e}"

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    import asyncio
    async def main_test():
        print("--- Testing Hippocrates Agent ---")
        test_query = "What are the latest treatments for type 2 diabetes?"
        response = await invoke_hippocrates_agent(test_query)
        print(f"Query: {test_query}")
        print(f"Response: {response}")

        test_query_2 = "Tell me about common cold."
        response_2 = await invoke_hippocrates_agent(test_query_2, [{"role": "user", "content": "Any previous context?"}])
        print(f"Query 2: {test_query_2}")
        print(f"Response 2: {response_2}")

    logging.basicConfig(level=logging.INFO) # Ensure logger output is visible for tests
    asyncio.run(main_test())
