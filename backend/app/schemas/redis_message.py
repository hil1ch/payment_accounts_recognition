from pydantic import BaseModel, FilePath
from app.schemas.client_DTOs import JobStatus
from datetime import datetime

class RedisMessage(BaseModel):
    status: JobStatus
    file_path: FilePath
    creation_time: datetime
    result: dict | None = None #maybe there should be json here, but with it was error
    
