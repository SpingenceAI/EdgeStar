from src.openai_whisper_model import Model
# from src.faster_whisper_model import Model
from src import utils
from pydantic import BaseModel
import os
from src.env import MODEL_NAME
from typing import List

class Transcription(BaseModel):
    text: str
    start: float  # in seconds
    end: float  # in seconds


class Transcriptions(BaseModel):
    file_name: str
    audio_length: float  # in seconds
    chunks: List[Transcription]
    transcript: str


model = Model(MODEL_NAME)


def transcribe_chunk(audio_path: str, language: str):
    """transcribe a chunk
    Args:
        audio_path (str): audio path
        language (str): language
    Returns:
        str: transcription
    """

    return model.transcribe(audio_path, language)


def transcribe_chunk_by_chunk(
    temp_folder: str, file_path: str, language: str = "zh"
) -> Transcriptions:
    """transcribe the file, if file is video convert to audio first, will chunk the audio into 30s segments with 0s overlap
    model will trim the audio to 30s if the audio is longer than 30s
    Args:
        temp_folder (str): temp folder path
        file_path (str): file path
        language (str): language
    Returns:
        Transcriptions: transcriptions
    """
    repakcage_file_path = os.path.join(temp_folder, f"repackage.mp3")
    utils.repackage_audio(file_path, repakcage_file_path)
    audio_length = utils.get_audio_duration(repakcage_file_path)

    chunk_length = 30
    overlap = 0
    if chunk_length < 30:
        # model will trim the audio to 30s
        raise ValueError(
            "chunk_length must be greater or equal to 30, model will trim the audio to 30s"
        )
    autio_path_list = utils.split_audio_with_overlap(
        input_file=repakcage_file_path,
        output_dir=temp_folder,
        chunk_length=chunk_length,
        overlap=overlap,
    )
    chunks = []
    # autio_path_list = [x.path for x in os.scandir(TEMP_FOLDER)]
    for audio_path in autio_path_list[:2]:
        audio_filename = os.path.basename(audio_path)
        start, end = audio_filename.replace(".mp3", "").split("-")
        text = model.transcribe_chunk(audio_path, language)
        chunks.append(Transcription(text=text, start=start, end=end))
    return Transcriptions(
        file_name=os.path.basename(file_path),
        audio_length=audio_length,
        chunks=chunks,
        transcript="\n".join([x.text for x in chunks]),
    )

def transcribe(
    temp_folder: str,
    file_path: str
):
    repakcage_file_path = os.path.join(temp_folder, f"repackage.mp3")
    utils.repackage_audio(file_path, repakcage_file_path)
    return Transcriptions(
        file_name=os.path.basename(file_path),
        audio_length=utils.get_audio_duration(repakcage_file_path),
        chunks=[],
        transcript=model.transcribe(repakcage_file_path),
    )