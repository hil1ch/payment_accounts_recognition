import pika
import json
from services.task_processor import TaskProcessor
from services.redis_service import RedisService
from core.logging_config import logger

class RabbitService:
    def __init__(self, 
                 amqp_url: str,
                 queue_name: str,
                 task_processor: TaskProcessor 
                 ):
        try:
            self.amqp_url = amqp_url
            self.queue_name = queue_name
            self.task_processor = task_processor
            
            logger.debug(f"Connecting to RabbitMQ: {amqp_url}")
            self.connection = pika.BlockingConnection(pika.URLParameters(self.amqp_url))
            self.channel = self.connection.channel()
            logger.info("RabbitMQ connection established")
            
            #if not created queue
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            logger.info(f"Queue declared: {self.queue_name}")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ connection: {str(e)}")
            raise
    
    def start(self):
        try:
            logger.info(f"Starting to consume messages from queue: {self.queue_name}")
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self._callback,
                auto_ack=False
            )
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            self.channel.stop_consuming()
            self.connection.close()
        except Exception as e:
            logger.error(f"Error in RabbitMQ consumer: {str(e)}")
            raise
    
    def _callback(self, ch, method, properties, body):
        try:
            message = json.loads(body.decode())
            logger.info(f"Received message from queue: job_id={message.get('job_id', 'unknown')}")
            
            self.task_processor.process(message)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug(f"Message acknowledged: job_id={message.get('job_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Удаляем сообщение из очереди если не обработали
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            logger.warning(f"Message rejected and removed from queue")
            raise e 
        