from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import create_app


def test_tts_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("MCP_ELEVENLABS_API_KEY", raising=False)
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post("/tts/elevenlabs", json={"text": "hello"})
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()
