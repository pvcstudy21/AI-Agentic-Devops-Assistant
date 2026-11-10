from fastapi.testclient import TestClient

from devops_agent import api


class FakeAgent:
    def invoke(self, *_args, **_kwargs):
        return {"messages": [FakeAIMessage("Test response from fake agent.")]}


class FakeAIMessage:
    type = "ai"

    def __init__(self, content):
        self.content = content


def test_health_endpoint():
    client = TestClient(api.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_uses_thread_id(monkeypatch):
    client = TestClient(api.app)
    monkeypatch.setattr(api, "get_agent", lambda: FakeAgent())

    response = client.post(
        "/chat",
        json={"message": "hello", "thread_id": "test-thread"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Test response from fake agent.",
        "thread_id": "test-thread",
    }


def test_chat_rejects_empty_message():
    client = TestClient(api.app)
    response = client.post("/chat", json={"message": "", "thread_id": "x"})
    assert response.status_code == 422
