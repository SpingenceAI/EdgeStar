import os

STATIC_FOLDER = os.path.abspath("../static")

ES_LOGO_PATH = os.path.join(STATIC_FOLDER, "ES_LOGO.png")
SP_ICON_PATH = os.path.join(STATIC_FOLDER, "SP_ICON.png")
SP_LOGO_PATH = os.path.join(STATIC_FOLDER, "SP_LOGO.png")
AI_ICON_PATH = os.path.join(STATIC_FOLDER, "AI_ICON.png")
USER_ICON_PATH = os.path.join(STATIC_FOLDER, "USER_ICON.png")
TEMP_FOLDER_PATH = os.path.join("/temp")
os.makedirs(TEMP_FOLDER_PATH,exist_ok=True)

from dotenv import load_dotenv
import os
from envyaml import EnvYAML

def get_agent_config(kb_name:str|None=None):
    env_path = os.environ["ENV_PATH"]
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"File {env_path} not found")
    load_dotenv(env_path)
    agent_config_path = os.environ["AGENTS_CONFIG_PATH"]
    if not os.path.exists(agent_config_path):
        raise FileNotFoundError(f"File {agent_config_path} not found")
    env = EnvYAML(agent_config_path,strict=False)
    if "rag" not in env:
        raise ValueError("'rag' config not found in agents.yml")
    agent_config = env["rag"]
    if kb_name is not None:
        agent_config["retriever"]["vector_store"]["name"] = kb_name

    # DATA MOUNT PATH
    DATA_MOUNT_PATH = os.environ["DATA_MOUNT_PATH"]
    TEMP_FOLDER_PATH = os.path.join(DATA_MOUNT_PATH, "temp")
    os.makedirs(TEMP_FOLDER_PATH, exist_ok=True)

    return agent_config

def get_documents_path(kb_name:str|None=None):
    agent_config = get_agent_config(kb_name)
    return agent_config["retriever"]["save_folder_path"]



def get_retriever_config(kb_name):
    if kb_name is None or kb_name == "":
        raise ValueError("kb_name is required")
    agent_config = get_agent_config(kb_name)
    return agent_config["retriever"]
