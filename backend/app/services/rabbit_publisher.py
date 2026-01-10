import aio_pika
from app.schemas.queue_message import QueueMessage
from app.core.config import settings
from app.core.rabbit_connection import RabbitConnection, rabbit_conn
from app.core.logging_config import logger

class RabbitPublisher:
    def __init__(self, conn: RabbitConnection):
        self.conn = conn

    async def publish(self, message: QueueMessage):
        try:
            logger.debug(f"Publishing message to queue, job_id: {message.job_id}")
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
            logger.info(f"Message published successfully, job_id: {message.job_id}, routing_key: {settings.routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish message for job_id {message.job_id}: {str(e)}")
            raise

publisher = RabbitPublisher(rabbit_conn)  