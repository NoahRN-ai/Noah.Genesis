# LLM Abstraction Service (`llm_service.py`)

This document describes the LLM (Large Language Model) Abstraction Service for Project Noah MVP. This service provides a standardized interface for interacting with various generative AI models hosted on Google Cloud Vertex AI.

## 1. Overview

The `llm_service.py` module offers a core function, `get_llm_response`, designed to:
*   Send prompts and conversational history to a specified LLM on Vertex AI.
*   Handle model switching based on a provided model name.
*   Incorporate error handling and automatic retries for LLM API calls.
*   Operate securely using Application Default Credentials (ADC) via the assigned service account when deployed on GCP (e.g., Cloud Run).
*   Provide a foundational layer for more complex agentic logic (e.g., to be used by LangGraph).

## 2. Core Function

### `async def get_llm_response(...)`

*   **Signature:**
    ```python
    async def get_llm_response(
        prompt: str,
        conversation_history: Optional[List[BaseMessage]] = None,
        llm_model_name: str = "gemini-1.0-pro-001",
        generation_config_override: Optional[GenerationConfig] = None,
        safety_settings_override: Optional[Dict[HarmCategory, HarmBlockThreshold]] = None,
        tools_schema: Optional[List[vertexai.generative_models.Tool]] = None
    ) -> str:
    ```
*   **Parameters:**
    *   `prompt: str`: The current textual prompt or query for the LLM.
    *   `conversation_history: Optional[List[BaseMessage]]`: A list of `langchain_core.messages.BaseMessage` objects (e.g., `HumanMessage`, `AIMessage`, `ToolMessage`) representing the prior turns of the conversation. This is converted internally to Vertex AI's `Content` object format.
    *   `llm_model_name: str`: The identifier for the Vertex AI model to be used.
        *   Examples: `"gemini-1.0-pro-001"`, `"gemini-1.5-flash-preview-0514"`, `"gemini-1.5-pro-preview-0514"`.
        *   For MedGemma or other specific/fine-tuned models, this would be the model's full resource name or registered endpoint ID on Vertex AI if consumable by the `GenerativeModel` class. E.g., `projects/YOUR_PROJECT_ID/locations/YOUR_REGION/endpoints/YOUR_ENDPOINT_ID` or a published model ID.
    *   `generation_config_override: Optional[GenerationConfig]`: Allows overriding default generation parameters like `temperature`, `top_p`, `max_output_tokens`. (See `vertexai.generative_models.GenerationConfig`).
    *   `safety_settings_override: Optional[Dict[HarmCategory, HarmBlockThreshold]]`: Allows overriding default content safety settings.
    *   `tools_schema: Optional[List[vertexai.generative_models.Tool]]`: Allows passing tool/function declarations to the LLM. This is primarily for use by higher-level orchestrators like LangGraph which will construct these schemas.
*   **Returns:** `str`: The LLM's textual response. In case of errors or if the LLM response is blocked/empty, it may return an empty string or an error message string. If the LLM returns a function call without accompanying text, this function currently returns an empty string; the calling layer (LangGraph) is expected to parse the full LLM candidate object for tool calls.
*   **Purpose:** To provide a single, resilient entry point for getting text-based completions from various LLMs, abstracting away the direct Vertex AI SDK calls for message formatting, retries, and basic error handling.

## 3. Model Switching

The `llm_model_name` parameter directly controls which Vertex AI model is invoked. The service uses `vertexai.generative_models.GenerativeModel(llm_model_name)` to instantiate the model client. This supports using various Google foundational models (like Gemini versions) by their short names or fully qualified model/endpoint IDs for other compatible models (e.g., MedGemma if available via this SDK class).

## 4. Error Handling and Retry Strategy (`dynamous.ai` Resilience)

*   **Automatic Retries:** The service employs the `tenacity` library to automatically retry LLM API calls upon encountering specific transient Google API core exceptions (`Aborted`, `DeadlineExceeded`, `InternalServerError`, `ResourceExhausted`, `ServiceUnavailable`, `Unknown`).
    *   Retries use a random exponential backoff strategy (waits `1s * 2^attempt_number`, up to 60s between retries).
    *   A maximum of 5 attempts are made per call.
*   **Specific Exception Handling:**
    *   `google.api_core.exceptions.RetryError`: If all retries fail.
    *   `google.api_core.exceptions.InvalidArgument`: For issues like incorrect model names or malformed requests.
    *   `google.api_core.exceptions.PermissionDenied`: For authentication/authorization issues.
    *   A general `Exception` catch-all logs and returns a generic error message for unexpected issues.
*   **Blocked/Empty Responses:** The service checks if the LLM response was blocked due to safety settings or if no content/candidates were returned, providing an appropriate message.

## 5. Authentication

*   The service relies on **Application Default Credentials (ADC)**.
*   When deployed on Google Cloud services like Cloud Run, the attached service account (e.g., `sa-cloudrun-agent`) must have the necessary IAM permissions to access Vertex AI (typically `roles/aiplatform.user`).
*   No explicit API keys or credential files are managed within this service module.

## 6. Vertex AI Initialization

*   `vertexai.init(project=GCP_PROJECT_ID, location=VERTEX_AI_REGION)` is called once at the module level when `llm_service.py` is first imported.
*   `GCP_PROJECT_ID` and `VERTEX_AI_REGION` are fetched from environment variables. It's crucial these are correctly set in the runtime environment.

## 7. Token Usage Tracking & Cost Analysis (`dynamous.ai` Foresight)

*   The Vertex AI SDK's response object (from `generate_content_async`) often includes a `usage_metadata` attribute containing token counts (`prompt_token_count`, `candidates_token_count`, `total_token_count`).
*   The `get_llm_response` function includes commented-out placeholders showing how this information *could* be accessed.
*   For MVP, full logging or database storage of token counts per call is not implemented by this service. However, this information is vital for:
    *   **Cost Monitoring:** Understanding and managing LLM API expenses.
    *   **Rate Limiting/Quota Management:** Tracking usage against quotas.
    *   **Performance Analysis:** Correlating token counts with latency.
*   Future enhancements could involve integrating this token tracking with Cloud Monitoring as custom metrics or logging it for detailed analysis.

## 8. Interfacing with LangGraph & Tool Usage

*   This `llm_service.py` provides the fundamental LLM interaction capability.
*   LangGraph (to be implemented in Phase 3) will be the primary consumer of this service. LangGraph will be responsible for:
    *   Formatting prompts that may include descriptions of available tools/functions.
    *   Passing the appropriate `tools_schema` to `get_llm_response` if it intends for the LLM to select and use tools.
    *   Parsing the full LLM response: If the LLM returns a `function_call` (tool invocation request), LangGraph will extract this information from the `response.candidates[0].content.parts` and orchestrate the tool execution. This `llm_service` currently focuses on extracting simple text, so LangGraph will need to work with the richer response object before it's reduced to just text if tools are involved. Forcing this service to *only* return text when tools are used can be limiting, so the design may evolve to return a more structured object if LangGraph needs more than just the text part from the LLM in a single pass.
