def worker():
    rabbit = RabbitConsumer()
    redis = RedisClient()
    
    while True:
if __name__ == "__main__":
    worker()