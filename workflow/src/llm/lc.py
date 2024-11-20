"""Langchain utils"""

from typing import List
from langchain.tools import StructuredTool
from src.llm.config import LLMConfig, LLMProvider, LLMModelType
from loguru import logger

# def tools_factory_structured(tools: List[str]) -> List[StructuredTool]:
#     """factory method to create tools"""
#     from src.tools.demo import structured_tools as demo_tools

#     structured_tools = []
#     for tool_name in tools:
#         package, tool = tool_name.split(".")
#         if package == "demo":
#             structured_tools.append(demo_tools[tool])
#         else:
#             raise ValueError(f"Unsupported tool package: {package}")
#     return structured_tools


def tools_factory(tools: List[str]=None) -> dict[str, callable]:
    """factory method to create tools return callable functions"""
    if tools is None:
        return {}
    from src.tools import tools_map

    callable_tools = {}
    for tool_name in tools:
        callable_tools[tool_name] = tools_map[tool_name]
    return callable_tools


def format_ollama_tools_schema(tool: StructuredTool):
    """format ollama tools schema
    https://python.langchain.com/v0.1/docs/integrations/chat/ollama_functions
    """
    data = {
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.args_schema.schema(),
    }
    return data


def init_ollama_llm(config: LLMConfig,json_mode:bool=False):
    """init ollama llm from langchain"""
    # from langchain_community.chat_models import ChatOllama
    # from langchain_community.embeddings import OllamaEmbeddings
    # from langchain_experimental.llms.ollama_functions import OllamaFunctions
    # from langchain_ollama import OllamaFunctions

    from langchain_ollama import ChatOllama
    from langchain_ollama import OllamaEmbeddings

    model_type = LLMModelType(config.model_type)
    config_args = config.args or {}
    if model_type == LLMModelType.CHAT:
        if json_mode:
            llm = ChatOllama(
                model=config.model,
                base_url=config.base_url,
                temperature=config.temperature,
                format="json",
                **config_args,
            )
        else:
            llm = ChatOllama(
                model=config.model,
                base_url=config.base_url,
                temperature=config.temperature,
                **config_args,
            )
        if config.tools:
            tools_map = tools_factory(config.tools)
            logger.debug(f"Bind tools to llm: {tools_map}")
            llm = llm.bind_tools(tools=list(tools_map.values()))
        return llm
    elif model_type == LLMModelType.EMBEDDING:
        return OllamaEmbeddings(
            model=config.model,
            base_url=config.base_url,
            **config_args,
        )
    else:
        raise ValueError(f"Unsupported model type: {config.model_type}")


def init_openai_llm(config: LLMConfig,json_mode:bool=False):
    """init openai llm from langchain"""
    from langchain_openai import ChatOpenAI
    from langchain_openai import OpenAIEmbeddings

    model_type = LLMModelType(config.model_type)
    config_args = config.args or {}
    if model_type == LLMModelType.EMBEDDING:
        return OpenAIEmbeddings(
            model=config.model,
            base_url=config.base_url,
            api_key=config.api_key,
            **config_args,
        )
    else:
        if json_mode:
            llm = ChatOpenAI(
                model=config.model,
                base_url=config.base_url,
                temperature=config.temperature,
                api_key=config.api_key,
                **config_args,
                format="json",
            )
        else:
            llm = ChatOpenAI(
                model=config.model,
                base_url=config.base_url,
                temperature=config.temperature,
                api_key=config.api_key,
                **config_args,
            )
        if config.tools:
            tools_map = tools_factory(config.tools)
            logger.debug(f"Bind tools to llm: {tools_map}")
            llm = llm.bind_tools(tools=list(tools_map.values()))
        return llm


def llm_factory(config: LLMConfig,json_mode:bool=False):
    """factory method to create llm"""
    if config.provider.lower() == LLMProvider.OLLAMA.value:
        return init_ollama_llm(config,json_mode)
    elif config.provider.lower() == LLMProvider.OPENAI.value:
        return init_openai_llm(config,json_mode)
    else:
        raise ValueError(f"Unsupported provider: {config.provider}")
