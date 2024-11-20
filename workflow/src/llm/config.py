from pydantic import BaseModel
from typing import Optional,List


from enum import Enum


class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"

class LLMModelType(Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    GENERATE = "generate"
    FUNCTION = "function"


class LLMConfig(BaseModel):
    """configuration of the llm"""
    provider: LLMProvider
    model: str
    system_prompt: Optional[str] = None
    system_prompt_tail: Optional[str] = None
    tools: Optional[List[str]] = None
    model_type: Optional[LLMModelType] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = 0.5
    args: Optional[dict] = None

    class Config:
        use_enum_values = True