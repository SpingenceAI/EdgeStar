from pydantic import BaseModel
from typing import Optional

import requests
import opencc


class STTConfig(BaseModel):
    """configuration of the speech to text"""

    base_url: str
    model: str = "whisper"
    provider: str = "custom"
    api_key: Optional[str] = None


def convert_language(text: str, mode: str = "s2twp"):
    """convert language of the text using opencc
    mode: s2tw, s2twp (simplified chinese to traditional chinese with pronunciation)
    """
    return opencc.OpenCC(mode).convert(text)


def transcribe_audio(file_path: str, stt_config: STTConfig) -> str:
    """transcribe audio to text"""
    if stt_config.provider == "custom":
        url = f"{stt_config.base_url}/transcribe"
    else:
        raise ValueError(f"provider {stt_config.provider} is not supported")
    files = {"file": open(file_path, "rb")}
    response = requests.post(url, files=files)
    return convert_language(response.json()["transcript"], "s2twp")
