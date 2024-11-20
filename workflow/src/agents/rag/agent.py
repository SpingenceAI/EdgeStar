"""Chat with file use self rag"""

from typing import TypedDict, Literal, Optional


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
from src.retriever.retriever import Retriever, RetrieverConfig
from src.agents.rag import advance


class TranslationConfig(BaseModel):
    """Translation config"""

    enable: bool = False
    llm: Optional[LLMConfig] = None
    language: str = "zh-tw"


class AgentConfig(BaseModel):
    """Agent config"""

    chat_llm: LLMConfig
    retriever: RetrieverConfig
    input_translation: Optional[TranslationConfig] = None
    output_translation: Optional[TranslationConfig] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.chat_llm.model_type is None:
            self.chat_llm.model_type = LLMModelType.CHAT
        if self.retriever.embedding.model_type is None:
            self.retriever.embedding.model_type = LLMModelType.EMBEDDING


class State(TypedDict):
    """state of the chatbot"""

    messages: list[BaseMessage]
    # data_path: str
    data_list: list[str]
    relevant_docs: list[Document]
    user_query: str
    answer: str

    # TODO: loop times


DEFAULT_SYSTEM_PROMPT = """
You are a helpful assistant, who can answer questions about the file.
<CONTEXT>
{context}
</CONTEXT>
Please answer the question based on the context, if you are not sure, you can say "I don't know" or "I don't know the answer".
<QUESTION>
{question}
</QUESTION>
ANSWER:
"""

TRANSLATION_PROMPT = """
You are a helpful assistant, who can translate the text to {language}.
<TEXT>
{text}
</TEXT>
TRANSLATION:
"""


class Agent:
    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config
        self.custom_system_prompt = self.agent_config.chat_llm.system_prompt
        self.system_prompt_tail = self.agent_config.chat_llm.system_prompt_tail
        self.chat_llm = llm_factory(agent_config.chat_llm)
        self.chat_llm_json = llm_factory(agent_config.chat_llm, json_mode=True)
        self.retriever = Retriever(retriever_config=agent_config.retriever)
        self.input_translator = None
        self.output_translator = None
        if self.agent_config.input_translation:
            self.input_translator = llm_factory(self.agent_config.input_translation.llm)
        if self.agent_config.output_translation:
            self.output_translator = llm_factory(
                self.agent_config.output_translation.llm
            )

    def translate(self, llm, text: str, language: str) -> str:
        """translate text to language"""
        messages = [
            {
                "role": "system",
                "content": "you are a professional translator please translate the text to {language} without giving any explanation.".format(
                    language=language
                ),
            },
            {"role": "user", "content": text},
        ]
        response = llm.invoke(messages)
        return response.content

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

    def edge_has_user_query(self, state: State, **kwargs) -> Literal["YES", "NO"]:
        """Get user query from messages
        if messages is empty, ingest data
        if messages is not empty, get user query from the last message
        format the query to be a question
        """
        # TODO: 1. query expansion , 2. rephasing chat history to one question
        logger.debug(f"[chat-file] ENTER : EDGE_HAS_USER_QUERY")
        if len(state["messages"]) == 0:
            return "NO"
        return "YES"

    def node_get_user_query(self, state: State, **kwargs):
        """
        get user query from messages
        """
        logger.debug(f"[chat-file] ENTER : NODE_GET_USER_QUERY")
        messages = self.format_messages(state["messages"])
        user_query = messages[-1].content
        if self.input_translator is not None:
            user_query = self.translate(
                self.input_translator,
                user_query,
                self.agent_config.input_translation.language,
            )
        state["user_query"] = user_query
        return state

    def node_ingest_data(self, state: State, **kwargs):
        """
        ingest data into retriever
        """
        logger.debug(f"[chat-file] ENTER : NODE_INGEST_DATA")
        self.retriever.insert_data_list(state["data_list"])
        return state

    def node_retrieve(self, state: State, **kwargs):
        """
        Retrieve relevant docs from retriever
        """
        # TODO: 1. query expansion , 2. rephasing chat history to one question 3. rerank relevant docs
        logger.debug(f"[chat-file] ENTER : NODE_RETRIEVE")
        query = state["user_query"]
        relevant_docs = self.retriever.retrieve_data(query)
        # logger.error(f"relevant_docs: {relevant_docs}")
        state["relevant_docs"] = relevant_docs
        return state

    def node_grade_documents(self, state: State, **kwargs):
        """Determines whether the retrieved documents are relevant to the user query
        will filtered out irrelevant docs
        """
        logger.debug(f"[chat-file] ENTER : NODE_GRADE_DOCUMENTS")
        relevant_docs = state["relevant_docs"]
        user_query = state["user_query"]
        filtered_docs = []
        for doc in relevant_docs:
            if advance.grade_retrieved_docs(
                doc, user_query, self.chat_llm_json, retries=3
            ):
                filtered_docs.append(doc)
        logger.debug(
            f"Remove {len(relevant_docs) - len(filtered_docs)} irrelevant docs,len {len(filtered_docs)}"
        )
        state["relevant_docs"] = filtered_docs
        return state

    def node_transform_query(self, state: State, **kwargs):
        """
        transform query to a new question
        """
        # TODO: add transform query
        logger.debug(f"[chat-file] ENTER : NODE_TRANSFORM_QUERY")
        user_query = state["user_query"]
        template = f"""You a question re-writer that converts an input question to a better version that is optimized \n 
        for vectorstore retrieval. Look at the initial and formulate an improved question. \n
        Here is the initial question: \n\n {user_query}. Improved question with no preamble: \n """
        messages = [

        ]
        response = self.chat_llm.invoke({"generation": template})
        new_query = response.content
        logger.warning(f"refrase user query to {new_query}")
        state["user_query"] = new_query

        return state

    def node_generate_answer(self, state: State, **kwargs):
        """generate answer"""
        logger.debug(f"[chat-file] ENTER : NODE_GENERATE_ANSWER")
        user_query = state["user_query"]
        relevant_docs = state["relevant_docs"]
        prompt = DEFAULT_SYSTEM_PROMPT.format(
            context="\n\n".join([x.page_content for x in relevant_docs]),
            question=user_query,
        )
        answer = self.chat_llm.invoke(prompt)
        state["answer"] = answer.content
        return state

    def edge_decide_to_generate(self, state: State, **kwargs) -> Literal["YES", "NO"]:
        """
        Determines whether to generate an answer or re-generate a question

        """
        logger.debug(f"[chat-file] ENTER : EDGE_DECIDE_TO_GENERATE")
        if state["relevant_docs"] is None:
            return "NO"
        return "YES"

    def edge_grade_generation_v_documents_and_question(
        self, state: State, **kwargs
    ) -> Literal["Answer is correct", "Answer is incorrect", "Hallucination"]:
        """grade generation v documents and question"""
        logger.debug(
            f"[chat-file] ENTER : EDGE_GRADE_GENERATION_V_DOCUMENTS_AND_QUESTION"
        )
        user_query = state["user_query"]
        answer = state["answer"]
        doc = "\n".join([x.page_content for x in state["relevant_docs"]])

        # if not advance.grade_hallucination(
        #     doc=doc,
        #     generation=answer,
        #     llm=self.chat_llm_json,
        # ):  # no hallucination
        if True:
            if advance.grade_answer(
                question=user_query,
                generation=answer,
                llm=self.chat_llm_json,
            ):  # answer is correct
                messages = state["messages"]
                messages.append(AIMessage(content=answer))
                state["messages"] = messages
                logger.warning(f"Answer is correct {answer},doc {doc}")
                return "Answer is correct"
            else:  # answer is incorrect
                logger.warning(f"Answer is incorrect {answer}")
                return "Answer is incorrect"
        else:  # hallucination
            logger.warning(f"Hallucination {answer}")
            return "Hallucination"

    def node_append_answer(self, state: State, **kwargs):
        """append answer to messages"""
        logger.debug(f"[chat-file] ENTER : NODE_APPEND_ANSWER")
        messages = state["messages"]
        relevant_docs = state["relevant_docs"]
        if len(relevant_docs) > 0:

            if self.output_translator is not None:
                logger.info(
                    f"Translate answer to {self.agent_config.output_translation.language}"
                )
                answer_str = self.translate(
                    self.output_translator,
                    state["answer"],
                    self.agent_config.output_translation.language,
                )
            else:
                answer_str = state["answer"]
            messages.append(AIMessage(content=answer_str))
        else:
            messages.append(AIMessage(content="I don't know the answer."))
        state["messages"] = messages
        return state


