"""M0 第一个测试:验证 /health 返回 200 且响应体格式正确。"""
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    """GET /health 应该返回 200 + 正确字段。"""
    response = client.get("/health")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "rag-assistant"
    assert body["env"] in ("dev", "staging", "prod")
    assert "version" in body


def test_root_returns_metadata() -> None:
    """GET / 应该返回服务元信息。"""
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "rag-assistant"
    assert "version" in body
