import os

STATIC_FOLDER = os.path.abspath('../static')

ES_LOGO_PATH = os.path.join(STATIC_FOLDER, "ES_LOGO.png")
SP_ICON_PATH = os.path.join(STATIC_FOLDER, "SP_ICON.png")
SP_LOGO_PATH = os.path.join(STATIC_FOLDER, "SP_LOGO.png")
AI_ICON_PATH = os.path.join(STATIC_FOLDER, "AI_ICON.png")
USER_ICON_PATH = os.path.join(STATIC_FOLDER, "USER_ICON.png")
from dotenv import load_dotenv
import os
from envyaml import EnvYAML
from loguru import logger




def get_agent_config():
    env_path = os.environ["ENV_PATH"]
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"File {env_path} not found")
    load_dotenv(env_path)
    agent_config_path = os.environ["AGENTS_CONFIG_PATH"]
    if not os.path.exists(agent_config_path):
        raise FileNotFoundError(f"File {agent_config_path} not found")
    env = EnvYAML(agent_config_path,strict=False)
    if "data_summarizer" not in env:
        raise ValueError("'data_summarizer' config not found in agents.yml")
    return env["data_summarizer"]
