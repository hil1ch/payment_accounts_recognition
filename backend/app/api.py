import json
import os
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
from fastapi import Request, File
from app.core.logging_config import logger
from typing import Annotated

async def parse(request: Request, file: UploadFile ) -> ParseResponce:
    curr_job_id = uuid4()
    
    if(file.content_type not in  ["image/jpeg", "image/png","application/pdf" ]):
        logger.warning(f"Unsupported file type: {file.content_type}, job_id: {curr_job_id}")
        raise HTTPException(status_code=400, detail="Unsupported file type. Only JPEG, PNG, and PDF are allowed.")
    
    logger.info(f"Received file: {file.filename} (type: {file.content_type}), job_id: {curr_job_id}")
    
    try:
        file_path = save_uploaded_file(file, settings.shared_dir, curr_job_id)
        logger.debug(f"File saved to: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file for job_id {curr_job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    redis_message = RedisMessage(
        status=JobStatus.waiting,
        file_path=file_path,
        creation_time=datetime.now(),
        result={} 
    )
    await save_message_to_redis(request.app.state.redis, curr_job_id, redis_message)
    logger.debug(f"Job status saved to Redis, job_id: {curr_job_id}")

    queue_message = QueueMessage(
        job_id=curr_job_id,
        file_path=file_path,
        creation_time=datetime.now()
    )
    await publisher.publish(queue_message)
    logger.info(f"Job published to queue, job_id: {curr_job_id}")

    return ParseResponce(job_id = curr_job_id)

async def get_result(request: Request, job_id: UUID) -> ResultResponce:
    logger.info(f"Result requested for job_id: {job_id}")
    
    message = await get_message_from_redis(request.app.state.redis, job_id)
    if message is None:
        logger.warning(f"Job not found in Redis, job_id: {job_id}")
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    logger.debug(f"Job status: {message.status}, job_id: {job_id}")
    
    if message.status == JobStatus.failed:
        logger.error(f"Job processing failed, job_id: {job_id}")
        raise HTTPException(status_code=500, detail="Error processing file")
    
    if message.status == JobStatus.done:
        logger.info(f"Job completed successfully, job_id: {job_id}")
        # If the client crashes before the result is displayed, he will not be able to get it again.
        #        await delete_message_from_redis(request.app.state.redis, job_id)
        if(os.path.exists(message.file_path)):
            try:
                delete_file(message.file_path) #TODO: do async maybe
                logger.debug(f"File deleted after processing, job_id: {job_id}")
            except Exception as e:
                logger.error(f"Failed to delete file for job_id {job_id}: {str(e)}")
                
    #BUG: processing time calculation on ml_side
    processing_time_ms = int((datetime.now() - message.creation_time).total_seconds() * 1000)
    logger.info(f"Returning result for job_id: {job_id}, processing_time: {processing_time_ms}ms")
    
    return ResultResponce(status = message.status, 
                          result = json.dumps(message.result),  
                          processing_time_ms = processing_time_ms)