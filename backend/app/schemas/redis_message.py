from pydantic import UUID4, BaseModel, FilePath
from pydantic import UUID4, BaseModel
from app.schemas.client_DTOs import JobStatus

class RedisMessage(BaseModel):
    job_id: UUID4
    status: JobStatus
    file_path: FilePath
    
    
