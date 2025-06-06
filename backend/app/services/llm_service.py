import os
import json
import logging
from typing import List, Optional, Dict, Any

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Part,
    Content,
    FunctionCall, # For constructing tool_call parts if received in history
    FunctionResponse, # For constructing tool_response parts if received in history
    HarmCategory,
    HarmBlockThreshold,
    GenerationConfig
)
from google.api_core import exceptions as google_exceptions
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage

from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type

from backend.app.core.exceptions import LLMError, LLMConnectionError, LLMResponseError, InvalidInputError

# Configure logging
logger = logging.getLogger(__name__)

# --- Vertex AI Initialization ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
VERTEX_AI_REGION = os.getenv("VERTEX_AI_REGION", "us-central1")

_vertex_ai_initialized = False

def _init_vertex_ai_once():
    global _vertex_ai_initialized
    if not _vertex_ai_initialized:
        if not GCP_PROJECT_ID:
            logger.warning("GCP_PROJECT_ID environment variable not set. LLM service may fail.")
        else:
            try:
                vertexai.init(project=GCP_PROJECT_ID, location=VERTEX_AI_REGION)
                _vertex_ai_initialized = True
                logger.info(f"Vertex AI initialized for project {GCP_PROJECT_ID} in region {VERTEX_AI_REGION}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")

_init_vertex_ai_once()

# --- Default Configurations ---
DEFAULT_LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-1.0-pro-001")

DEFAULT_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

DEFAULT_GENERATION_CONFIG = GenerationConfig(
    temperature=float(os.getenv("LLM_TEMPERATURE", 0.7)),
    top_p=float(os.getenv("LLM_TOP_P", 0.95)),
    **({"max_output_tokens": int(os.environ["LLM_MAX_OUTPUT_TOKENS"])} if "LLM_MAX_OUTPUT_TOKENS" in os.environ else {})
)

# --- Helper for Message Conversion ---
def _convert_lc_messages_to_vertex_content(
    lc_messages: Optional[List[BaseMessage]],
    current_prompt: Optional[str] = None
) -> List[Content]:
    vertex_contents: List[Content] = []
    if lc_messages:
        for lc_msg in lc_messages:
            if isinstance(lc_msg, HumanMessage):
                vertex_contents.append(Content(role="user", parts=[Part.from_text(lc_msg.content)]))
            elif isinstance(lc_msg, AIMessage):
                model_parts = []
                if lc_msg.content and isinstance(lc_msg.content, str) and lc_msg.content.strip():
                    model_parts.append(Part.from_text(lc_msg.content))
                if lc_msg.tool_calls:
                    for tc in lc_msg.tool_calls:
                        args_dict = tc.get("args", {})
                        if not isinstance(args_dict, dict):
                           try: args_dict = json.loads(str(args_dict)) if isinstance(args_dict, str) else dict(args_dict)
                           except: args_dict = {}
                        model_parts.append(Part.from_function_call(
                            FunctionCall(name=tc["name"], args=args_dict)
                        ))
                if model_parts:
                    vertex_contents.append(Content(role="model", parts=model_parts))
                elif not lc_msg.tool_calls:
                    logger.debug("AIMessage with no text content or tool_calls encountered in history.")
            elif isinstance(lc_msg, ToolMessage):
                response_data_dict = {"content": lc_msg.content}
                try:
                    parsed_content = json.loads(lc_msg.content)
                    if isinstance(parsed_content, dict):
                        response_data_dict = parsed_content
                except (json.JSONDecodeError, TypeError):
                    pass
                vertex_contents.append(Content(
                    role="function",
                    parts=[Part.from_function_response(
                        name=lc_msg.name,
                        response=response_data_dict
                    )]
                ))
    if current_prompt:
        vertex_contents.append(Content(role="user", parts=[Part.from_text(current_prompt)]))
    return vertex_contents

RETRYABLE_EXCEPTIONS = (
    google_exceptions.Aborted,
    google_exceptions.DeadlineExceeded,
    google_exceptions.InternalServerError,
    google_exceptions.ResourceExhausted,
    google_exceptions.ServiceUnavailable,
    google_exceptions.Unknown,
)

llm_retry_decorator = retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS)
)

