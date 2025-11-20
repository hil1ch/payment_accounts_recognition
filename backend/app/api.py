from fastapi import UploadFile
from app.schemas.client_DTOs import *
import uuid

async def parse(file: UploadFile) -> ParseResponce:
    #Mock 
    return ParseResponce(job_id = uuid.uuid1())

async def get_result(uuid: UUID) -> ResultResponce:
    #Mock 
    return ResultResponce(
        status=JobStatus.done,
        processing_time_ms=1534,
        result={"test_1": 1, "test":"test"}
    )