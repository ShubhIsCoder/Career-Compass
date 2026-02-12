from app import create_app


def test_health_endpoint() -> None:
    app = create_app()
    client = app.test_client()

    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] in {"ready", "degraded"}


def test_chat_fallback_without_keys() -> None:
    app = create_app()
    client = app.test_client()

    response = client.post("/api/chat", json={"message": "Help me pick a career", "history": []})
    assert response.status_code == 200
    payload = response.get_json()
    assert "reply" in payload
    assert "provider" in payload
