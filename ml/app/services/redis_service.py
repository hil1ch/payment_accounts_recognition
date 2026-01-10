import redis
from schemas.redis_message import JobStatus, RedisMessage
from core.config import settings
from core.logging_config import logger


class RedisService:
    def __init__(self , host: str, port: int, password: str):
        try:
            self.host = host
            self.port = port
            self.password = password
            
            logger.debug(f"Connecting to Redis at {host}:{port}")
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                decode_responses=True
            )
            # Проверяем подключение
            self.client.ping()
            logger.info(f"Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    #Changing the value extends the expire time
    def change_status(self, job_id:str, status: JobStatus):
        try:
            value = self.client.get(job_id)
            if value is None:
                logger.warning(f"Job not found in Redis: {job_id}")
                raise ValueError(f"Job {job_id} not found")
            
            message = RedisMessage.model_validate_json(value)
            message.status = status
            self.client.set(job_id, message.model_dump_json(), ex=settings.redis_expire_seconds)
            logger.info(f"Status changed to {status.value} for job_id: {job_id}")
        except Exception as e:
            logger.error(f"Failed to change status for job_id {job_id}: {str(e)}")
            raise

    def save_result(self, job_id: str, result: dict):
        try:
            value = self.client.get(job_id)
            if value is None:
                logger.warning(f"Job not found in Redis: {job_id}")
                raise ValueError(f"Job {job_id} not found")
            
            message = RedisMessage.model_validate_json(value)
            message.result = result
            message.status = JobStatus.done
            self.client.set(job_id, message.model_dump_json(), ex=settings.redis_expire_seconds)
            logger.info(f"Result saved for job_id: {job_id}")
        except Exception as e:
            logger.error(f"Failed to save result for job_id {job_id}: {str(e)}")
            raise
