from pydantic import BaseModel, Field

# --- Pydantic Input Schema for the RAG Tool (aligns with tools.py) ---
class RAGQueryInputArgs(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base.")

# --- Tool Name (ensure consistency) ---
RAG_TOOL_NAME = "retrieve_knowledge_base_tool" # Explicitly define, matching @tool name in tools.py

# --- RAG Tool Definition for LLM (e.g., Vertex AI Function Calling) ---
rag_tool_definition = {
    "name": RAG_TOOL_NAME,
    "description": (
        "Searches the clinical knowledge base to answer questions about critical care, "
        "medical protocols, patient guidelines, or other specific medical topics. "
        "Use this tool when the user's query requires factual information that is "
        "likely found within the curated medical documents and is not general knowledge. "
        "For example, use for 'What are the current sepsis bundle guidelines?' or 'Tell me about managing ARDS.' "
        "The query should be a clear, natural language question or a concise topic."
    ),
    "input_schema": RAGQueryInputArgs  # Use the renamed schema
}

# --- List of all available tool definitions ---
TOOL_DEFINITIONS = [
    rag_tool_definition,
    # Add other tool definitions here as your system grows
]

# --- Function to get Vertex AI compatible tool definitions ---
def get_vertex_ai_tool_definitions():
    """
    Generates a list of tool definitions formatted for Vertex AI function calling.
    """
    vertex_tools = []
    for tool_def in TOOL_DEFINITIONS:
        # Ensure the schema is correctly converted to JSON schema for Vertex AI
        parameters_schema = tool_def["input_schema"].model_json_schema()

        # Remove 'title' from schema if present and not desired by Vertex AI
        # parameters_schema.pop("title", None)

        vertex_tools.append(
            {
                "function_declarations": [
                    {
                        "name": tool_def["name"],
                        "description": tool_def["description"],
                        "parameters": parameters_schema
                    }
                ]
            }
        )
    return vertex_tools

# Example usage (optional, for testing or direct use):
# if __name__ == "__main__":
#     vertex_formatted_tools = get_vertex_ai_tool_definitions()
#     import json
#     print(json.dumps(vertex_formatted_tools, indent=2))
