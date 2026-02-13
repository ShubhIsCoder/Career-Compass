from __future__ import annotations

from app import create_app


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


def build_client():
    flask_app = create_app(
        test_config={"SQLALCHEMY_DATABASE_URI": "sqlite+pysqlite:///:memory:"},
        redis_store_cls=FakeRedis,
    )
    return flask_app.test_client()


def register(client, email="user@example.com", tier="free"):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": "strongpass123", "tier": tier},
    )


def test_health_endpoint() -> None:
    client = build_client()
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["db"] == "ok"


def test_auth_and_chat_session_flow() -> None:
    client = build_client()

    register_resp = register(client)
    assert register_resp.status_code == 201
    token = register_resp.get_json()["access_token"]

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


def test_chat_requires_auth() -> None:
    client = build_client()
    response = client.post("/api/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_free_tier_rate_limit() -> None:
    client = build_client()
    register_resp = register(client)
    token = register_resp.get_json()["access_token"]

    for _ in range(10):
        ok = client.post(
            "/api/chat",
            json={"message": "Plan my transition"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ok.status_code == 200

    limited = client.post(
        "/api/chat",
        json={"message": "One more"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert limited.status_code == 429
