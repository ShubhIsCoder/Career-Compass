from __future__ import annotations

from app import create_app
from app.config import settings


class FakeRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def ping(self) -> bool:
        return True

    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int:  # noqa: ARG002
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    def set_json(self, key: str, payload: dict, ttl_seconds: int = 3600) -> None:  # noqa: ARG002
        return None


def build_client(monkeypatch):
    settings.database_url = "sqlite+pysqlite:///:memory:"
    import app as app_module

    monkeypatch.setattr(app_module, "RedisStore", FakeRedis)
    flask_app = create_app()
    return flask_app.test_client()


def test_health_endpoint(monkeypatch) -> None:
    client = build_client(monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["db"] == "ok"


def test_auth_and_chat_session_flow(monkeypatch) -> None:
    client = build_client(monkeypatch)

    register = client.post(
        "/api/auth/register",
        json={"email": "user@example.com", "password": "strongpass123", "tier": "free"},
    )
    assert register.status_code == 201
    token = register.get_json()["access_token"]

    chat = client.post(
        "/api/chat",
        json={"message": "Help me become data analyst"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert chat.status_code == 200
    chat_payload = chat.get_json()
    assert "session_id" in chat_payload

    sessions = client.get("/api/sessions", headers={"Authorization": f"Bearer {token}"})
    assert sessions.status_code == 200
    assert len(sessions.get_json()["sessions"]) == 1


def test_chat_requires_auth(monkeypatch) -> None:
    client = build_client(monkeypatch)
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 401
