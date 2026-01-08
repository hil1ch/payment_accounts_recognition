from pydantic import UUID4, BaseModel, FilePath
from datetime import datetime

class RabbitMessage(BaseModel):
    job_id: UUID4
    file_path: FilePath
    creation_time: datetime
    
