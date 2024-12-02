import os

os.makedirs("logs", exist_ok=True)
from dotenv import load_dotenv
from envyaml import EnvYAML


def load_agents_config(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"AGENTS_CONFIG_PATH not found: {path}")
    print("LOADING AGENTS CONFIG FROM", path)
    return EnvYAML(path, strict=False)


def load_env():
    ENV_PATH = os.environ["ENV_PATH"]
    if not os.path.exists(ENV_PATH):
        raise FileNotFoundError(f"ENV_PATH not found: {ENV_PATH}")
    # LOAD ENV
    print("LOADING ENV FROM", ENV_PATH)
    load_dotenv(ENV_PATH)

    MAIL_ENV_PATH = os.environ["MAIL_ENV_PATH"]
    if not os.path.exists(MAIL_ENV_PATH):
        raise FileNotFoundError(f"MAIL_ENV_PATH not found: {MAIL_ENV_PATH}")
    print("LOADING MAIL ENV FROM", MAIL_ENV_PATH)
    load_dotenv(MAIL_ENV_PATH)

    AGENTS_CONFIG_PATH = os.environ["AGENTS_CONFIG_PATH"]
    if not os.path.exists(AGENTS_CONFIG_PATH):
        raise FileNotFoundError(f"AGENTS_CONFIG_PATH not found: {AGENTS_CONFIG_PATH}")

    DATA_MOUNT_PATH = os.environ["DATA_MOUNT_PATH"]
    if not os.path.exists(DATA_MOUNT_PATH):
        raise FileNotFoundError(f"DATA_MOUNT_PATH not found: {DATA_MOUNT_PATH}")
    

    return ENV_PATH, MAIL_ENV_PATH, AGENTS_CONFIG_PATH, DATA_MOUNT_PATH


ENV_PATH, MAIL_ENV_PATH, AGENTS_CONFIG_PATH, DATA_MOUNT_PATH = load_env()
AGENTS_CONFIG = load_agents_config(AGENTS_CONFIG_PATH)

CHATBOT_CONFIG = AGENTS_CONFIG["chatbot"]
print("CHATBOT_CONFIG",CHATBOT_CONFIG)
DATA_SUMMARIZER_CONFIG = AGENTS_CONFIG["data_summarizer"]
print("DATA_SUMMARIZER_CONFIG",DATA_SUMMARIZER_CONFIG)
MEETING_RECAP_CONFIG = AGENTS_CONFIG["meeting_recap"]
print("MEETING_RECAP_CONFIG",MEETING_RECAP_CONFIG)

WEB_SEARCH_CONFIG = AGENTS_CONFIG["web_search"]
print("WEB_SEARCH_CONFIG",WEB_SEARCH_CONFIG)


DATA_FOLDER = DATA_MOUNT_PATH
MAIL_PROVIDER = os.environ["MAIL_PROVIDER"]