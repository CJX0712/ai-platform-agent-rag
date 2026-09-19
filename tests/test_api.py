"""Gateway 集成 / e2e 测试。"""

import pytest
from fastapi.testclient import TestClient

from ai_platform.config import get_settings
from ai_platform.gateway.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_CHROMA_PATH", str(tmp_path))
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite:///" + str(tmp_path / "a.db"))
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_and_ingest(client):
    h = client.post("/v1/ingest", json={"text": "深度学习依赖反向传播优化参数。", "title": "dl"})
    assert h.status_code == 200
    assert h.json()["chunks"] >= 1
    r = client.post("/v1/chat", json={"message": "反向传播是什么？"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] and body["conv_id"]


def test_tools_endpoint(client):
    r = client.get("/v1/tools")
    assert r.status_code == 200
    assert any(t["name"] == "calculator" for t in r.json())


def test_auth_enabled_requires_token(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_AUTH_ENABLED", "true")
    monkeypatch.setenv("APP_CHROMA_PATH", str(tmp_path))
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite:///" + str(tmp_path / "b.db"))
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        assert c.get("/v1/tools").status_code == 401
        r = c.post("/v1/auth/token", json={"username": "demo", "password": "demo1234"})
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        ok = c.get("/v1/tools", headers={"Authorization": f"Bearer {token}"})
        assert ok.status_code == 200


def test_websocket(client):
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"message": "你好"})
        data = ws.receive_json()
        assert "answer" in data
