from typing import List
from pydantic import BaseModel, Field # Added for explicit RAGQueryInput model
from vertexai.generative_models import Tool as VertexTool
from vertexai.generative_models import FunctionDeclaration

# --- Pydantic Model for RAG Tool Input (for documentation consistency) ---
# This explicitly defines the input structure the LLM should provide for the RAG tool.
# It must match the `args_schema` (RAGQueryInputArgs) of the `@tool` in `tools.py`.
class RAGQueryInput(BaseModel):
    query: str = Field(description="The specific question, topic, or keywords to search for in the clinical knowledge base. This should be a well-formed query derived from the user's current request.")

# --- Tool Name Constant ---
RAG_TOOL_NAME = "retrieve_knowledge_base"

# --- Vertex AI Tool Declaration for RAG ---
# This schema is provided to the LLM to inform it about the RAG tool's capabilities and expected arguments.
rag_tool_vertex_declaration = VertexTool(
    function_declarations=[
        FunctionDeclaration(
            name=RAG_TOOL_NAME,
            description=(
                "Searches the clinical knowledge base to answer questions about critical care, "
                "medical protocols, patient guidelines, or other specific medical topics. "
                "Use this tool when the user's query requires specific factual information that is "
                "likely found within curated medical documents and is not general knowledge or part of common sense. "
                "For example, for queries like 'What are the current sepsis bundle guidelines?' "
                "or 'Tell me about managing ARDS protocol details'."
            ),
            parameters={ # This schema structure MUST align with RAGQueryInput / RAGQueryInputArgs
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The specific question, keywords, or topic to search for effectively in the knowledge base. Formulate a clear and concise search query based on the user's need for information from the clinical knowledge base."
                    }
                },
                "required": ["query"]
            }
        )
    ]
)

# List of all available tools for the LLM (Vertex AI format)
# For MVP, this only contains the RAG tool.
AVAILABLE_TOOLS_SCHEMAS_FOR_LLM: List[VertexTool] = [
    rag_tool_vertex_declaration
    # Add other VertexTool declarations here if more tools are developed
]

# --- Helper Functions ---
def get_available_tools_for_llm() -> List[VertexTool]:
    """Returns the schemas of available tools for the LLM (Vertex AI format)."""
    return AVAILABLE_TOOLS_SCHEMAS_FOR_LLM

def get_tool_names() -> List[str]:
    """Returns a list of available tool names."""
    # This list helps the graph router identify if a tool requested by LLM is valid and implemented.
    return [RAG_TOOL_NAME] # Add other tool names here as they are implemented
