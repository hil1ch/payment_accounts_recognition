from pydantic import Json
from services.redis_service import RedisService
from schemas.redis_message import JobStatus
from services.model import process_document
from schemas.rabbit_message import RabbitMessage


class TaskProcessor:
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service

    def process(self, message: Json):
        parsed_message = RabbitMessage.model_validate(message)
        job_id = parsed_message.job_id
        file_path = parsed_message.file_path
        self.redis_service.change_status(str(job_id), JobStatus.in_progress)
        result = process_document(file_path)
        self.redis_service.save_result(str(job_id), result)
        print(f"Processed job {job_id} with result: {result}")
