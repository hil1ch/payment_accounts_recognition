import pytest
from fastapi.testclient import TestClient
from app.main import app
from uuid import UUID
import json

client = TestClient(app)

def test_parse_endpoint(monkeypatch):
    async def fake_publish_event(message):
        return True

    monkeypatch.setattr("app.api.publish_event", fake_publish_event)

    response = client.post("/parse", files={"file": ("test.txt", b"abc")})
    assert response.status_code == 200


def test_result_endpoint(monkeypatch):
    # Мок get_result чтобы возвращал JSON-строку
    async def fake_get_result(job_id):
        from app.schemas.client_DTOs import ResultResponce, JobStatus
        return ResultResponce(
            status=JobStatus.done,
            processing_time_ms=1534,
            result=json.dumps({"test_1": 1, "test": "test"})  # JSON-строка
        )

    monkeypatch.setattr("app.api.get_result", fake_get_result)

    response = client.get("/result/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "done"
    assert data["result"] is not None
    assert data["result"] == {"test_1": 1, "test": "test"}