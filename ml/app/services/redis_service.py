import redis
from schemas.redis_message import JobStatus, RedisMessage
import time


class RedisService:
    def __init__(self , host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            decode_responses=True
        )

    def change_status(self, job_id:str, status: JobStatus):
        value = self.client.get(job_id) 
        message = RedisMessage.model_validate_json(value)
        message.status = status
        self.client.set(job_id, message.model_dump_json())

    def save_result(self, job_id: str, result: dict):
        value = self.client.get(job_id) 
        message = RedisMessage.model_validate_json(value)
        message.result = result
        message.status = JobStatus.done
        self.client.set(job_id, message.model_dump_json())
