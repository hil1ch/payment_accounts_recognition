import pytest
from app.api import parse, get_result
from app.schemas.client_DTOs import JobStatus, ParseResponce, ResultResponce
from fastapi import UploadFile
from io import BytesIO
from uuid import uuid4
import json


@pytest.mark.asyncio
async def test_parse_function(monkeypatch):
    # мок publish_event, чтобы не дергать Rabbit
    async def fake_publish_event(msg):
        return True

    monkeypatch.setattr("app.services.rabbit_publisher.publisher.publish", fake_publish_event)

    file = UploadFile(filename="test.pdf", file=BytesIO(b"data"))
    result = await parse(file)

    assert isinstance(result, ParseResponce)
    assert result.job_id is not None


@pytest.mark.asyncio
async def test_get_result_function(monkeypatch):
    # Мок get_result чтобы возвращал JSON-строку
    async def fake_get_result(job_id):
        return ResultResponce(
            status=JobStatus.done,
            processing_time_ms=1534,
            result=json.dumps({"test_1": 1, "test": "test"})
        )

    monkeypatch.setattr("app.api.get_result", fake_get_result)

    job_id = uuid4()
    result = await get_result(job_id)

    assert isinstance(result, ResultResponce)
    assert result.status == JobStatus.done
    assert result.result is not None
    assert result.result == {"test_1": 1, "test": "test"}