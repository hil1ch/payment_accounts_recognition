from fastapi import FastAPI
from app.api import parse, get_result
from contextlib import asynccontextmanager
from app.core.rabbit_connection import rabbit_conn
from redis.asyncio import Redis
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    await rabbit_conn.init()
    app.state.redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        decode_responses=True
    )

    yield

    #shutdown
    await app.state.redis.close()
    await app.state.redis.connection_pool.disconnect()
    await rabbit_conn.close()

app = FastAPI(lifespan=lifespan)

app.add_api_route("/parse", parse, methods=["POST"])
app.add_api_route("/result/{job_id}", get_result, methods=["GET"])




