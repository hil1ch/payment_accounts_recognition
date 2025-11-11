from typing import Any
from pydantic import BaseModel, Json
from uuid import UUID
from enum import Enum

class JobStatus(str, Enum):
    done = "done"
    in_progress = "in_progress"


class ParseResponce(BaseModel):
    job_id: UUID

class ResultResponce(BaseModel):
    status: JobStatus
    processing_time_ms: int
    result: Json[Any] | None
