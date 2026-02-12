from __future__ import annotations

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pydantic import ValidationError

from app.config import settings
from app.llm import LLMService, LLMServiceError
from app.schemas import ChatRequest, ChatResponse


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    CORS(app)

    llm_service: LLMService | None = None
    llm_error: str | None = None

    try:
        llm_service = LLMService()
    except LLMServiceError as exc:
        llm_error = str(exc)

    @app.get("/")
    def index() -> str:
        return render_template("index.html", llm_error=llm_error)

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        status = "ready" if llm_service else "degraded"
        return {"status": status, "env": settings.app_env}, 200

    @app.post("/api/chat")
    def chat() -> tuple[dict[str, str], int]:
        try:
            payload = ChatRequest.model_validate(request.get_json(force=True))
        except ValidationError as exc:
            return jsonify({"error": "Invalid payload", "details": exc.errors()}), 400

        if llm_service is None:
            fallback = (
                "I can help you plan your career roadmap, but model credentials are not configured yet. "
                "Set OPENAI_API_KEY or GEMINI_API_KEY and try again."
            )
            response = ChatResponse(reply=fallback, provider="fallback", model="none")
            return response.model_dump(), 200

        reply = llm_service.generate_reply(payload.message, payload.history)
        response = ChatResponse(reply=reply, provider=llm_service.provider, model=llm_service.model)
        return response.model_dump(), 200

    return app
