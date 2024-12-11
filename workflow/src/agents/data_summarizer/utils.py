from pydantic import BaseModel
from enum import Enum
from urllib.parse import urlparse
import os
import tempfile
import validators
from src.agents.data_summarizer import utils_yt
from src.agents.data_summarizer import utils_sharepoint
from src.agents.data_summarizer import utils_google_drive
from src.retriever.parser import PARSERS
from typing import Optional
from src.agents.data_summarizer import utils_stt
from src.agents.data_summarizer import utils_download
from loguru import logger


class DataType(Enum):
    MEDIA = "media"  # audio or video
    FILE = "file"
    URL = "url"
    IMAGE = "image"


class DataContent(BaseModel):
    title: str
    content: str
    data_type: DataType


def is_valid_domain(url: str, domain: str) -> bool:
    """check if the url is from the given domain"""
    try:
        parsed_url = urlparse(url)
        # Extract the domain from the netloc and compare it
        return parsed_url.netloc.endswith(domain)
    except ValueError:
        return False


def parse_data(data_path: str, file_extension: str) -> str:
    """parse data using parsers"""
    if file_extension not in PARSERS:
        raise ValueError(f"File extension {file_extension} is not supported")
    loader = PARSERS[file_extension](data_path)
    docs = loader.load()
    return "\n".join([doc.page_content for doc in docs])


def extract_data(data_source: str, **kwargs) -> DataContent:
    """extract data from the url
    ARGS:
        data_source: could be a url or a file path
        **kwargs: other arguments
    RETURNS:
        the data content
    """
    audio_extensions = ["mp3", "mp4", "wav", "m4a", "aac"]
    image_extensions = ["jpg", "jpeg", "png"]
    text_extensions = ["txt", "json", "xml", "html", "csv"]
    office_extensions = ["docx", "doc", "pdf", "ppt", "pptx"]
    supported_file_extensions = audio_extensions + image_extensions + text_extensions + office_extensions

    stt_config = kwargs.get("stt_config", None)

    with tempfile.TemporaryDirectory() as temp_dir:
        if validators.url(data_source):
            if is_valid_domain(data_source, "youtube.com"):
                content = utils_yt.extract_youtube_transcript(data_source, stt_config)
                title = utils_yt.get_yt_title(data_source)
                return DataContent(
                    title=title, content=content, data_type=DataType.MEDIA
                )
            elif is_valid_domain(data_source, "sharepoint.com") or is_valid_domain(data_source, "onedrive.com"):
                # TODO: add support for folder download
                file_path_list = utils_sharepoint.download_sharepoint_data(data_source, temp_dir)
                file_path_list = [x for x in file_path_list if os.path.basename(x).split(".")[-1] in supported_file_extensions]
                if len(file_path_list) == 0:
                    raise ValueError(f"No file found in {data_source}")
                data_path = file_path_list[0]
            elif is_valid_domain(data_source, "drive.google.com") or is_valid_domain(data_source, "docs.google.com"):
                data_path = utils_google_drive.download_google_drive_data(data_source, temp_dir)
            else:
                # download the data
                data_path = utils_download.download_data(data_source, temp_dir)
        else:
            data_path = data_source
        print(f"data_path: {data_path}")
        file_extension = os.path.basename(data_path).split(".")[-1].lower()
        if file_extension in audio_extensions:
            content = utils_stt.transcribe_audio(data_path, stt_config)
            title = os.path.basename(data_path)
            data_type = DataType.MEDIA
        elif file_extension in image_extensions:
            data_type = DataType.IMAGE
            # TODO: add image parser ocr or vlm
            raise ValueError(f"Image extension {file_extension} is not supported")
        else:
            content = parse_data(data_path, file_extension)
            title = os.path.basename(data_path)
            data_type = DataType.FILE
        return DataContent(title=title, content=content, data_type=data_type)
