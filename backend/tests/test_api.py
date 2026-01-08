import pytest
from uuid import uuid4
from io import BytesIO
from fastapi import UploadFile, Request
from datetime import datetime
from app.api import parse, get_result
from app.schemas.redis_message import RedisMessage
from app.schemas.client_DTOs import JobStatus


@pytest.mark.asyncio
async def test_parse_function(monkeypatch):
    async def fake_publish(msg):
        return True

    def fake_save(file, path, job_id):
        return "/tmp/test.pdf"

    async def fake_save_redis(redis, job_id, msg):
        return True

    monkeypatch.setattr(
        "app.api.publisher.publish", fake_publish
    )
    monkeypatch.setattr(
        "app.api.save_uploaded_file", fake_save
    )
    monkeypatch.setattr(
        "app.api.save_message_to_redis", fake_save_redis
    )

    request = Request({
        "type": "http",
        "app": type("app", (), {
            "state": type("state", (), {"redis": object()})()
        })()
    })

    file = UploadFile(
        filename="test.pdf",
        file=BytesIO(b"123")
    )

    response = await parse(request, file)

    assert "job_id" in response


@pytest.mark.asyncio
async def test_get_result_function(monkeypatch):
    job_id = uuid4()

    async def fake_get(redis, job_id):
        return RedisMessage(
            status=JobStatus.done,
            file_path=None,
            creadtion_time=datetime.now(),
            result={"account": "123456"}
        )

    async def fake_delete(redis, job_id):
        return True

    def fake_delete_file(path):
        return True

    monkeypatch.setattr(
        "app.api.get_message_from_redis", fake_get
    )
    monkeypatch.setattr(
        "app.api.delete_message_from_redis", fake_delete
    )
    monkeypatch.setattr(
        "app.api.delite_file", fake_delete_file
    )

    request = Request({
        "type": "http",
        "app": type("app", (), {
            "state": type("state", (), {"redis": object()})()
        })()
    })

    response = await get_result(request, job_id)

    assert response["status"] == JobStatus.done
    assert response["result"]["account"] == "123456"