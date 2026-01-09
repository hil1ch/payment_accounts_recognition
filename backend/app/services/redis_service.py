from math import e
from redis.asyncio import Redis
from app.schemas.redis_message import RedisMessage
from uuid import UUID
from app.core.config import settings
from app.core.logging_config import logger

async def save_message_to_redis(redis: Redis, key: UUID, message: RedisMessage):
    try:
        value = message.model_dump_json()
        await redis.set(str(key), value, ex=settings.redis_expire_seconds)
        logger.debug(f"Message saved to Redis, key: {key}, ttl: {settings.redis_expire_seconds}s, status: {message.status}")
    except Exception as e:
        logger.error(f"Failed to save message to Redis for key {key}: {str(e)}")
        raise

async def get_message_from_redis(redis: Redis, key: UUID) -> RedisMessage | None:
    try:
        value = await redis.get(str(key))
        if value is None:
            logger.warning(f"Message not found in Redis, key: {key}")
            return None
        
        message = RedisMessage.model_validate_json(value)
        logger.debug(f"Message retrieved from Redis, key: {key}, status: {message.status}")
        return message
    except Exception as e:
        logger.error(f"Failed to retrieve message from Redis for key {key}: {str(e)}")
        raise

# If the client crashes before the result is displayed, he will not be able to get it again.
# async def delete_message_from_redis(redis: Redis, key: UUID):
#     await redis.delete(str(key))