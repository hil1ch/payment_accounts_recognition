import json
import aio_pika
from backend.app.schemas.queue_message import QueueMessage
from app.core.config import settings
from app.core.rabbit_connection import rabbit_conn

async def publish_event(message: QueueMessage):
    # payload — Python dict (например, {'order_id': 123, 'action': 'created'})
    message_body = message.model_dump_json.encode() # AMQP передаёт байты

    message = aio_pika.Message(body=message_body, content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT)

    # используем заранее объявленный exchange
    await rabbit_conn.exchange.publish(message, routing_key=settings.routing_key)
