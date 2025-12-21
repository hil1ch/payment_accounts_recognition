from pydantic import BaseModel, FilePath
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    done = "done"
    in_progress = "in_progress"
    waiting = "waiting"
    failed = "failed"

class RedisMessage(BaseModel):
    status: JobStatus
    file_path: FilePath
    creadtion_time: datetime
    result: dict | None = None #maybe there should be json here, but with it was error
    