"""OpenAI-compatible Chat Completions report provider."""

import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.config.prompts.v1_0 import PROMPT_VERSION, build_messages
from app.config.settings import Settings
from app.providers.llm.base import LlmProviderError
from app.schemas.report import ReportResult
from app.services.report import PreparedAnalysisReportInput

ChatCompletionClient = Callable[[dict[str, object], float], Mapping[str, object]]

DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAICompatibleReportProvider:
    """Generate reports through an OpenAI-compatible Chat Completions endpoint."""

    def __init__(
        self,
        *,
        settings: Settings,
        chat_completion_client: ChatCompletionClient | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._settings = settings
        self._chat_completion_client = chat_completion_client
        self._timeout_seconds = timeout_seconds

    def generate(self, report_input: PreparedAnalysisReportInput) -> ReportResult:
        """Return a validated public report result."""

        model = self._settings.llm_model.strip()
        if not model:
            raise LlmProviderError("LLM model is not configured")

        payload: dict[str, object] = {
            "model": model,
            "messages": build_messages(report_input),
            "temperature": 0.3,
            "max_tokens": 2000,
        }
        raw_response = (
            self._chat_completion_client(payload, self._timeout_seconds)
            if self._chat_completion_client is not None
            else self._send_chat_completion(payload, self._timeout_seconds)
        )
        content = _extract_chat_content(raw_response)
        try:
            return ReportResult.model_validate(
                {
                    "status": "success",
                    "text": content,
                    "provider": "openai_compatible",
                    "model": model,
                    "prompt_version": PROMPT_VERSION,
                },
            )
        except ValidationError as exc:
            raise LlmProviderError("LLM report result is invalid") from exc

    def _send_chat_completion(
        self,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> Mapping[str, object]:
        api_key = self._settings.llm_api_key.strip()
        if not api_key:
            raise LlmProviderError("LLM API key is not configured")

        base_url = (self._settings.llm_base_url.strip() or DEFAULT_BASE_URL).rstrip("/")
        url = f"{base_url}/chat/completions"
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except (TimeoutError, URLError, OSError) as exc:
            raise LlmProviderError("LLM provider request failed") from exc

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as exc:
            raise LlmProviderError("LLM provider returned invalid JSON") from exc
        if not isinstance(parsed, Mapping):
            raise LlmProviderError("LLM provider returned invalid response shape")
        return parsed


def _extract_chat_content(raw_response: Mapping[str, object]) -> str:
    choices = raw_response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LlmProviderError("LLM provider response has no choices")

    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        raise LlmProviderError("LLM provider choice has invalid shape")

    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        raise LlmProviderError("LLM provider message has invalid shape")

    content: Any = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LlmProviderError("LLM provider returned empty content")
    return content.strip()
