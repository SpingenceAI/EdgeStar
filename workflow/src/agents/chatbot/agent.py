"""CHATBOT AGENT"""

from typing import TypedDict, Optional

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


class State(TypedDict):
    """state of the chatbot"""

    messages: list[BaseMessage]


class AgentConfig(LLMConfig):
    """configuration of the chatbot"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.model_type is None:  # default to chat model
            self.model_type = LLMModelType.CHAT.value


class Agent:
    """Agent for chatbot"""

    def __init__(self, agent_config: AgentConfig):
        _system_prompt = agent_config.system_prompt or ""
        _system_prompt_tail = agent_config.system_prompt_tail or ""
        self.system_prompt = _system_prompt + _system_prompt_tail
        self.llm = llm_factory(agent_config)
        self.tools_map = tools_factory(agent_config.tools)

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

    def chat(self, state: State, **kwargs):
        """chat with the user"""
        messages = state["messages"]
        self.format_messages(messages)
        self.insert_system_prompt(messages)
        # invoke the llm
        response = self.llm.invoke(messages)
        # append tool messages to messages
        tool_call_response = self.call_tools(response, messages)
        messages.append(tool_call_response)
        # set it back to state
        state["messages"] = messages
        return state

    def call_tools(self, response: AIMessage, messages: list[BaseMessage]):
        """call tools

        Args:
            tool_calls: list[dict]: the tool calls
                tool_call = {
                    "name": str,
                    "args": dict,
                    "id": str,
                }
        Returns:
            list[ToolMessage]: the tool messages

        1. execute the tool calls
        2. append the tool results to the prompt
        3. back to chat node
        """

        logger.debug(f"response: {response}")
        messages.append(response)
        if response.tool_calls:
            for tool_call in response.tool_calls:
                name = tool_call["name"]
                args = tool_call["args"]
                callable_function = self.tools_map[name]
                tool_call_response = callable_function(**args)
                messages.append(
                    ToolMessage(
                        tool_call_id=tool_call["id"], content=tool_call_response
                    )
                )
            response = self.llm.invoke(messages)
        return response


def init_graph(agent_config_dict: dict, save_graph_path: Optional[str] = None) -> tuple[CompiledStateGraph, Agent]:
    """initialize the graph"""
    agent_config = AgentConfig(**agent_config_dict)
    # init agent to handle graph nodes
    agent = Agent(agent_config)

    # build graph
    builder = StateGraph(State)
    # add nodes
    builder.add_node("chat", agent.chat)
    # add edges
    builder.add_edge(START, "chat")  # add node name
    builder.add_edge("chat", END)  # add node name
    graph = builder.compile(checkpointer=MemorySaver())
    # save graph diagram
    image = graph.get_graph().draw_mermaid_png()
    if save_graph_path is not None:
        with open(save_graph_path, "wb") as f:
            f.write(image)
    return graph, agent


def save_graph_png(graph, save_path):
    """save graph to png file"""
    with open(save_path, "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())