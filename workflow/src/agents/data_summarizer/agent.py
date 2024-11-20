from typing import TypedDict, Optional
from loguru import logger
import validators
from urllib.parse import urlparse
import os
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
import requests
import tempfile
from src.llm.config import LLMConfig, LLMModelType
from src.llm.lc import llm_factory, tools_factory
from src.llm.config import LLMModelType
from src.agents.data_summarizer.utils import extract_data, DataContent, DataType
from src.agents.data_summarizer.utils_stt import STTConfig
from src.retriever.parser import PARSERS
from langchain_core.messages import (
    BaseMessage,
    ToolMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
)

DEFAULT_VIDEO_SUMMARY_PROMPT = """
The Transcript is wrapped in the <transcription> tag.:
<transcription>
{transcription}
</transcription>
The content of the answer needs to be based on the content of the above transcript.
You are a professional document organizer and need to organize the content for the meeting transcript based on the following requirements.
{format}
Do not add content outside the transcript.
"""
DEFAULT_VIDEO_SUMMARY_FORMAT = """Condense a video transcript into a captivating and informative 250-word summary that highlights key points and engages viewers."""

DEFAULT_SUMMARY_PROMPT = """
The following content is wrapped in the <content> tag.
<content>
{content}
</content>
{format}
"""
DEFAULT_SUMMARY_FORMAT = """
Please provide a concise summary of the content.
"""

DEFAULT_ANSWER_PROMPT = """
The following content is wrapped in the <content> tag.
<content>
{content}
</content>
Only provide a concise answer using information from the content. If the content is not related to the question, please say "Content is not related to the question."
"""

EXTRACT_CONTENT_PROMPT = """
Extract the relevant content from the question.
<question>
{question}
</question>
<content>
{content}
</content>
"""

from pydantic import BaseModel
from enum import Enum


class State(TypedDict):
    """state of the data_summarizer"""

    data_source_list: list[str]
    data_content_list: list[DataContent]
    summary_list: list[str]
    answer: str
    format_instruction: str = ""
    user_query: str = ""
    extract_error: bool = False


class TranslationConfig(BaseModel):
    """Translation config"""

    enable: bool = False
    llm: Optional[LLMConfig] = None
    language: str = "zh-tw"


class AgentConfig(BaseModel):
    """configuration of the data_summarizer"""

    chat_llm: LLMConfig
    stt_config: Optional[STTConfig] = None
    input_translation: Optional[TranslationConfig] = None
    output_translation: Optional[TranslationConfig] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.chat_llm.model_type is None:
            self.chat_llm.model_type = LLMModelType.CHAT


