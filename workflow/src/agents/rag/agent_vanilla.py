"""Chat with file only use retriever"""

from typing import TypedDict


from loguru import logger
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage
from pydantic import BaseModel

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.documents import Document


from src.llm.config import LLMConfig, LLMModelType
from src.llm.lc import llm_factory
from src.retriever.retriever import Retriever
from src.retriever.vector_store import VectorStoreConfig, VectorStoreProvider


class RetrieverConfig(BaseModel):
    """Retriever config"""

    vector_store: VectorStoreConfig = VectorStoreConfig(
        provider=VectorStoreProvider.Memory,
        name="chat_file",
        connection_string="./chroma_db",
    )
    top_k: int = 2
    use_bm25: bool = True
    bm25_weight: float = 0.4


class SplitterConfig(BaseModel):
    """Splitter config"""

    chunk_size: int = 1000
    chunk_overlap: int = 128


class AgentConfig(BaseModel):
    """Agent config"""

    chat_llm: LLMConfig
    embedding_llm: LLMConfig
    retriever: RetrieverConfig = RetrieverConfig()
    splitter: SplitterConfig = SplitterConfig()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.chat_llm.model_type is None:
            self.chat_llm.model_type = LLMModelType.CHAT
        if self.embedding_llm.model_type is None:
            self.embedding_llm.model_type = LLMModelType.EMBEDDING


class State(TypedDict):
    """state of the chatbot"""

    messages: list[BaseMessage]
    data_path: str
    relevant_docs: list[Document]


DEFAULT_SYSTEM_PROMPT = """
You are a helpful assistant, who can answer questions about the file.
<CONTEXT>
{context}
</CONTEXT>
Please answer the question based on the context, if you are not sure, you can say "I don't know" or "I don't know the answer".
"""




class Agent:
    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config
        self.custom_system_prompt = self.agent_config.chat_llm.system_prompt
        self.system_prompt_tail = self.agent_config.chat_llm.system_prompt_tail
        self.chat_llm = llm_factory(agent_config.chat_llm)
        self.chat_llm_json = llm_factory(agent_config.chat_llm,json_mode=True)
        self.retriever = Retriever(
            self.agent_config.retriever.vector_store,
            self.agent_config.embedding_llm,
            top_k=self.agent_config.retriever.top_k,
            chunk_size=self.agent_config.splitter.chunk_size,
            chunk_overlap=self.agent_config.splitter.chunk_overlap,
            use_bm25=self.agent_config.retriever.use_bm25,
            bm25_weight=self.agent_config.retriever.bm25_weight,
        )

    def format_messages(self, messages: list):
        """format messages"""
        for idx in range(len(messages)):

            if isinstance(messages[idx], dict):
                if messages[idx]["role"] == "user":
                    messages[idx] = HumanMessage(content=messages[idx]["content"])
                elif messages[idx]["role"] == "ai":
                    messages[idx] = AIMessage(content=messages[idx]["content"])
                elif messages[idx]["role"] == "system":
                    messages[idx] = SystemMessage(content=messages[idx]["content"])
        return messages

    def retrieve_relevant_docs(self, queries: list[str]):
        """retrieve relevant docs"""
        # TODO: 1. query expansion , 2. rephasing chat history to one question 3. rerank relevant docs
        relevant_docs = []
        for query in queries:
            relevant_docs.extend(self.retriever.retrieve_data(query))
        return relevant_docs

    def get_user_query(self, messages: list[BaseMessage]) -> list[str]:
        """get user query"""
        # TODO: 1. query expansion , 2. rephasing chat history to one question
        return [messages[-1].content]

    def chat_node(self, state: State, **kwargs):
        """chat with file"""
        if len(state["messages"]) == 0:
            # insert data to retriever
            self.retriever.insert_data_list([state["data_path"]])
            return state
        messages = self.format_messages(state["messages"])
        # get user query
        queries = self.get_user_query(messages)
        # retrieve docs
        relevant_docs = self.retrieve_relevant_docs(queries)
        state["relevant_docs"] = relevant_docs
        # setup system prompt
        messages = self.insert_system_prompt(messages, relevant_docs)
        # chat with llm
        response = self.chat_llm.invoke(messages)
        state["messages"].append(response)
        return state

    def insert_system_prompt(
        self, messages: list[BaseMessage], relevant_docs: list[Document]
    ):
        """insert system prompt into messages"""
        system_prompt = DEFAULT_SYSTEM_PROMPT.format(
            context="\n".join([doc.page_content for doc in relevant_docs])
        )
        if self.custom_system_prompt:
            system_prompt = f"{self.custom_system_prompt}\n{system_prompt}"
        if self.system_prompt_tail:
            system_prompt = f"{system_prompt}\n{self.system_prompt_tail}"
        if messages[0].type == "system":
            messages[0].content = system_prompt
        else:
            messages.insert(0, SystemMessage(content=system_prompt))
        return messages


def init_graph(agent_config: dict) -> tuple[CompiledStateGraph, Agent]:
    """initialize the graph"""
    agent_config = AgentConfig(**agent_config)
    logger.debug(f"Agent Config For Graph: {agent_config}")
    # init agent to handle graph nodes
    agent = Agent(agent_config)

    # build graph
    builder = StateGraph(State)
    # add nodes
    builder.add_node("chat", agent.chat_node)
    # add edges
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    graph = builder.compile(checkpointer=MemorySaver())
    return graph, agent
