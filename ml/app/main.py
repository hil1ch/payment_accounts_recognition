from services.rabbit_service import RabbitService
from core.config import settings

def main():
    rabbit_service = RabbitService(
        amqp_url=settings.rabbit_url,
        queue_name=settings.queue_name
    )
    print("Starting RabbitMQ consumer...")
    rabbit_service.start()

if __name__ == "__main__":
    main()

print("Starting RabbitMQ consumer...")