def init_graph(
    agent_config: dict, save_graph_path: Optional[str] = None
) -> tuple[CompiledStateGraph, Agent]:
    """initialize the graph"""
    agent_config = AgentConfig(**agent_config)
    logger.debug(f"Agent Config For Graph: {agent_config}")
    # init agent to handle graph nodes
    agent = Agent(agent_config)

    # build graph
    builder = StateGraph(State)
    # add nodes
    builder.add_node("node_get_user_query", agent.node_get_user_query)
    builder.add_node("node_ingest_data", agent.node_ingest_data)
    builder.add_node("node_retrieve", agent.node_retrieve)
    builder.add_node("node_grade_documents", agent.node_grade_documents)
    builder.add_node("node_transform_query", agent.node_transform_query)
    builder.add_node("node_generate_answer", agent.node_generate_answer)
    builder.add_node("node_append_answer", agent.node_append_answer)
    # add edges
    builder.add_conditional_edges(
        START,
        agent.edge_has_user_query,
        {
            "YES": "node_get_user_query",
            "NO": "node_ingest_data",
        },
    )
    builder.add_edge("node_ingest_data", END)
    builder.add_edge("node_get_user_query", "node_retrieve")
    builder.add_edge("node_retrieve", "node_grade_documents")

    builder.add_conditional_edges(
        "node_grade_documents",
        agent.edge_decide_to_generate,
        {
            "YES": "node_generate_answer",
            "NO": "node_transform_query",
        },
    )

    builder.add_conditional_edges(
        "node_generate_answer",
        agent.edge_grade_generation_v_documents_and_question,
        {
            "Answer is correct": "node_append_answer",
            "Answer is incorrect": "node_transform_query",
            "Hallucination": "node_generate_answer",
        },
    )
    builder.add_edge("node_append_answer", END)
    graph = builder.compile(checkpointer=MemorySaver())

    # save graph diagram
    if save_graph_path is not None:
        image = graph.get_graph().draw_mermaid_png()
        with open(save_graph_path, "wb") as f:
            f.write(image)
    return graph, agent
