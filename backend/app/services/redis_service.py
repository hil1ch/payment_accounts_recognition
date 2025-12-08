from redis.asyncio import Redis
from app.schemas.redis_message import RedisMessage
from uuid import UUID

async def save_message_to_redis(redis: Redis, key: UUID, message: RedisMessage):
    value = message.model_dump_json()
    await redis.set(str(key), value)

async def get_message_from_redis(redis: Redis, key: UUID) -> RedisMessage | None:
    value = await redis.get(str(key))
    if value is None:
        return None
    return RedisMessage.model_validate_json(value)

async def delete_message_from_redis(redis: Redis, key: UUID):
    await redis.delete(str(key))