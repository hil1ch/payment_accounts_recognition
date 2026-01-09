from math import e
from redis.asyncio import Redis
from app.schemas.redis_message import RedisMessage
from uuid import UUID
from app.core.config import settings

async def save_message_to_redis(redis: Redis, key: UUID, message: RedisMessage):
    value = message.model_dump_json()
    await redis.set(str(key), value, ex=settings.redis_expire_seconds)

async def get_message_from_redis(redis: Redis, key: UUID) -> RedisMessage | None:
    value = await redis.get(str(key))
    if value is None:
        return None
    
    return RedisMessage.model_validate_json(value)

# If the client crashes before the result is displayed, he will not be able to get it again.
# async def delete_message_from_redis(redis: Redis, key: UUID):
#     await redis.delete(str(key))