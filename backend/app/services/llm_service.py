import json
import logging
import os
from typing import Any, Optional

import vertexai
from google.api_core import exceptions as google_exceptions
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from vertexai.generative_models import (
    Content,
    FunctionCall,  # For constructing tool_call parts if received in history
    GenerationConfig,
    GenerativeModel,
    HarmBlockThreshold,
    HarmCategory,
    Part,
)

# Configure logging
logger = logging.getLogger(__name__)

# --- Vertex AI Initialization ---
# These should ideally be loaded from a centralized configuration (e.g., Pydantic BaseSettings via .env)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
VERTEX_AI_REGION = os.getenv("VERTEX_AI_REGION", "us-central1")  # Default if not set

_vertex_ai_initialized = False


def _init_vertex_ai_once():
    global _vertex_ai_initialized
    if not _vertex_ai_initialized:
        if not GCP_PROJECT_ID:
            logger.warning(
                "GCP_PROJECT_ID environment variable not set. LLM service may fail."
            )
            # Or raise ConfigurationError
        else:
            try:
                vertexai.init(project=GCP_PROJECT_ID, location=VERTEX_AI_REGION)
                _vertex_ai_initialized = True
                logger.info(
                    f"Vertex AI initialized for project {GCP_PROJECT_ID} in region {VERTEX_AI_REGION}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                # Potentially raise or handle to prevent app startup if critical


_init_vertex_ai_once()


# --- Default Configurations ---
DEFAULT_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

DEFAULT_GENERATION_CONFIG = GenerationConfig(
    temperature=0.7,  # Controls randomness. Lower for more deterministic.
    top_p=0.95,  # Nucleus sampling.
    # max_output_tokens=2048, # Varies by model, can be set if needed
)


# --- Helper for Message Conversion ---
def _convert_lc_messages_to_vertex_content(
    lc_messages: Optional[list[BaseMessage]], current_prompt: Optional[str] = None
) -> list[Content]:
    """Converts a list of LangChain BaseMessage objects and an optional current prompt
    into a list of Vertex AI Content objects.
    """
    vertex_contents: list[Content] = []

    if lc_messages:
        for lc_msg in lc_messages:
            if isinstance(lc_msg, HumanMessage):
                vertex_contents.append(
                    Content(role="user", parts=[Part.from_text(lc_msg.content)])
                )
            elif isinstance(lc_msg, AIMessage):
                model_parts = []
                if (
                    lc_msg.content
                    and isinstance(lc_msg.content, str)
                    and lc_msg.content.strip()
                ):  # Ensure content is not empty string for part
                    model_parts.append(Part.from_text(lc_msg.content))

                # LangChain ToolCall is a dict: {'name': str, 'args': Dict, 'id': str}
                # Vertex AI FunctionCall is an object FunctionCall(name=..., args=...)
                if lc_msg.tool_calls:
                    for tc in lc_msg.tool_calls:
                        # Assuming tc is a dict as per LangChain AIMessage.tool_calls structure
                        # Ensure args are properly structured if they come from Pydantic models initially
                        args_dict = tc.get("args", {})
                        if not isinstance(args_dict, dict):  # Should already be dict
                            try:
                                args_dict = (
                                    json.loads(str(args_dict))
                                    if isinstance(args_dict, str)
                                    else dict(args_dict)
                                )
                            except:
                                args_dict = {}

                        model_parts.append(
                            Part.from_function_call(
                                FunctionCall(name=tc["name"], args=args_dict)
                            )
                        )

                if model_parts:  # Only add if there's text or tool calls
                    vertex_contents.append(Content(role="model", parts=model_parts))
                elif not lc_msg.tool_calls:  # If no text and no tool_calls, log warning or handle empty AIMessage
                    logger.debug(
                        "AIMessage with no text content or tool_calls encountered in history."
                    )

            elif isinstance(lc_msg, ToolMessage):
                # ToolMessage content is often JSON string from tool execution
                # Vertex AI FunctionResponse part expects a dict for the response content.
                response_data_dict = {
                    "content": lc_msg.content
                }  # Default if content is simple string
                try:
                    # Attempt to parse if lc_msg.content is a JSON string representing a dict
                    parsed_content = json.loads(lc_msg.content)
                    if isinstance(parsed_content, dict):
                        response_data_dict = parsed_content
                except (json.JSONDecodeError, TypeError):
                    # If not a JSON string or not a dict, keep as {"content": lc_msg.content}
                    pass

                vertex_contents.append(
                    Content(
                        role="function",  # Vertex AI expects "function" role for tool responses
                        parts=[
                            Part.from_function_response(
                                name=lc_msg.name,  # Name of the function/tool that was called
                                response=response_data_dict,
                            )
                        ],
                    )
                )
            # SystemMessage could be handled here if needed, typically as the first "user" or "model" content.
            # For GenerativeModel, system prompts are often part of the model config or first Content obj.

    # Add the current user prompt as the last message
    if current_prompt:
        vertex_contents.append(
            Content(role="user", parts=[Part.from_text(current_prompt)])
        )

    return vertex_contents


# Define what exceptions to retry on
RETRYABLE_EXCEPTIONS = (
    google_exceptions.Aborted,
    google_exceptions.DeadlineExceeded,
    google_exceptions.InternalServerError,
    google_exceptions.ResourceExhausted,  # Often for quota limits
    google_exceptions.ServiceUnavailable,
    google_exceptions.Unknown,
)

# Retry decorator configuration
# Waits 1s * 2^attempt_number, up to 60s, for 5 attempts.
llm_retry_decorator = retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
)


