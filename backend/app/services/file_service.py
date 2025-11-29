import os
from fastapi import UploadFile
from pathlib import Path
from pydantic import DirectoryPath, FilePath
import uuid 


def generate_file_id(file: UploadFile, job_id: uuid.UUID) -> str:
    filename = Path(file.filename).name
    new_filename = f"{job_id}-{filename}"
    return new_filename

def save_uploaded_file(uploaded_file: UploadFile, destination_folder: DirectoryPath, job_id: uuid.UUID) -> FilePath:
    print(uploaded_file.filename, uploaded_file.content_type)
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    new_filename = generate_file_id(uploaded_file, job_id)
    file_path: FilePath = os.path.join(destination_folder, new_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(uploaded_file.file.read())
    return file_path
