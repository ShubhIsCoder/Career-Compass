from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.config import settings
from app.prompting import SYSTEM_PROMPT


class LLMServiceError(RuntimeError):
    pass


class LLMService:
    def __init__(self) -> None:
        self.provider = settings.llm_provider.lower()
        self.model = ""
        self._llm = self._create_client()

    def _create_client(self) -> Any:
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise LLMServiceError("OPENAI_API_KEY is missing.")
            from langchain_openai import ChatOpenAI

            self.model = settings.openai_model
            return ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                timeout=settings.request_timeout,
                temperature=0.3,
            )

        if self.provider == "gemini":
            if not settings.gemini_api_key:
                raise LLMServiceError("GEMINI_API_KEY is missing.")
            from langchain_google_genai import ChatGoogleGenerativeAI

            self.model = settings.gemini_model
            return ChatGoogleGenerativeAI(
                google_api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                temperature=0.3,
            )

        raise LLMServiceError("Unsupported LLM_PROVIDER. Use 'openai' or 'gemini'.")

    def generate_reply(self, message: str, history: list[dict[str, str]]) -> str:
        messages: list[Any] = [SystemMessage(content=SYSTEM_PROMPT)]
        for turn in history[-10:]:
            user_msg = turn.get("user")
            assistant_msg = turn.get("assistant")
            if user_msg:
                messages.append(HumanMessage(content=user_msg))
            if assistant_msg:
                messages.append(AIMessage(content=assistant_msg))
        messages.append(HumanMessage(content=message))

        response = self._llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            return "\n".join(str(item) for item in content)
        return str(content)
