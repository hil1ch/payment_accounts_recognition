from services.rabbit_service import RabbitService
from core.config import settings
from services.redis_service import RedisService
from services.task_processor import TaskProcessor

def main():
    redis = RedisService(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password
    )
    task_processor = TaskProcessor(redis_service=redis)
    rabbit_service = RabbitService(
        amqp_url=settings.rabbit_url,
        queue_name=settings.queue_name,
        task_processor=task_processor
    )
    print("Starting RabbitMQ consumer...")
    rabbit_service.start()

if __name__ == "__main__":
    main()

print("Starting RabbitMQ consumer...")