@llm_retry_decorator
async def _generate_content_with_retry(
    model: GenerativeModel,
    contents: List[Content],
    generation_config: GenerationConfig,
    safety_settings: Dict[HarmCategory, HarmBlockThreshold],
    tools: Optional[List[Any]] = None
) -> Any:
    try:
        logger.debug(f"Sending to Vertex AI GenModel.generate_content. Contents: {contents}, Tools: {tools is not None}")
        if tools:
             response = await model.generate_content_async(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings,
                tools=tools
            )
        else:
            response = await model.generate_content_async(
                contents,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        return response
    except google_exceptions.GoogleAPICallError as e:
        logger.error(f"Vertex AI API call error: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during LLM content generation: {e}", exc_info=True)
        raise

async def get_llm_response(
    prompt: str,
    conversation_history: Optional[List[BaseMessage]] = None,
    llm_model_name: Optional[str] = None,
    generation_config_override: Optional[GenerationConfig] = None,
    safety_settings_override: Optional[Dict[HarmCategory, HarmBlockThreshold]] = None,
    tools_schema: Optional[List[Any]] = None
) -> str:
    if not _vertex_ai_initialized:
        logger.error("Vertex AI not initialized. Cannot get LLM response.")
        raise LLMConnectionError(detail="LLM service not available (Vertex AI not initialized).")

    current_model_name = llm_model_name if llm_model_name else DEFAULT_LLM_MODEL_NAME

    try:
        model = GenerativeModel(current_model_name)
        vertex_content_list = _convert_lc_messages_to_vertex_content(conversation_history, prompt)

        if not vertex_content_list:
            logger.warning("No content to send to LLM (empty prompt and history).")
            # Consider raising InvalidInputError if prompt is essential
            return ""

        current_generation_config = generation_config_override if generation_config_override else DEFAULT_GENERATION_CONFIG
        current_safety_settings = safety_settings_override if safety_settings_override else DEFAULT_SAFETY_SETTINGS

        response = await _generate_content_with_retry(
            model,
            vertex_content_list,
            current_generation_config,
            current_safety_settings,
            tools=tools_schema
        )

        if not response.candidates:
            logger.warning(f"LLM response for model {current_model_name} had no candidates. Finish reason: {response.prompt_feedback.block_reason if response.prompt_feedback else 'Unknown'}")
            raise LLMResponseError(detail=f"LLM response was blocked or empty. Finish reason: {response.prompt_feedback.block_reason if response.prompt_feedback else 'Unknown'}")

        first_candidate = response.candidates[0]
        if first_candidate.content and first_candidate.content.parts:
            all_text_parts = []
            for part in first_candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    all_text_parts.append(part.text)

            if all_text_parts:
                return "".join(all_text_parts)
            elif any(hasattr(part, 'function_call') for part in first_candidate.content.parts):
                logger.info(f"LLM for model {current_model_name} returned function call(s) without accompanying text.")
                return "" # Or some indicator, this part will be revisited with BE-LLM-001
            else:
                logger.warning(f"LLM response candidate for model {current_model_name} had parts but no parsable text or function calls.")
                return ""

        logger.warning(f"LLM response for model {current_model_name} was empty or in an unexpected format.")
        return ""

    except google_exceptions.RetryError as e:
        logger.error(f"LLM call failed after multiple retries for model {current_model_name}: {e.last_attempt.exception()}", exc_info=True)
        raise LLMError(detail=f"LLM call failed after multiple retries: {e.last_attempt.exception()}")
    except google_exceptions.InvalidArgument as e:
        logger.error(f"LLM call failed due to InvalidArgument for model {current_model_name}: {e}", exc_info=True)
        raise InvalidInputError(detail=f"LLM request was invalid: {e}. Check model name and parameters.")
    except google_exceptions.PermissionDenied as e:
        logger.error(f"LLM call failed due to PermissionDenied for model {current_model_name}: {e}", exc_info=True)
        raise LLMConnectionError(detail=f"Permission denied for LLM service: {e}. Check service account permissions for Vertex AI.")
    except Exception as e: # Catch-all for other unexpected errors
        logger.error(f"Unexpected error in get_llm_response for model {current_model_name}: {e}", exc_info=True)
        raise LLMError(detail=f"An unexpected error occurred with the LLM service: {type(e).__name__} - {e}")
