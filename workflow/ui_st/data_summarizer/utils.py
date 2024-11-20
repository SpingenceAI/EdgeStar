import sys
import os

sys.path.append("../../")
from src.agents.data_summarizer.agent import init_graph
import env


def get_graph():
    config = env.get_agent_config()
    graph, _ = init_graph(config)
    return graph


def get_st_session_id() -> str:
    from streamlit.runtime import get_instance
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_info.session.id
