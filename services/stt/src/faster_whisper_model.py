from faster_whisper import WhisperModel
import time
# model_size = "large-v3"
# # model_size = "distil-large-v3"
# # Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")

# # or run on GPU with INT8
# # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# # or run on CPU with INT8
# # model = WhisperModel(model_size, device="cpu", compute_type="int8")

# segments, info = model.transcribe("test.wav", beam_size=5)

# print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
# start = time.time()
# for segment in segments:
#     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
# end = time.time()
# print(f"Time taken: {end - start} seconds")
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
        if model_name not in ["large-v3"]:
            raise ValueError("Invalid model name")
        logging.info(f"Loading model: {model_name}")
        self.model = WhisperModel(model_name, device="cuda", compute_type="float16",download_root=MODEL_DIR)
        logging.info(f"Model loaded: {self.model}")

    def transcribe_chunk(self, audio_path: str, language: str = "zh") -> str:
        if language not in ["zh", "en"]:
            raise ValueError("Invalid language")

        result_text = ""
        segments, info = self.model.transcribe(audio_path, beam_size=5,vad_filter=True)
        for segment in segments:
            result_text += segment.text
        return result_text
    
    def transcribe(self, audio_path: str) -> str:
        return self.transcribe_chunk(audio_path)
