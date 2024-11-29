"""Search Agent"""

from datetime import datetime
import json
from typing import List, TypedDict
from loguru import logger
import os

from pydantic import BaseModel
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.memory import MemorySaver
from src.llm.config import LLMConfig, LLMModelType
from src.llm.lc import llm_factory, tools_factory

from src.agents.web_search import data_schema
from src.agents.web_search import prompts
from src.agents.web_search import search as search_api
from src.agents.web_search import scrapper as scrapper_api


class AgentConfig(BaseModel):
    """Agent config"""

    chat_llm: LLMConfig
    search_engine: search_api.SearchEngineConfig
    search_result_limit: int = 3
    is_scrap_url: bool = False
    is_concise_step_results: bool = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.chat_llm.model_type is None:
            self.chat_llm.model_type = LLMModelType.CHAT


class State(TypedDict):
    """State of the agent"""

    user_query: str
    answer: str


def get_current_datetime() -> str:
    """Get the current datetime"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_search_plan(user_query: str, json_llm) -> List[data_schema.SearchPlanStep]:
    """Generate a search plan for the user query"""
    # return [data_schema.SearchPlanStep(id=0, step=user_query, dependencies=[])]

    prompt = prompts.SEARCH_PLAN_PROMPT.format(
        user_query=user_query, current_datetime=get_current_datetime()
    )
    response = json_llm.invoke(prompt)
    response_json = json.loads(response.content)
    steps = [data_schema.SearchPlanStep(**x) for x in response_json["steps"]]
    return steps


def generate_search_queries(
    user_query: str, prev_steps_context: str, current_step: str, json_llm
) -> List[data_schema.SearchQuery]:
    """Generate search queries for the user query
    ARGS:
        user_query:str, user original query
        prev_steps_context:str, context from previous steps results
        current_step:str, the current step to generate search queries for
        json_llm:ChatOllama, json mode llm
    """
    generate_search_query_prompt = prompts.SEARCH_QUERY_PROMPT.format(
        current_datetime=get_current_datetime(),
        user_query=user_query,
        prev_steps_context=prev_steps_context,
        current_step=current_step,
    )
    response = json_llm.invoke(generate_search_query_prompt)
    try:
        response_json = json.loads(response.content)
        return [data_schema.SearchQuery(**x) for x in response_json["queries"]]
    except Exception as e:
        logger.error(
            f"Error in generate_search_queries: {e}, response={response.content}"
        )
        return []


def scrap_url(url: str) -> tuple[str, str]:
    """Scrape the url
    ARGS:
        url:str, the url to scrape
    RETURNS:
        html:str, the html content of the url
        body:str, the body text of the url in markdown format
    """
    html, body = scrapper_api.scrape_html_and_body(url)
    return html, body


def remove_unrelated_results(web_page_content: str, user_query: str, json_llm) -> str:
    """Remove the content that is not relevant to the user query"""
    prompt = prompts.REMOVE_UNRELATED_CONTENT_PROMPT.format(
        web_page_content=web_page_content, user_query=user_query
    )
    response = json_llm.invoke(prompt)
    return response.content


def concise_content(content: str, user_query: str, llm) -> str:
    """Conceise the content"""
    prompt = prompts.CONCISE_CONTENT_PROMPT.format(
        content=content, user_query=user_query
    )
    response = llm.invoke(prompt)
    return response.content


def answer_question(user_query: str, related_content: str, llm) -> str:
    """Answer the question based on the related content"""
    prompt = prompts.ANSWER_QUESTION_PROMPT.format(
        context=related_content, question=user_query
    )
    response = llm.invoke(prompt)
    return response.content


def pro_search(
    user_query: str,
    llm,
    json_llm,
    search_engine: search_api.SearchEngineBase,
    temp_save_dir: str = None,
    is_scrap_url: bool = False,
    is_concise_step_results: bool = False,
    search_result_limit: int = 3,
) -> str:
    """Pro search
    ARGS:
        user_query:str, user original query
        llm:ChatOllama, llm
        json_llm:ChatOllama, json mode llm
    RETURNS:
        answer:str, the answer to the user query

    Steps:
        1. generate search plan
        2. for each step:
            1. generate search queries
            2. search the web for the search queries
            3. scrape the url from search results and check relevance with user query
            4. concise the content
        3. answer the question based on the related content
    """
    # SET VARIABLES
    IS_SCRAP_URL = is_scrap_url
    IS_CONCISE_STEP_RESULTS = is_concise_step_results
    SEARCH_RESULT_LIMIT = search_result_limit
    logger.debug(f"user_query: {user_query}")
    # GENERATE SEARCH PLAN
    steps = generate_search_plan(user_query, json_llm)
    logger.debug(f"generated steps: {steps}")
    if temp_save_dir:
        os.makedirs(temp_save_dir, exist_ok=True)
        with open(os.path.join(temp_save_dir, "steps.json"), "w") as f:
            f.write(json.dumps([x.dict() for x in steps], indent=4, ensure_ascii=False))
    # SEARCH FOR EACH STEP
    step_results = []
    for step in steps:
        # format previous content
        previous_content = ""
        for dependency_id in step.dependencies:
            if dependency_id < len(step_results):
                previous_content += step_results[dependency_id].results_text
        # generate search queries for search engine
        search_queries = generate_search_queries(
            user_query, previous_content, step.step, json_llm
        )

        logger.debug(f"generated search queries: {search_queries}")

        # search results for this step
        step_result_data_list = []
        for search_query in search_queries:
            # use search engine to get search results
            search_results: List[search_api.SearchResult] = search_engine.search(
                search_query.query,
                time_range=search_query.time_range,
                limit=SEARCH_RESULT_LIMIT,
                locale="zh-TW",
                categories="general",
            )
            # scrape the url from search results and check relevance with user query
            for search_result in search_results:
                logger.debug(f"search_result: {search_result}")
                search_result_data = data_schema.ResultData(**search_result.dict())
                # add additional information to search result
                if IS_SCRAP_URL:
                    html, body_markdown, body_text = scrapper_api.scrape_url(
                        search_result.url
                    )
                    search_result_data.body_text = body_text
                    search_result_data.concised_content = concise_content(
                        body_text, user_query, llm
                    )
                else:
                    search_result_data.body_text = search_result.content
                    search_result_data.concised_content = search_result.content
                step_result_data_list.append(search_result_data)

        if temp_save_dir:
            with open(os.path.join(temp_save_dir, f"results_{step.id}.json"), "w") as f:
                f.write(
                    json.dumps(
                        [x.dict() for x in step_result_data_list],
                        indent=4,
                        ensure_ascii=False,
                    )
                )
        # format step result
        step_result = data_schema.StepResult(
            id=step.id,
            step=step.step,
            results=step_result_data_list,
        )
        # concise the step result
        if IS_CONCISE_STEP_RESULTS:
            step_result.summary = concise_content(
                step_result.results_text, user_query, llm
            )
        else:
            step_result.summary = step_result.results_text
        if temp_save_dir:
            with open(
                os.path.join(temp_save_dir, f"step_result_summary_{step.id}.txt"), "w"
            ) as f:
                f.write(step_result.summary)
        step_results.append(step_result)

    # summarize all the step results
    all_results_content = "\n".join([x.summary for x in step_results])
    logger.debug(f"all_results_content: {all_results_content}")
    if temp_save_dir:
        with open(os.path.join(temp_save_dir, "all_results_content.txt"), "w") as f:
            f.write(all_results_content)

    # answer the question
    answer = answer_question(user_query, all_results_content, llm)
    logger.debug(f"answer: {answer}")

    # format the final answer with references in markdown format
    final_answer = f"{answer}\n\n### References:\n"
    for step_result in step_results:
        final_answer += f"#### Step {step_result.id}: {step_result.step}\n"
        for result in step_result.results:
            final_answer += f"- {result.reference_markdown}\n"
        final_answer += "\n\n"

    return final_answer


class Agent:
    """Agent for web search"""

    def __init__(self, agent_config: AgentConfig):
        self.agent_config = agent_config
        self.llm = llm_factory(agent_config.chat_llm)
        self.json_llm = llm_factory(agent_config.chat_llm, json_mode=True)
        self.search_engine = search_api.search_engine_factory(
            agent_config.search_engine
        )

    def node_search(self, state: State):
        """Node for search"""
        state["query"] = state["user_query"]
        answer = pro_search(
            state["user_query"],
            self.llm,
            self.json_llm,
            self.search_engine,
            temp_save_dir=None,
            is_concise_step_results=self.agent_config.is_concise_step_results,
            is_scrap_url=self.agent_config.is_scrap_url,
            search_result_limit=self.agent_config.search_result_limit,
        )
        state["answer"] = answer
        return state


def save_graph_png(graph, save_path):
    """save graph to png file"""
    with open(save_path, "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())


def init_graph(
    agent_config_dict: dict, save_graph_path: str = None
) -> tuple[CompiledStateGraph, Agent]:
    """Initialize the graph"""
    agent_config = AgentConfig(**agent_config_dict)
    agent = Agent(agent_config)

    # build graph
    builder = StateGraph(State)
    # add nodes
    builder.add_node("search", agent.node_search)
    # add edges
    builder.add_edge(START, "search")
    builder.add_edge("search", END)
    graph = builder.compile(checkpointer=MemorySaver())
    # save graph diagram
    image = graph.get_graph().draw_mermaid_png()
    if save_graph_path is not None:
        with open(save_graph_path, "wb") as f:
            f.write(image)
    return graph, agent
