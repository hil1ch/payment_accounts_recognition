import aio_pika
from app.core.config import settings
from app.core.logging_config import logger

class RabbitConnection:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def init(self):
        try:
            # 1) Создаём надёжное соединение
            logger.debug(f"Connecting to RabbitMQ at {settings.rabbit_url}")
            self.connection = await aio_pika.connect_robust(settings.rabbit_url)
            logger.info("Connected to RabbitMQ")

            # 2) Создаём канал — через канал проходят publish/consume операции
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)  # сколько сообщений consumer возьмёт одновременно
            logger.debug("Channel created, QoS set to 10")

            # 3) Объявляем exchange и очередь (если их нет — создадутся)
            self.exchange = await self.channel.declare_exchange(settings.exchange_name, aio_pika.ExchangeType.DIRECT)
            logger.debug(f"Exchange declared: {settings.exchange_name}")
            
            queue = await self.channel.declare_queue(settings.queue_name, durable=True)
            await queue.bind(self.exchange, routing_key=settings.routing_key)
            logger.info(f"Queue {settings.queue_name} declared and bound to exchange with routing_key {settings.routing_key}")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ connection: {str(e)}")
            raise

    async def close(self):
        try:
            logger.debug("Closing RabbitMQ connection")
            await self.connection.close()
            logger.info("RabbitMQ connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")
            raise

# создаём глобальный объект, который будем импортировать
rabbit_conn = RabbitConnection()