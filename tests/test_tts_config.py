"""Tests for runtime TTS configuration."""

from fastapi.testclient import TestClient

from backend.main import app


def test_tts_config_can_be_updated_and_restored():
    client = TestClient(app)
    original = client.get("/tts-config").json()

    try:
        res = client.post(
            "/tts-config",
            json={
                "base_url": "https://example.ngrok-free.dev/",
                "timeout_seconds": 600,
            },
        )
        assert res.status_code == 200
        assert res.json() == {
            "base_url": "https://example.ngrok-free.dev",
            "timeout_seconds": 600.0,
        }

        current = client.get("/tts-config")
        assert current.status_code == 200
        assert current.json()["base_url"] == "https://example.ngrok-free.dev"
    finally:
        client.post("/tts-config", json=original)


def test_tts_config_rejects_empty_url():
    client = TestClient(app)

    res = client.post(
        "/tts-config",
        json={"base_url": "   ", "timeout_seconds": 600},
    )

    assert res.status_code == 400
    assert res.json()["detail"] == "TTS base URL cannot be empty."
