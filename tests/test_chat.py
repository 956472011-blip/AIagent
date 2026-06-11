"""M1 测试:chat 端点。

策略:
- 测输入校验(不调 LLM,纯 Pydantic 验证)
- 真流式调用放在手动 curl 阶段(避免 pytest 依赖网络/额度)
"""
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_empty_body_rejected() -> None:
    """缺 query 字段应该被 Pydantic 拦下,返 422。"""
    response = client.post("/chat", json={})

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


def test_chat_empty_query_rejected() -> None:
    """query 是空字符串也应该被拦下(min_length=1)。"""
    response = client.post("/chat", json={"query": ""})

    assert response.status_code == 422


def test_chat_stream_endpoint_accepts_valid_request() -> None:
    """/chat/stream 应该接受合法请求(本测试用 monkeypatch 短路 LLM 调用)。"""
    from app.api import chat as chat_module

    async def fake_retrieve_context(_query):
        return "资料片段", [{"index": 1, "source": "demo.md", "chunk_id": 0}]

    async def fake_astream(_input):
        for word in ["你", "好", "!", "\n", "世界"]:
            yield word

    class FakeChain:
        astream = staticmethod(fake_astream)  # type: ignore[assignment]

    # 整体替换 _chain 变量(不能用属性赋值,RuannableSequence 是 frozen pydantic model)
    original_chain = chat_module._chain
    original_retrieve_context = chat_module._retrieve_context
    chat_module._chain = FakeChain()  # type: ignore[assignment]
    chat_module._retrieve_context = fake_retrieve_context  # type: ignore[assignment]
    try:
        with client.stream("POST", "/chat/stream", json={"query": "hi"}) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            body = "".join(response.iter_text())
    finally:
        chat_module._chain = original_chain
        chat_module._retrieve_context = original_retrieve_context

    # SSE 格式: data: <chunk>\\n\\n
    assert "data: 你" in body
    assert "data: 好" in body
    assert "event: citations" in body
    assert '"source": "demo.md"' in body
    assert "data: [DONE]" in body
