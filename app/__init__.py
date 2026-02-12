from __future__ import annotations

from flask import Flask, g, jsonify, render_template, request
from flask_cors import CORS
from pydantic import ValidationError
from sqlalchemy import select

from app.auth import AuthService
from app.config import settings
from app.llm import LLMService, LLMServiceError
from app.models import ChatMessage, ChatSession, Tier, User, db
from app.redis_client import RedisStore
from app.schemas import AuthResponse, ChatRequest, ChatResponse, LoginRequest, RegisterRequest

RATE_LIMITS_PER_MINUTE: dict[Tier, int] = {
    Tier.free: 10,
    Tier.pro: 60,
    Tier.enterprise: 300,
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    CORS(app)
    db.init_app(app)

    auth_service = AuthService()
    redis_store = RedisStore()

    llm_service: LLMService | None = None
    llm_error: str | None = None

    try:
        llm_service = LLMService()
    except LLMServiceError as exc:
        llm_error = str(exc)

    with app.app_context():
        db.create_all()

    def get_current_user() -> User | None:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header.replace("Bearer ", "", 1).strip()
        user_id = auth_service.parse_token(token)
        if not user_id:
            return None
        return db.session.get(User, user_id)

    def enforce_rate_limit(user: User) -> bool:
        limit = RATE_LIMITS_PER_MINUTE[user.tier]
        key = f"rate:{user.id}:{request.endpoint}"
        try:
            current = redis_store.incr_with_ttl(key, 60)
        except Exception:
            return True
        return current <= limit

    @app.before_request
    def attach_user() -> None:
        g.user = get_current_user()

    @app.get("/")
    def index() -> str:
        return render_template("index.html", llm_error=llm_error)

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        status = "ready" if llm_service else "degraded"
        db_state = "ok"
        redis_state = "ok"
        try:
            db.session.execute(select(1))
        except Exception:
            db_state = "down"
        try:
            redis_store.ping()
        except Exception:
            redis_state = "down"
        return {"status": status, "env": settings.app_env, "db": db_state, "redis": redis_state}, 200

    @app.post("/api/auth/register")
    def register() -> tuple[dict, int]:
        try:
            payload = RegisterRequest.model_validate(request.get_json(force=True))
        except ValidationError as exc:
            return jsonify({"error": "Invalid payload", "details": exc.errors()}), 400

        exists = db.session.scalar(select(User).where(User.email == payload.email.lower()))
        if exists:
            return jsonify({"error": "Email already exists"}), 409

        user = User(
            email=payload.email.lower(),
            password_hash=auth_service.hash_password(payload.password),
            tier=Tier(payload.tier),
        )
        db.session.add(user)
        db.session.commit()

        token = auth_service.issue_token(user.id)
        return AuthResponse(access_token=token, user_id=user.id, tier=user.tier.value).model_dump(), 201

    @app.post("/api/auth/login")
    def login() -> tuple[dict, int]:
        try:
            payload = LoginRequest.model_validate(request.get_json(force=True))
        except ValidationError as exc:
            return jsonify({"error": "Invalid payload", "details": exc.errors()}), 400

        user = db.session.scalar(select(User).where(User.email == payload.email.lower()))
        if not user or not auth_service.verify_password(user.password_hash, payload.password):
            return jsonify({"error": "Invalid credentials"}), 401

        token = auth_service.issue_token(user.id)
        return AuthResponse(access_token=token, user_id=user.id, tier=user.tier.value).model_dump(), 200

    @app.get("/api/sessions")
    def list_sessions() -> tuple[dict, int]:
        if not g.user:
            return jsonify({"error": "Unauthorized"}), 401

        sessions = db.session.scalars(
            select(ChatSession).where(ChatSession.user_id == g.user.id).order_by(ChatSession.updated_at.desc())
        ).all()
        data = [
            {"id": s.id, "title": s.title, "created_at": s.created_at.isoformat(), "updated_at": s.updated_at.isoformat()}
            for s in sessions
        ]
        return {"sessions": data}, 200

    @app.post("/api/chat")
    def chat() -> tuple[dict, int]:
        if not g.user:
            return jsonify({"error": "Unauthorized"}), 401

        if not enforce_rate_limit(g.user):
            return jsonify({"error": "Rate limit exceeded for your subscription tier"}), 429

        try:
            payload = ChatRequest.model_validate(request.get_json(force=True))
        except ValidationError as exc:
            return jsonify({"error": "Invalid payload", "details": exc.errors()}), 400

        chat_session = None
        if payload.session_id:
            chat_session = db.session.get(ChatSession, payload.session_id)
            if not chat_session or chat_session.user_id != g.user.id:
                return jsonify({"error": "Session not found"}), 404
        else:
            chat_session = ChatSession(user_id=g.user.id)
            db.session.add(chat_session)
            db.session.flush()

        prior_messages = db.session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat_session.id)
            .order_by(ChatMessage.created_at.asc())
        ).all()

        history = []
        pair: dict[str, str] = {}
        for msg in prior_messages:
            if msg.role == "user":
                pair["user"] = msg.content
            elif msg.role == "assistant":
                pair["assistant"] = msg.content
                history.append(pair)
                pair = {}

        db.session.add(ChatMessage(session_id=chat_session.id, role="user", content=payload.message))

        if llm_service is None:
            reply = (
                "I can help you plan your career roadmap, but model credentials are not configured yet. "
                "Set OPENAI_API_KEY or GEMINI_API_KEY and try again."
            )
            provider = "fallback"
            model = "none"
        else:
            reply = llm_service.generate_reply(payload.message, history)
            provider = llm_service.provider
            model = llm_service.model

        db.session.add(ChatMessage(session_id=chat_session.id, role="assistant", content=reply))
        db.session.commit()

        try:
            redis_store.set_json(
                f"session:last:{g.user.id}",
                {"session_id": chat_session.id, "preview": reply[:140], "tier": g.user.tier.value},
                ttl_seconds=3600,
            )
        except Exception:
            pass

        return ChatResponse(reply=reply, provider=provider, model=model, session_id=chat_session.id).model_dump(), 200

    return app
