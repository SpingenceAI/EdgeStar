from typing import List
import tempfile
import os
import shutil

from fastapi import FastAPI
from fastapi import UploadFile

from src import use_cases

app = FastAPI()

@app.get("/")
def health_check():
    return "STT is running"

@app.post("/transcribe_chunk_by_chunk")
def transcribe_chunk_by_chunk_api(file: UploadFile, language: str = "zh") -> use_cases.Transcriptions:
    temp_folder = tempfile.mkdtemp()
    # temp_folder = "temp_test"
    os.makedirs(temp_folder, exist_ok=True)
    temp_file_path = os.path.join(temp_folder, file.filename)
    with open(temp_file_path, "wb") as f:
        f.write(file.file.read())
    transcriptions = use_cases.transcribe_chunk_by_chunk(temp_folder, temp_file_path, language)
    shutil.rmtree(temp_folder, ignore_errors=True)
    return transcriptions.dict()


@app.post("/transcribe")
def transcribe_file_api(file: UploadFile) -> use_cases.Transcriptions:
    temp_folder = tempfile.mkdtemp()
    # temp_folder = "temp_test"
    os.makedirs(temp_folder, exist_ok=True)
    temp_file_path = os.path.join(temp_folder, file.filename)
    with open(temp_file_path, "wb") as f:
        f.write(file.file.read())
    transcriptions = use_cases.transcribe(temp_folder,temp_file_path)
    shutil.rmtree(temp_folder, ignore_errors=True)
    return transcriptions.dict()
