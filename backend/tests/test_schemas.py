from app.schemas.client_DTOs import ParseResponce, ResultResponce, JobStatus
from app.schemas.queue_message import QueueMessage
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import json


def test_parse_response_schema():
    job_id = uuid4()
    obj = ParseResponce(job_id=job_id)
    assert obj.job_id == job_id


def test_result_response_schema():
    # Используем JSON-строку вместо словаря
    result_json = json.dumps({"ok": True})

    obj = ResultResponce(
        status=JobStatus.done,
        processing_time_ms=100,
        result=result_json  # JSON-строка
    )
    assert obj.status == JobStatus.done
    assert obj.processing_time_ms == 100
    # Pydantic автоматически парсит JSON в dict
    assert obj.result == {"ok": True}


def test_queue_message_schema(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("hello")

    msg = QueueMessage(
        job_id=uuid4(),
        file_path=file,
        creation_time=datetime.now()
    )

    assert Path(msg.file_path).exists()