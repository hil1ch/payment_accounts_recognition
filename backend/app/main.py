from fastapi import FastAPI
from app.api import parse, get_result
from contextlib import asynccontextmanager
from app.core.rabbit_connection import rabbit_conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    #startup
    await rabbit_conn.init()

    yield

    #shutdown
    await rabbit_conn.close()

app = FastAPI(lifespan=lifespan)

app.add_api_route("/parse", parse, methods=["POST"])
app.add_api_route("/result/{job_id}", get_result, methods=["GET"])




