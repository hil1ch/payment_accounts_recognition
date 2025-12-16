import aio_pika
from app.core.config import settings

class RabbitConnection:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None

    async def init(self):
        # 1) Создаём надёжное соединение
        self.connection = await aio_pika.connect_robust(settings.rabbit_url)

        # 2) Создаём канал — через канал проходят publish/consume операции
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=10)  # сколько сообщений consumer возьмёт одновременно

        # 3) Объявляем exchange и очередь (если их нет — создадутся)
        self.exchange = await self.channel.declare_exchange(settings.exchange_name, aio_pika.ExchangeType.DIRECT)
        queue = await self.channel.declare_queue(settings.queue_name, durable=True)
        await queue.bind(self.exchange, routing_key=settings.routing_key)

    async def close(self):
        await self.connection.close()

# создаём глобальный объект, который будем импортировать
rabbit_conn = RabbitConnection()