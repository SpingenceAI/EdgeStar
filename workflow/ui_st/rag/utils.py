import sys
import os
sys.path.append('../../')
from src.agents.rag.agent import init_graph,AgentConfig
from src.retriever.retriever import Retriever,list_knowledge_bases,RetrieverConfig
import env


def create_knowledge_base(kb_name):
    documents_folder = env.get_documents_path(kb_name)
    document_folder_path = os.path.join(documents_folder,kb_name)
    os.makedirs(document_folder_path,exist_ok=True)

def list_kb()->list[str]:
    documents_path = env.get_documents_path()
    return list_knowledge_bases(documents_path)

def get_retriever(kb_name):
    retriver_config_dict = env.get_retriever_config(kb_name)
    return Retriever(RetrieverConfig(**retriver_config_dict))

def add_documents(kb_name,files):
    retriver = get_retriever(kb_name)
    retriver.insert_data_list(files)

def list_documents(kb_name):
    documents_folder = env.get_documents_path(kb_name)
    documents_folder_path = os.path.join(documents_folder,kb_name)
    return os.listdir(documents_folder_path)

def get_graph(kb_name):
    config = env.get_agent_config(kb_name)
    graph,_ = init_graph(config)
    return graph





def get_st_session_id()->str:
    from streamlit.runtime import get_instance
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    runtime = get_instance()
    session_id = get_script_run_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)
    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    return session_info.session.id