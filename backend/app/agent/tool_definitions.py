from typing import List, Dict, Any, Type
from pydantic import BaseModel, Field
from vertexai.generative_models import Tool as VertexTool
from vertexai.generative_models import FunctionDeclaration

# --- Pydantic Models for Tool Inputs (Example for RAG) ---
class RAGQueryInput(BaseModel):
    query: str = Field(description="The natural language query to search the knowledge base.")

# --- Tool Name Constants ---
RAG_TOOL_NAME = "retrieve_knowledge_base"

# --- Tool Schemas for Vertex AI Function Calling ---

# This schema defines the RAG tool for the LLM.
rag_tool_vertex_declaration = VertexTool(
    function_declarations=[
        FunctionDeclaration(
            name=RAG_TOOL_NAME,
            description="Searches the clinical knowledge base to answer questions about critical care, medical protocols, or patient guidelines. Use this if the user's query requires factual information beyond general knowledge or standard conversational abilities.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The specific question, topic, or keywords to search for in the knowledge base. This should be a well-formed query derived from the user's current request."
                    }
                },
                "required": ["query"]
            }
        )
    ]
)

# For MVP, this list contains only the RAG tool. Add other tools here as they are developed.
AVAILABLE_TOOLS_SCHEMAS_FOR_LLM: List[VertexTool] = [
    rag_tool_vertex_declaration
]

# --- Helper Functions ---

def get_available_tools_for_llm() -> List[VertexTool]:
    """Returns the schema of available tools for the LLM."""
    return AVAILABLE_TOOLS_SCHEMAS_FOR_LLM

def get_tool_names() -> List[str]:
    """Returns a list of available tool names."""
    # Add other tool names to this list if more tools are integrated.
    return [RAG_TOOL_NAME]