@llm_retry_decorator
async def _generate_content_with_retry(
    model: GenerativeModel,
    contents: list[Content],
    generation_config: GenerationConfig,
    safety_settings: dict[HarmCategory, HarmBlockThreshold],
    tools: Optional[
        list[Any]
    ] = None,  # Placeholder for vertexai.generative_models.Tool schema
) -> Any:  # vertexai.generative_models.GenerateContentResponse
    """Internal function to call LLM with retry logic."""
    try:
        logger.debug(
            f"Sending to Vertex AI GenModel.generate_content. Contents: {contents}, Tools: {tools is not None}"
        )
        # The 'tools' argument for structured output/function calling will be provided by LangGraph in Phase 3.
        # For now, this service mainly handles text generation based on history.
        # If LangGraph itself pre-formats a prompt that includes tool schemas and asks the LLM to produce JSON,
        # this function remains simple. If this function needs to pass structured tool schemas,
        # the 'tools' parameter here will be used.
        if tools:
            response = await model.generate_content_async(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
                tools=tools,
            )
        else:
            response = await model.generate_content_async(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
            )
        return response
    except google_exceptions.GoogleAPICallError as e:
        logger.error(f"Vertex AI API call error: {e}", exc_info=True)
        raise  # Re-raise to be caught by tenacity or higher-level handler
    except Exception as e:  # Catch other unexpected errors
        logger.error(
            f"Unexpected error during LLM content generation: {e}", exc_info=True
        )
        raise  # Re-raise for visibility