class Agent:
    """Agent for data_summarizer"""

    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config
        self.llm = llm_factory(agent_config.chat_llm)
        self.input_translator = None
        self.output_translator = None
        if agent_config.input_translation:
            self.input_translator = llm_factory(agent_config.input_translation.llm)

        if agent_config.output_translation:
            self.output_translator = llm_factory(agent_config.output_translation.llm)

    def translate(self, translator, text: str, language: str) -> str:
        """translate the text"""
        messages = [
            {
                "role": "system",
                "content": "you are a professional translator please translate the text to {language} without giving any explanation.".format(
                    language=language
                ),
            },
            {"role": "user", "content": text},
        ]
        response = translator.invoke(messages)
        return response.content

    def insert_system_prompt(self, messages: list[BaseMessage]):
        """insert the system prompt"""
        # if first message is not system, insert it
        if not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=self.system_prompt))
        else:
            messages[0].content = self.system_prompt

    def format_messages(self, messages: list[BaseMessage]):
        """format the messages"""
        for idx in range(len(messages)):
            if isinstance(messages[idx], dict):
                if messages[idx]["role"] == "user":
                    messages[idx] = HumanMessage(content=messages[idx]["content"])
                elif messages[idx]["role"] == "system":
                    messages[idx] = SystemMessage(content=messages[idx]["content"])
                elif messages[idx]["role"] == "assistant":
                    messages[idx] = AIMessage(content=messages[idx]["content"])

    def node_extract_data(self, state: State, **kwargs):
        """extract data from the data source list"""
        logger.debug(f"[DATA_summarizer-EXTRACT_DATA]-state: {state}")
        data_source_list = state.get("data_source_list", None)
        if data_source_list is None:
            raise ValueError("Data source list is None")
        data_content_list = []
        for data_source in data_source_list:
            data_content = extract_data(data_source, stt_config=self.agent_config.stt_config)
            if data_content is None:
                logger.error(f"Failed to extract data {data_source}")
                state["extract_error"] = True
                return state
            data_content_list.append(data_content)
        all_content = "\n".join(
            [data_content.content for data_content in data_content_list]
        ).strip()
        if all_content == "":
            state["extract_error"] = True
            return state
        state["data_content_list"] = data_content_list
        return state

    def node_summarize(self, state: State, **kwargs):
        """summarize the transcription"""
        logger.debug(f"[DATA_summarizer-SUMMARIZE]-state: {state}")
        data_content_list = state.get("data_content_list", None)

        if data_content_list is None:
            raise ValueError("Data content list is None")
        summary_list = []
        format_instruction = state.get("format_instruction", "")
        if format_instruction == "":
            format_instruction = DEFAULT_SUMMARY_FORMAT
        for data_content in data_content_list:
            content = data_content.content
            if data_content.data_type == DataType.MEDIA:
                user_prompt = DEFAULT_VIDEO_SUMMARY_PROMPT.format(
                    transcription=content, format=format_instruction
                )
                messages = [
                    HumanMessage(content=user_prompt),
                ]
            else:  # file or url
                user_prompt = DEFAULT_SUMMARY_PROMPT.format(
                    content=content, format=format_instruction
                )
                messages = [
                    HumanMessage(content=user_prompt),
                ]

            response = self.llm.invoke(messages)
            summary = response.content
            if self.output_translator:
                logger.debug(
                    f"[DATA_summarizer-SUMMARIZE] translate summary: {summary}"
                )
                summary = self.translate(
                    self.output_translator,
                    summary,
                    self.agent_config.output_translation.language,
                )
            summary_list.append(summary)
        state["summary_list"] = summary_list
        state["format_instruction"] = ""
        return state

    def node_generate_answer(self, state: State, **kwargs):
        """generate answer from the summary"""
        logger.debug(f"[DATA_summarizer-GENERATE_ANSWER]-state: {state}")
        data_content_list = state["data_content_list"]
        content = ""
        for data_content in data_content_list:
            if data_content.data_type == DataType.MEDIA:
                chunk = (
                    "Content is in transcription format(please read it carefully before answering):"
                    + data_content.content
                )
            else:
                chunk = data_content.content
            content += chunk
        messages = [
            HumanMessage(
                content=EXTRACT_CONTENT_PROMPT.format(
                    content=content, question=state["user_query"]
                )
            ),
        ]
        response = self.llm.invoke(messages)
        content = response.content
        logger.debug(f"[DATA_summarizer-GENERATE_ANSWER]-Relevant content: {content}")

        system_prompt = DEFAULT_ANSWER_PROMPT.format(content=content)
        user_query = state["user_query"]
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ]
        logger.debug(f"[DATA_summarizer-GENERATE_ANSWER] input messages: {messages}")
        response = self.llm.invoke(messages)
        answer = response.content
        if self.output_translator:
            logger.debug(
                f"[DATA_summarizer-GENERATE_ANSWER] translate answer: {answer}"
            )
            answer = self.translate(
                self.output_translator,
                answer,
                self.agent_config.output_translation.language,
            )
        state["answer"] = answer
        state["user_query"] = ""
        return state

    def route(self, state: State, **kwargs):
        """route the messages"""
        logger.debug(f"[DATA_summarizer-ROUTE]-state: {state}")
        if len(state["data_content_list"]) == 0:
            return "extract_data"
        if state["format_instruction"] != "":
            return "summarize"
        if state["user_query"] != "":
            return "generate_answer"


def init_graph(
    agent_config_dict: dict, save_graph_path: Optional[str] = None
) -> tuple[CompiledStateGraph, Agent]:
    """initialize the graph"""
    agent_config = AgentConfig(**agent_config_dict)
    # init agent to handle graph nodes
    agent = Agent(agent_config)

    # build the graph
    builder = StateGraph(State)
    # add the nodes
    builder.add_node("extract_data", agent.node_extract_data)
    builder.add_node("summarize", agent.node_summarize)
    builder.add_node("generate_answer", agent.node_generate_answer)
    # add the edges
    builder.add_conditional_edges(
        START,
        agent.route,
        {
            "extract_data": "extract_data",
            "summarize": "summarize",
            "generate_answer": "generate_answer",
        },
    )

    builder.add_edge("extract_data", "summarize")
    builder.add_edge("summarize", END)
    builder.add_edge("generate_answer", END)

    graph = builder.compile(checkpointer=MemorySaver())
    image = graph.get_graph().draw_mermaid_png()
    try:
        if save_graph_path is not None:
            with open(save_graph_path, "wb") as f:
                f.write(image)
    except Exception as e:
        logger.error(f"Failed to save graph: {e}")
    return graph, agent
