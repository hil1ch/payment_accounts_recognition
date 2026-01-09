import json
from fastapi import HTTPException, UploadFile
from app.schemas.client_DTOs import *
from app.schemas.redis_message import RedisMessage
from app.schemas.queue_message import QueueMessage
from app.services.rabbit_publisher import publisher
from datetime import datetime
from app.core.config import settings
from app.services.file_service import save_uploaded_file, delete_file
from app.services.redis_service import save_message_to_redis, get_message_from_redis
from uuid import UUID, uuid4
from fastapi import Request

async def parse(request: Request, file: UploadFile) -> ParseResponce:
    curr_job_id = uuid4()
    file_path = save_uploaded_file(file, settings.shared_dir, curr_job_id)

    redis_message = RedisMessage(
        status=JobStatus.waiting,
        file_path=file_path,
        creadtion_time=datetime.now(),
        result={} 
    )
    await save_message_to_redis(request.app.state.redis, curr_job_id, redis_message)

    queue_message = QueueMessage(
        job_id=curr_job_id,
        file_path=file_path,
        creation_time=datetime.now()
    )
    await publisher.publish(queue_message)

    return ParseResponce(job_id = curr_job_id)

async def get_result(request: Request, job_id: UUID) -> ResultResponce:
    message = await get_message_from_redis(request.app.state.redis, job_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Job ID not found")
    elif message.status == JobStatus.failed:
        raise HTTPException(status_code=500, detail="Error processing file")
    
    if message.status == JobStatus.done:
# If the client crashes before the result is displayed, he will not be able to get it again.
#        await delete_message_from_redis(request.app.state.redis, job_id)
        delete_file(message.file_path) #TODO: do async maybe
    
    return ResultResponce(status = message.status, 
                          result = json.dumps(message.result),  
                          processing_time_ms = int((datetime.now() - message.creation_time).total_seconds() * 1000))