async def get_llm_response(
    prompt: str,
    conversation_history: Optional[list[BaseMessage]] = None,
    llm_model_name: str = "gemini-1.0-pro-001",  # More specific Gemini 1.0 Pro version
    generation_config_override: Optional[GenerationConfig] = None,
    safety_settings_override: Optional[dict[HarmCategory, HarmBlockThreshold]] = None,
    tools_schema: Optional[
        list[Any]
    ] = None,  # Placeholder for vertexai.generative_models.Tool objects
) -> str:
    """Gets a textual response from a specified LLM model on Vertex AI.

    Args:
    ----
        prompt: The current user prompt or query.
        conversation_history: A list of LangChain BaseMessage objects representing prior turns.
        llm_model_name: The name/ID of the Vertex AI model to use (e.g., "gemini-1.5-flash-preview-0514", "gemini-1.0-pro-001").
        generation_config_override: Optional override for model generation parameters.
        safety_settings_override: Optional override for content safety settings.
        tools_schema: Optional list of tools (function declarations) for the model to consider.
                      This will typically be assembled and passed by LangGraph.

    Returns:
    -------
        The LLM's textual response. Returns an empty string or error message on failure.
    """
    if not _vertex_ai_initialized:
        logger.error("Vertex AI not initialized. Cannot get LLM response.")
        return "Error: LLM service not available (Vertex AI not initialized)."

    try:
        model = GenerativeModel(llm_model_name)

        # Prepare content list for Vertex AI
        # The `prompt` is the latest user message in the conversation sequence
        vertex_content_list = _convert_lc_messages_to_vertex_content(
            conversation_history, prompt
        )

        if not vertex_content_list:
            logger.warning("No content to send to LLM (empty prompt and history).")
            return ""

        current_generation_config = (
            generation_config_override
            if generation_config_override
            else DEFAULT_GENERATION_CONFIG
        )
        current_safety_settings = (
            safety_settings_override
            if safety_settings_override
            else DEFAULT_SAFETY_SETTINGS
        )

        response = await _generate_content_with_retry(
            model,
            vertex_content_list,
            current_generation_config,
            current_safety_settings,
            tools=tools_schema,
        )

        # --- Token Usage Tracking Placeholder (dynamous.ai contribution) ---
        # Access token counts from response.usage_metadata if available and needed.
        # Example:
        # if hasattr(response, 'usage_metadata'):
        # prompt_tokens = response.usage_metadata.prompt_token_count
        # candidates_tokens = response.usage_metadata.candidates_token_count
        # total_tokens = response.usage_metadata.total_token_count
        # logger.info(f"LLM Token Usage - Prompt: {prompt_tokens}, Candidates: {candidates_tokens}, Total: {total_tokens}")
        # This data can be logged or sent to a monitoring system for cost analysis.
        # The exact structure of usage_metadata can vary by model and SDK version.

        # Process response - check for blocked content or errors first
        if not response.candidates:
            logger.warning(
                f"LLM response for model {llm_model_name} had no candidates. Finish reason: {response.prompt_feedback.block_reason if response.prompt_feedback else 'Unknown'}"
            )
            # Consider specific handling for response.prompt_feedback.block_reason_message
            return "Error: LLM response was blocked or empty."

        first_candidate = response.candidates[0]

        # Check for function calls
        if first_candidate.content and first_candidate.content.parts:
            all_text_parts = []
            # If function calling is used, LangGraph will handle this part.
            # This service should aim to return the raw LLM output which might include function calls
            # or the text part. For a simple text response, we look for text parts.
            # LangGraph (in Task 3.1) will be responsible for parsing this and deciding next steps if there's a function call.
            # This service, for now, should primarily return text. If it *only* returns a function call, text might be empty.

            # For now, let's assume we concatenate all text parts for the simplest abstraction
            # However, if a function call is present, the expectation of "text response" might change.
            # For robust integration with LangGraph, returning the full candidate or structured parts
            # might be better. But prompt asks for "LLM's text response" (string).

            # If there's a function call, this service's role in returning "text response" is tricky.
            # LangGraph needs the structured tool call. This service is the "raw LLM call".
            # Let's try to extract simple text if available, and note that complex responses
            # (like tool calls) will be handled by the calling layer (LangGraph).

            # A more robust return could be a Pydantic model:
            # class LLMServiceResponse: text: Optional[str]; tool_calls: Optional[List[dict]]
            # For now, sticking to string return as per prompt.

            for part in first_candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    all_text_parts.append(part.text)
                # If part is a function call, LangGraph (the caller) will need to handle it.
                # We are not executing functions here, just relaying what the LLM said.
                # For this function to return *just text*, if a function_call is the only part,
                # the text might be empty or just the LLM's reasoning before the call.

            if all_text_parts:
                return "".join(all_text_parts)
            elif any(
                hasattr(part, "function_call") for part in first_candidate.content.parts
            ):
                # LLM returned a function call, but no accompanying text.
                # LangGraph needs the structured call, not an empty string from here.
                # For now, to fit "returns LLM's text response", we might return a placeholder.
                # This highlights a slight tension between "simple text response" and full LLM capability.
                # For MVP and this service's current signature, it will primarily aim to return aggregated text.
                # The next layer (LangGraph) will more intelligently parse `response.candidates[0]`.
                logger.info(
                    f"LLM for model {llm_model_name} returned function call(s) without accompanying text."
                )
                # To fully support LangGraph's tool usage, the response of this function might need to be more structured
                # (e.g., returning the raw Candidate object or a Pydantic model).
                # For MVP strict "text response":
                return ""  # Or a conventional string indicating a tool call happened, e.g., "[TOOL_CALL_INTENT]"
            else:  # No text and no function call parts
                logger.warning(
                    f"LLM response candidate for model {llm_model_name} had parts but no parsable text or function calls."
                )
                return ""

        logger.warning(
            f"LLM response for model {llm_model_name} was empty or in an unexpected format."
        )
        return ""

    except google_exceptions.RetryError as e:  # Tenacity's RetryError
        logger.error(
            f"LLM call failed after multiple retries for model {llm_model_name}: {e.last_attempt.exception()}",
            exc_info=True,
        )
        return f"Error: LLM call failed after retries ({e.last_attempt.exception()})."
    except (
        google_exceptions.InvalidArgument
    ) as e:  # Often bad model name or malformed request
        logger.error(
            f"LLM call failed due to InvalidArgument for model {llm_model_name}: {e}",
            exc_info=True,
        )
        return f"Error: LLM request was invalid ({e}). Check model name and parameters."
    except google_exceptions.PermissionDenied as e:  # ADC or SA permissions issue
        logger.error(
            f"LLM call failed due to PermissionDenied for model {llm_model_name}: {e}",
            exc_info=True,
        )
        return "Error: Permission denied for LLM service. Check service account permissions for Vertex AI."
    except Exception as e:  # Catch-all for other unexpected errors
        logger.error(
            f"Unexpected error in get_llm_response for model {llm_model_name}: {e}",
            exc_info=True,
        )
        return f"Error: An unexpected error occurred with the LLM service ({type(e).__name__})."
