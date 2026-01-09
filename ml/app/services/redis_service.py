import redis
from schemas.redis_message import JobStatus, RedisMessage
from core.config import settings


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
    #Changing the value extends the expire time
    def change_status(self, job_id:str, status: JobStatus):
        value = self.client.get(job_id) 
        print(value)
        message = RedisMessage.model_validate_json(value)
        message.status = status
        self.client.set(job_id, message.model_dump_json(), ex=settings.redis_expire_seconds)

    def save_result(self, job_id: str, result: dict):
        value = self.client.get(job_id) 
        message = RedisMessage.model_validate_json(value)
        message.result = result
        message.status = JobStatus.done
        self.client.set(job_id, message.model_dump_json(), ex=settings.redis_expire_seconds)
