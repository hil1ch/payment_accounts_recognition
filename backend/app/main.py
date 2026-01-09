from fastapi import FastAPI
from app.api import parse, get_result
from contextlib import asynccontextmanager
from app.core.rabbit_connection import rabbit_conn
from redis.asyncio import Redis
from app.core.config import settings
from app.core.logging_config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    try:
        logger.info("Starting up application...")
        await rabbit_conn.init()
        logger.info("RabbitMQ connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ: {str(e)}")
        raise
    
    try:
        app.state.redis = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True
        )
        logger.info(f"Redis connection established (host: {settings.redis_host}:{settings.redis_port})")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise

    yield

    #shutdown
    try:
        logger.info("Shutting down application...")
        await app.state.redis.close()
        await app.state.redis.connection_pool.disconnect()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {str(e)}")
    
    try:
        await rabbit_conn.close()
        logger.info("RabbitMQ connection closed")
    except Exception as e:
        logger.error(f"Error closing RabbitMQ connection: {str(e)}")

app = FastAPI(lifespan=lifespan)

app.add_api_route("/parse", parse, methods=["POST"])
app.add_api_route("/result/{job_id}", get_result, methods=["GET"])




