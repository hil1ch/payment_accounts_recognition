from services.rabbit_service import RabbitService
from core.config import settings
from services.redis_service import RedisService
from services.task_processor import TaskProcessor
from core.logging_config import logger

def main():
    try:
        logger.info("Initializing ML service...")
        
        redis = RedisService(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password
        )
        logger.info(f"Redis service initialized (host: {settings.redis_host}:{settings.redis_port})")
        
        task_processor = TaskProcessor(redis_service=redis)
        logger.info("Task processor initialized")
        
        rabbit_service = RabbitService(
            amqp_url=settings.rabbit_url,
            queue_name=settings.queue_name,
            task_processor=task_processor
        )
        logger.info(f"RabbitMQ service initialized (queue: {settings.queue_name})")
        
        logger.info("Starting RabbitMQ consumer...")
        rabbit_service.start()
    except Exception as e:
        logger.error(f"Failed to start ML service: {str(e)}")
        raise

if __name__ == "__main__":
    main()