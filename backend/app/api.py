import os
from fastapi import UploadFile
from app.schemas.client_DTOs import *
from app.schemas.queue_message import QueueMessage
from app.services.rabbit_publisher import publisher
import uuid
from datetime import datetime

async def parse(file: UploadFile) -> ParseResponce:
    curr_job_id = uuid.uuid4()
    message = QueueMessage(
        job_id=curr_job_id,
        file_path=os.path.abspath(__file__), #Mock
        creation_time=datetime(2025, 11, 21, 15, 30)
        )
    await publisher.publish(message)
    return ParseResponce(job_id = curr_job_id)

async def get_result(uuid: UUID) -> ResultResponce:
    #Mock 
    return ResultResponce(
        status=JobStatus.done,
        processing_time_ms=1534,
        result={"test_1": 1, "test":"test"}
    )