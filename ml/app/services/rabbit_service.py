import pika
import json
from services.task_processor import TaskProcessor
from services.redis_service import RedisService

class RabbitService:
    def __init__(self, 
                 amqp_url: str,
                 queue_name: str,
                 task_processor: TaskProcessor 
                 ):
        self.amqp_url = amqp_url
        self.queue_name = queue_name
        self.task_processor = task_processor
        self.connection = pika.BlockingConnection(pika.URLParameters(self.amqp_url))
        self.channel = self.connection.channel()
        #if not created queue
        self.channel.queue_declare(queue=self.queue_name, durable=True)
    
    def start(self):
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._callback,
            auto_ack=False
        )
        self.channel.start_consuming()
    
    def _callback(self, ch, method, properties, body):
        #Тут будет обработка пока не придумал как это построить
        try:
            message = json.loads(body.decode())
            print(f"Received message: {message}")
            self.task_processor.process(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing message: {e}")
            traceback.print_exc()
            #Говрит что мы удаляем сообщение из очереди если не обработали
            #Пока не знаю как лучше, тут в идеале добавить случи при который мы оставляем, а при каких нет
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        