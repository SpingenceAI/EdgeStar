"""MEETING RECAP AGENT"""

import os
from typing import TypedDict, Optional
from pydantic import BaseModel
from loguru import logger

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.messages import (
    BaseMessage,
    ToolMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
)


from src.llm.config import LLMConfig, LLMModelType
from src.llm.lc import llm_factory, tools_factory
from src.llm.config import LLMModelType
from src.agents.meeting_recap.utils import transcribe_audio, STTConfig, convert_language


class State(TypedDict):
    """state of the chatbot"""

    file_path: str
    transcription: str
    summary: str
    format_instruction: str


class AgentConfig(BaseModel):
    """configuration of the chatbot"""
    chat_llm: LLMConfig
    stt_config: STTConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stt_config = STTConfig(**kwargs["stt_config"])


TRANSCRIPT_PROMPT = """
會議逐字稿以<transcription>標籤包住。
<transcription>
`{transcription}`
</transcription>
回答的內容需要參考上述逐字稿的內容，不要私自添加逐字稿以外的內容。
您是一位專業的文件整理人員，需要整理出針對會議逐字稿的內容，請根據<format>標籤的要求進行整理。
不許額外加入逐字稿以外的內容。
<format>
{format}
</format>
"""

DEFAULT_SUMMARY_FORMAT = """
需要整理出以下內容，列出每個討論項目與每個討論項目的詳細內容。
討論項目：
- 討論過程中的詳細內容與數據
- 討論結果
- 下一步的行動項目
"""


class Agent:
    """Agent for chatbot"""

    def __init__(self, agent_config: AgentConfig):
        self.llm = llm_factory(agent_config.chat_llm)
        self.stt_config = agent_config.stt_config

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

    def transcribe(self, state: State, **kwargs):
        """transcribe the audio file"""
        logger.debug(f"[MEETING RECAP-TRANSCRIBE]-state: {state}")
        transcription = state.get("transcription", None)
        if transcription is None:
            file_path = state["file_path"]
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"file not found: {file_path}")
            transcription = transcribe_audio(file_path, self.stt_config)
            state["transcription"] = transcription
        return state

    def summarize(self, state: State, **kwargs):
        """summarize the meeting"""
        logger.debug(f"[MEETING RECAP-SUMMARIZE]-state: {state}")
        transcription = state.get("transcription", None)
        if transcription is None:
            raise ValueError("transcription is not found")
        format_instruction = (
            state.get("format_instruction", None) or DEFAULT_SUMMARY_FORMAT
        )
        messages = [
            HumanMessage(
                content=TRANSCRIPT_PROMPT.format(
                    transcription=transcription, format=format_instruction
                )
            ),
        ]
        response = self.llm.invoke(messages)
        response.content = convert_language(response.content, "s2twp")
        state["summary"] = response.content
        return state


def init_graph(agent_config_dict: dict, save_graph_path: Optional[str] = None) -> tuple[CompiledStateGraph, Agent]:
    """initialize the graph"""
    agent_config = AgentConfig(**agent_config_dict)
    # init agent to handle graph nodes
    agent = Agent(agent_config)

    # build graph
    builder = StateGraph(State)
    # add nodes
    builder.add_node("transcribe", agent.transcribe)
    builder.add_node("summarize", agent.summarize)
    # add edges
    builder.add_edge(START, "transcribe")  # add node name
    builder.add_edge("transcribe", "summarize")  # add node name
    builder.add_edge("summarize", END)  # add node name
    graph = builder.compile(checkpointer=MemorySaver())
    image = graph.get_graph().draw_mermaid_png()
    if save_graph_path is not None:
        with open(save_graph_path, "wb") as f:
            f.write(image)
    return graph, agent


def save_graph_png(graph, save_path):
    """save graph to png file"""
    with open(save_path, "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

