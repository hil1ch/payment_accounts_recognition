import aio_pika
from app.schemas.queue_message import QueueMessage
from app.core.config import settings
from app.core.rabbit_connection import RabbitConnection, rabbit_conn

class RabbitPublisher:
    def __init__(self, conn: RabbitConnection):
        self.conn = conn

    async def publish(self, message: QueueMessage):
        body = message.model_dump_json().encode()
        msg = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await self.conn.exchange.publish(
            msg,
            routing_key=settings.routing_key
        )

publisher = RabbitPublisher(rabbit_conn)  