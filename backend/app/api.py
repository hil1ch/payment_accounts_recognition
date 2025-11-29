import json
from fastapi import UploadFile
from app.schemas.client_DTOs import *
from app.schemas.queue_message import QueueMessage
from app.services.rabbit_publisher import publisher
import uuid
from datetime import datetime
from app.core.config import settings
from app.services.file_service import save_uploaded_file

async def parse(file: UploadFile) -> ParseResponce:
    curr_job_id = uuid.uuid4()
    file_path = save_uploaded_file(file, settings.shared_dir, curr_job_id)
    message = QueueMessage(
        job_id=curr_job_id,
        file_path=file_path,
        creation_time=datetime(2025, 11, 21, 15, 30)
        )
    await publisher.publish(message)
    
    return ParseResponce(job_id = curr_job_id)

async def get_result(job_id: UUID) -> ResultResponce:
    #Mock 
    return ResultResponce(
        status=JobStatus.done,
        processing_time_ms=1534,
        result=json.dumps({"test_1": 1, "test":"test"})
    )