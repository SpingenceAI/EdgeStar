"""Base LLM"""

from typing import List, Any, Union
from abc import ABC, abstractmethod
import time
import requests
from pydantic import BaseModel
import uuid
import os
from loguru import logger

from src.llm.config import LLMConfig, LLMProvider, LLMModelType


class Message(BaseModel):
    """Message"""

    role: str  # system, user, assistant
    content: str


class LLMException(Exception):
    """LLM exception"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class RequestException(Exception):
    """Request exception"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def send_requests(
    url: str,
    method: str,
    data: dict = None,
    params: dict = None,
    response_data_class: Any = None,
    *args,
    **kwargs,
) -> requests.Response:
    """Send request
    ARGS:
        url: str
        method: str
        data: dict
        params: dict
        response_data_class: Any
        retry_times: int
        retry_interval: float
    RETURNS:
        requests.Response or response_data_class
    """
    request_id = kwargs.pop("request_id", uuid.uuid4())
    with logger.contextualize(
        request_id=str(request_id), url=url, method=method, data=data, params=params
    ):
        retry_times = kwargs.pop("retry_times", 3)
        retry_interval = kwargs.pop("retry_interval", 0.1)
        response = None
        for retry_counts in range(retry_times):
            try:
                response = requests.request(
                    method, url, json=data, params=params, **kwargs
                )
                if response.status_code == 200:
                    return (
                        response
                        if response_data_class is None
                        else response_data_class(**response.json())
                    )
                raise RequestException(
                    f"Request failed({response.status_code}): {response.text}"
                )
            except Exception as e:
                logger.error(f"Request tried {retry_counts + 1} times but failed: {e}")
                time.sleep(retry_interval)
                continue
        logger.error(f"Request tried {retry_times} times but failed.")
        raise LLMException(
            f"Request({str(request_id)}) tried {retry_times} times but failed."
        )


class BaseLLM(ABC):
    """Base LLM"""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    def chat(self, messages: List[Union[Message, dict]], **kwargs) -> str:
        """Chat with LLM"""
        pass

    @abstractmethod
    def embed_text(self, text: str, **kwargs) -> List[float]:
        """Embed text"""
        pass


"""Ollama utils"""


class OllamaBase:
    """Ollama Base
    OllamaAPI
    https://github.com/ollama/ollama/blob/main/docs/api.md
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = config.base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

    def add_args(self, data: dict) -> dict:
        """add args to data"""
        data["model"] = self.config.model
        data["stream"] = False
        if self.config.args:
            data.update(self.config.args)
        return data

    def check_model_exist(self, model: str) -> bool:
        """Check if the model exists"""
        if ":" not in model:
            model = f"{model}:latest"
        return model in self.list_models()

    def list_models(self) -> List[str]:
        """list local models"""
        url = f"{self.base_url}/api/tags"
        response = send_requests(url, method="GET")
        return [x["name"] for x in response.json()["models"] if "name" in x]

    def pull_model(self, model_name: str):
        """pull model
        return :
            success: {"status": "success"}
            error: {'error': 'pull model manifest: file does not exist'}
        """
        if ":" not in model_name:
            model_name = f"{model_name}:latest"
        if self.check_model_exist(model_name):
            return
        url = f"{self.base_url}/api/pull"
        send_requests(url, method="POST", data={"name": model_name})


class OllamaChat(OllamaBase):
    def invoke(self, messages: List[Union[Message, dict]], **kwargs) -> Message:
        """complete chat"""
        assert isinstance(messages, list), "messages must be a list of Message or dict"
        if isinstance(messages[0], Message):
            messages = [x.dict() for x in messages]
        url = f"{self.base_url}/api/chat"
        data = {"messages": messages}
        data = self.add_args(data)
        response = send_requests(url, method="POST", data=data)
        return Message(**response.json()["message"])


class OllamaEmbed(OllamaBase):
    def invoke(self, text: str, **kwargs) -> List[float]:
        """embed text"""
        url = f"{self.base_url}/api/embeddings"
        data = {"prompt": text}
        data = self.add_args(data)
        response = send_requests(url, method="POST", data=data)
        return response.json()["embedding"]


class OllamaGenerate(OllamaBase):
    def invoke(self, prompt: str, **kwargs) -> str:
        """generate text"""
        url = f"{self.base_url}/api/generate"
        data = {"prompt": prompt}
        data = self.add_args(data)
        response = send_requests(url, method="POST", data=data)
        return response.json()["response"]


def llm_factory(config: LLMConfig) -> BaseLLM:
    """LLM factory"""
    if config.provider == LLMProvider.OLLAMA.value:
        if config.model_type == LLMModelType.CHAT.value:
            return OllamaChat(config)
        elif config.model_type == LLMModelType.EMBEDDING.value:
            return OllamaEmbed(config)
        elif config.model_type == LLMModelType.GENERATE.value:
            return OllamaGenerate(config)
        else:
            raise ValueError(f"Unsupported model type: {config.model_type}")
    else:
        raise ValueError(f"Unsupported provider: {config.provider}")
