"""Playground CLI v2"""

import argparse
import os
import dotenv
from envyaml import EnvYAML
import colorama
import time
import warnings

warnings.filterwarnings("ignore")


class Logger:
    def __init__(self, log_level: str):
        self.log_level = log_level

    def debug(self, text: str):
        if self.log_level == "DEBUG":
            text = f"[DEBUG] {text}"
            print(colorama.Fore.CYAN + text + colorama.Fore.RESET)

    def system(self, text: str):
        text = f"[SYSTEM] {text}"
        print(colorama.Fore.BLUE + text + colorama.Fore.RESET)

    def user(self, text: str):
        text = f"[USER] {text}"
        print(colorama.Fore.YELLOW + text + colorama.Fore.RESET)

    def ai(self, text: str):
        text = f"[AI] {text}"
        print(colorama.Fore.GREEN + text + colorama.Fore.RESET)

    def error(self, text: str):
        text = f"[ERROR] {text}"
        print(colorama.Fore.RED + text + colorama.Fore.RESET)


def read_config(config_path):
    """read config file"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return EnvYAML(config_path, strict=False)


def chatbot(agent_config, logger: Logger):
    from src.agents.chatbot.agent import init_graph

    logger.debug(f"agent_config: {agent_config}")
    graph, agent = init_graph(agent_config)
    thread_config = {"configurable": {"thread_id": str(time.time())}}
    logger.debug(f"thread_config: {thread_config}")
    state = {"messages": []}
    while True:
        input_text = input("Enter your message: ")

        if input_text.lower() == "exit":
            logger.system("Exiting chat")
            break
        state["messages"].append({"role": "user", "content": input_text})
        logger.user(input_text)
        state = graph.invoke(state, thread_config)
        logger.debug(f"state: {state}")
        logger.ai(state["messages"][-1].content)


def data_summarizer(agent_config, logger: Logger):
    from src.agents.data_summarizer.agent import init_graph

    logger.system(f"Agent Config: {agent_config}")
    graph, agent = init_graph(
        agent_config, save_graph_path="./data/playground/graph.png"
    )
    thread_config = {"configurable": {"thread_id": str(time.time())}}
    logger.debug(f"thread_config: {thread_config}")
    data_source = input("Enter the data source: ")
    state = {
        "answer": "",
        "data_source_list": [data_source],
        "summary_list": [],
        "data_content_list": [],
        "format_instruction": "",
        "user_query": "",
        "extract_error": False,
    }
    logger.system(f"Start transcribing audio from {data_source}")
    state = graph.invoke(state, thread_config)
    # logger.ai(f'{"\n".join(state["summary_list"])}')
    logger.ai(state["summary_list"])
    while True:
        action = input("Choose action: 1.user query 2. format instruction 3.exit\n")
        if action == "1":
            user_query = input("Enter your query: ")
            state["user_query"] = user_query
            state = graph.invoke(state, thread_config)
            logger.ai(state["answer"])
        elif action == "2":
            format_instruction = input("Enter your format instruction: ")
            state["format_instruction"] = format_instruction
            state = graph.invoke(state, thread_config)
            logger.ai(state["summary_list"])
        elif action.lower() == "exit":
            logger.system("Exiting data_summarizer")
            break
        elif action == "3":
            logger.system("Exiting data_summarizer")
            break
        else:
            logger.error("Invalid action")


def meeting_recap(agent_config, logger: Logger):
    from src.agents.meeting_recap.agent import init_graph

    logger.system(f"Agent Config: {agent_config}")
    graph, agent = init_graph(agent_config)
    thread_config = {"configurable": {"thread_id": str(time.time())}}
    logger.debug(f"thread_config: {thread_config}")
    file_path = input("Enter the file path: ")
    state = {"messages": [], "file_path": file_path}
    logger.system(f"Start transcribing audio from {file_path}")
    state = graph.invoke(state, thread_config)
    logger.ai(state["summary"])
    while True:
        input_text = input("Enter your format instruction: ")
        if input_text.lower() == "exit":
            logger.system("Exiting meeting recap")
            break
        state["format_instruction"] = input_text
        state = graph.invoke(state, thread_config)
        logger.ai(state["summary"])


def rag(agent_config, logger: Logger):
    from src.agents.rag.agent import init_graph
    from src.retriever.retriever import list_knowledge_bases

    # memory vector store
    if agent_config["retriever"]["vector_store"]["provider"] == "memory":
        logger.system("Use memory vector store")
        use_memory = True
    else:
        logger.system("Use file vector store")
        # choose knowledge base
        document_folder = agent_config["retriever"]["save_folder_path"]
        knowledge_base_name = input(
            f"Choose knowledge base: {list_knowledge_bases(document_folder)}"
        )
        if knowledge_base_name == "":
            knowledge_base_name = str(time.time())
        agent_config["retriever"]["vector_store"]["name"] = knowledge_base_name
        use_memory = False

    data_path = input("Enter the folder/file path or url:")
    if data_path == "" and use_memory:
        raise ValueError("Data path is required")
    data_list = []
    if data_path != "":
        if data_path.startswith("http"):
            # data is from url
            data_list = [data_path]
        else:
            # data if from local
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"File {data_path} not found")
            if os.path.isdir(data_path):
                data_list = [os.path.join(data_path, x) for x in os.listdir(data_path)]
            else:
                data_list = [data_path]

    state = {"messages": [], "data_list": data_list}
    logger.system(f"Agent Config: {agent_config}")
    graph, agent = init_graph(agent_config)
    thread_config = {"configurable": {"thread_id": str(time.time())}}
    logger.debug(f"thread_config: {thread_config}")
    # ingest data
    logger.system(f"Start ingesting file from {data_list}")
    state = graph.invoke(state, thread_config)
    logger.system("Finish ingesting file")

    # file vector store
    logger.system(f"RAG Documents:{[x.name for x in agent.retriever.list_documents()]}")

    while True:
        input_text = input("Enter your message: ")
        if input_text.lower() == "exit":
            logger.system("Exiting RAG")
            break
        state["messages"].append({"role": "user", "content": input_text})
        logger.user(input_text)
        state = graph.invoke(state, thread_config)
        logger.debug(
            f"relevant_docs: {[x.metadata['source']+':'+str(x.metadata.get('page',0)) for x in state['relevant_docs']]}"
        )
        logger.ai(state["messages"][-1].content)


def web_search(agent_config, logger: Logger):
    from src.agents.web_search.agent import init_graph

    logger.system(f"Agent Config: {agent_config}")
    graph, agent = init_graph(agent_config)
    state = {"user_query": ""}
    thread_config = {"configurable": {"thread_id": str(time.time())}}

    while True:
        input_text = input("Enter your message: ")
        if input_text.lower() == "exit":
            logger.system("Exiting WEB SEARCH")
            break
        state["user_query"] = input_text
        state = graph.invoke(state, thread_config)
        logger.ai(state["answer"])


def main(agent, config, logger: Logger):
    """main function"""
    if agent == "chatbot":
        chatbot(config, logger)
    elif agent == "data_summarizer":
        data_summarizer(config, logger)
    elif agent == "meeting_recap":
        meeting_recap(config, logger)
    elif agent == "rag":
        rag(config, logger)
    else:
        raise ValueError(f"Agent {agent} not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Playground CLI")
    parser.add_argument(
        "--agent",
        type=str,
        default="",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default="DEBUG",
        help="Log level",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="envs/.env.production",
        help="Path to the configuration file",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="configs/agents.yml",
        help="Path to the configuration file",
    )
    agent_list = ["chatbot", "meeting_recap", "rag", "data_summarizer", "web_search"]

    args = parser.parse_args()
    logger = Logger(args.log_level)

    # load env file
    env_path = args.env
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Env file not found: {env_path}")
    logger.system(f"Loading env file: {env_path}")
    dotenv.load_dotenv(env_path)
    # load config file
    config = read_config(args.config)
    # select agent
    if args.agent not in agent_list:
        input_prompt = "Please select agent"
        for i, agent in enumerate(agent_list):
            logger.user(f"{i+1}. {agent}")
        input_prompt += "\n"
        agent_selection = input(input_prompt)
        agent_selection = int(agent_selection) - 1
        if agent_selection >= 0 and agent_selection < len(agent_list):
            args.agent = agent_list[agent_selection]
        else:
            logger.error("Invalid agent id")
            exit(1)
    # run agent
    main(args.agent, config[args.agent], logger)
