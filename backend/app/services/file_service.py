import os
from fastapi import UploadFile
from pathlib import Path
from pydantic import DirectoryPath, FilePath
import uuid 
from app.core.logging_config import logger


def generate_file_id(file: UploadFile, job_id: uuid.UUID) -> str:
    filename = Path(str(file.filename)).name
    new_filename = f"{job_id}-{filename}"
    return new_filename

#maybe errors with async 
def save_uploaded_file(uploaded_file: UploadFile, destination_folder: DirectoryPath, job_id: uuid.UUID) -> FilePath:
    try:
        logger.debug(f"Saving file: {uploaded_file.filename}, content_type: {uploaded_file.content_type}, job_id: {job_id}")
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
            logger.debug(f"Created directory: {destination_folder}")
        new_filename = generate_file_id(uploaded_file, job_id)
        file_path: FilePath =  os.path.join(destination_folder, new_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(uploaded_file.file.read())
        logger.info(f"File saved successfully: {file_path}, job_id: {job_id}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save file {uploaded_file.filename} for job_id {job_id}: {str(e)}")
        raise

#use it in endpoint when job_statuse = done 
def delete_file(file_path: FilePath):
    try:
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        raise e