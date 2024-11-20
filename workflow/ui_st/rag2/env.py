# TODO: 改用 configs/agents.yml

import os

from dotenv import load_dotenv

load_dotenv("../../.env.playground")

STATIC_FOLDER = os.path.abspath("../static")

ES_LOGO_PATH = os.path.join(STATIC_FOLDER, "ES_LOGO.png")
SP_ICON_PATH = os.path.join(STATIC_FOLDER, "SP_ICON.png")
SP_LOGO_PATH = os.path.join(STATIC_FOLDER, "SP_LOGO.png")
AI_ICON_PATH = os.path.join(STATIC_FOLDER, "AI_ICON.png")
USER_ICON_PATH = os.path.join(STATIC_FOLDER, "USER_ICON.png")


DATA_MOUNT_PATH = "./data"
TEMP_FOLDER_PATH = "./temp"
os.makedirs(TEMP_FOLDER_PATH, exist_ok=True)
VECTOR_DB_PATH = os.path.join(DATA_MOUNT_PATH, "vector_store")
os.makedirs(VECTOR_DB_PATH, exist_ok=True)
SQLITE_DB_PATH = os.path.join(DATA_MOUNT_PATH, "sqlite_db.db")
DOCUMENTS_PATH = os.path.join(DATA_MOUNT_PATH, "documents")
os.makedirs(DOCUMENTS_PATH, exist_ok=True)
from dotenv import load_dotenv
import os

load_dotenv("../../.env.playground")

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_MODEL = os.environ["OLLAMA_MODEL"]

EMBEDDING_CONFIG = {
    "provider": "ollama",
    "model": OLLAMA_MODEL,
    "base_url": OLLAMA_BASE_URL,
    "model_type": "embedding",
}
VECTOR_STORE_CONFIG = {
    "provider": "chroma",
    "name": "",
    "connection_string": VECTOR_DB_PATH,
}


def get_retriever_config(kb_name):
    if kb_name is None or kb_name == "":
        raise ValueError("kb_name is required")
    config = {
        "vector_store": VECTOR_STORE_CONFIG,
        "embedding": EMBEDDING_CONFIG,
        "save_folder_path": DOCUMENTS_PATH,
        "sqlite_db_path": SQLITE_DB_PATH,
        "use_bm25": False,
        "top_k": 5,
        "bm25_weight": 0.3,
        "chunk_size": 1024,
        "chunk_overlap": 128,
    }
    config["vector_store"]["name"] = kb_name
    return config


def get_agent_config(kb_name):
    config = {
        "retriever": get_retriever_config(kb_name),
        "chat_llm": {
            "provider": "ollama",
            "model": OLLAMA_MODEL,
            "base_url": OLLAMA_BASE_URL,
            "model_type": "chat",
        },
        # "output_translation": {
        #     "llm": {
        #         "provider": "ollama",
        #         "model": OLLAMA_MODEL,
        #         "base_url": OLLAMA_BASE_URL,
        #         "model_type": "chat",
        #     },
        #     "language": "japanese",
        # },
    }
    return config


def get_chatbot_agent_config():
    agent_config = {
        "provider": "ollama",
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_BASE_URL,
        "temperature": 0,
        "tools": [
            # "get_current_weather",
            "get_current_time",
            "web_search",
        ],
        "system_prompt": "You are a helpful assistant",
        "system_prompt_tail": "日本語でお答えください!日本語でお答えください!日本語でお答えください!",
    }
    return agent_config