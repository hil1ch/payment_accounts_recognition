from pydantic import UUID4, BaseModel, FilePath, Json
from pydantic import UUID4, BaseModel
from app.schemas.client_DTOs import JobStatus
from datetime import datetime

class RedisMessage(BaseModel):
    status: JobStatus
    file_path: FilePath
    creadtion_time: datetime
    result: dict | None = None #maybe there should be json here, but with it was error
    
