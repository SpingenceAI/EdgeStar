import whisper

import whisper
import logging
from src.env import MODEL_DIR

def singletone(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singletone
class Model:
    def __init__(self, model_name: str):
        if model_name not in ["tiny", "base", "small", "medium", "large","turbo"]:
            raise ValueError("Invalid model name")
        logging.info(f"Loading model: {model_name}")
        self.model = whisper.load_model(model_name,download_root=MODEL_DIR)
        logging.info(f"Model loaded: {self.model}")

    def transcribe_chunk(self, audio_path: str, language: str = "zh") -> str:
        if language not in ["zh", "en"]:
            raise ValueError("Invalid language")

        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)  # pad or trim audio to 30s
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        # _,probs = self.model.detect_language(mel)
        options = whisper.DecodingOptions(language=language, fp16=True)
        result = whisper.decode(self.model, mel, options)
        return result.text
    
    def transcribe(self, audio_path: str) -> str:
        return self.model.transcribe(audio_path)['text']
