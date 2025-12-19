import time
from services.rabbitmq import RabbitConsumer
from services.redis import RedisClient
from services.ml import process_file

def worker():
    rabbit = RabbitConsumer()
    redis = RedisClient()
    
    
    while True:
        try:
            # Ждем сообщение
            message = rabbit.get_message()
            if not message:
                time.sleep(0.1)  # Не грузить CPU при простое
                continue
            
            job_id = message['job_id']
            file_path = message['file_path']
            
            print(f"Processing job {job_id}")
            
            # Проверяем и захватываем задачу
            if redis.set_if_not_exists(f"lock:{job_id}", "processing", ttl=300):
                try:
                    # Обработка ML
                    result = process_file(file_path)
                    
                    # Сохраняем результат
                    redis.set(f"result:{job_id}", result)
                    redis.set(f"status:{job_id}", "completed")
                    
                    # Подтверждаем
                    rabbit.ack(message)
                    print(f"Job {job_id} completed")
                    
                except Exception as e:
                    redis.set(f"status:{job_id}", f"failed: {str(e)}")
                    rabbit.nack(message)
                    print(f"Job {job_id} failed: {e}")
                    
                finally:
                    redis.delete(f"lock:{job_id}")
            else:
                print(f"Job {job_id} is already being processed")
                rabbit.nack(message, requeue=False)

if __name__ == "__main__":
    worker()