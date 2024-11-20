"""Download and transcribe youtube video"""

from typing import Optional

import os
import tempfile
from pytubefix import YouTube
from src.agents.data_summarizer.utils_stt import transcribe_audio, STTConfig
from loguru import logger
import time
def extract_youtube_transcript(url: str, stt_config: Optional[STTConfig] = None) -> str:
    """get the transcript of the youtube video
    ARGS:
        url: the url of the youtube video
        stt_config: the config for the speech to text model
    RETURNS:
        the transcript of the youtube video
    """
    logger.debug(f"[UTILS_YT]-extract_youtube_transcript: {url}")
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(temp_dir, exist_ok=True)
        yt = YouTube(url)
        if len(yt.caption_tracks) > 0:
            logger.debug(f"Found captions:{yt.caption_tracks}")
            caption = yt.caption_tracks[0]
            caption.download(output_path=temp_dir, title="transcript", srt=True)
            file_path = [x.path for x in os.scandir(temp_dir)][0]
            with open(file_path, "r") as f:
                transcript = f.read()
            return transcript
        else:
            logger.warning("No caption found for the youtube video")
            if stt_config is None:
                raise ValueError("stt_config is required for youtube without caption")
            file_name = f"{time.time()}.mp3"
            file_path = yt.streams.get_lowest_resolution().download(output_path=temp_dir, filename=file_name)
            transcript = transcribe_audio(file_path, stt_config)
            # os.remove(file_path)
            return transcript


def get_yt_title(url: str) -> str:
    """get the title of the youtube video"""
    return YouTube(url).title
