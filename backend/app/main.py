from fastapi import FastAPI
from app.api import parse, get_result

app = FastAPI()

app.add_api_route("/parse", parse, methods=["POST"])
app.add_api_route("/result/{job_id}", get_result, methods=["GET"])




