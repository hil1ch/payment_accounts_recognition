from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
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



app = FastAPI(
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
    openapi_url="/openapi.json" if settings.app_env == "development" else None
    )

app.add_api_route("/parse", parse, methods=["POST"])
app.add_api_route("/result/{job_id}", get_result, methods=["GET"])

@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")

    if content_length and int(content_length) > settings.file_max_size_mb * 1024 * 1024:
        logger.warning(f"File size exceeds limit: {content_length} bytes")
        return JSONResponse(
            status_code=413,
            content={"detail": f"Maximum file size is {settings.file_max_size_mb} MB"},
        )

    return await call_next(request)


