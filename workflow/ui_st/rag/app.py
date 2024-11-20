import streamlit as st
import env
import os
from PIL import Image

import utils
import components

AVATAR_AI = Image.open(env.AI_ICON_PATH)
AVATAR_USER = Image.open(env.USER_ICON_PATH)
LOGO = Image.open(env.ES_LOGO_PATH)
SP_ICON = Image.open(env.SP_ICON_PATH)

# title
st.set_page_config(page_title="Spingence Rag", page_icon=SP_ICON)
TITLE_HTML = """
    <h1 style="color:#1D65A6;">Welcome to the journey of LLM</h1>
"""
st.markdown(TITLE_HTML, unsafe_allow_html=True)


def init_session_state():
    st.session_state.state = {
        "messages": [],
        "answer": "",
        "relevant_docs": [],
    }
    st.session_state.kb_name = None
    st.session_state.graph = None


if "kb_name" not in st.session_state:
    init_session_state()


# side bar
with st.sidebar:
    st.image(LOGO)
    with st.popover("Create a new knowledge base"):
        kb_name = st.text_input("Enter the name of the knowledge base")
        if st.button("Create"):
            utils.create_knowledge_base(kb_name)
            st.rerun()
    kb_list = utils.list_kb()
    st.session_state.kb_name = st.selectbox(
        "Select a knowledge base",
        kb_list,
        index=None,
    )
    if st.session_state.kb_name is not None and st.session_state.kb_name != "":
        st.session_state.graph = utils.get_graph(st.session_state.kb_name)
        upload_files = st.file_uploader(
            "Upload Document",
            type=[
                "txt",
                "csv",
                "pptx",
                "xlsx",
                "docx",
                "pdf",
            ],
            accept_multiple_files=True,
        )
        if st.button("UPLOAD"):
            with st.spinner("Uploading..."):
                save_path_list = []
                for file in upload_files:
                    save_path = os.path.join(env.TEMP_FOLDER_PATH, file.name)
                    with open(save_path, "wb") as f:
                        f.write(file.getvalue())
                    save_path_list.append(save_path)
                utils.add_documents(st.session_state.kb_name, save_path_list)
                st.rerun()
        documents = utils.list_documents(st.session_state.kb_name)
        for doc in documents:
            st.markdown(f"**{doc}**")
    components.footer()

def write_message(message,role:str=None):
    """write message to chat"""
    if role:
        content = message
    else:
        if isinstance(message, dict):
            role = message["role"]
            content = message["content"]
        else:
            if "Human" in str(type(message)).lower():
                role = "user"
            else:
                role = "assistant"
            content = message.content
    AVATAR = AVATAR_AI if role == "assistant" else AVATAR_USER
    with st.chat_message(role, avatar=AVATAR):
        st.markdown(content)


# chat history
if st.session_state.state["messages"] and st.session_state.kb_name is not None:
    collection_titile = f"Knowledge Base : {st.session_state.kb_name}"
    st.write(collection_titile)
    for msg in st.session_state.state["messages"]:
        write_message(msg)
if st.session_state.kb_name is not None and st.session_state.kb_name != "":
    user_query = st.chat_input("Enter your message")
    if user_query:
        write_message({"role":"user","content":user_query})
        st.session_state.state["messages"].append({"role":"user","content":user_query})
        session_id = utils.get_st_session_id()
        thread_config = {
            "configurable": {"thread_id": session_id}
        }
        with st.spinner("processing..."):
            st.session_state.state = st.session_state.graph.invoke(st.session_state.state,thread_config)
        last_message = st.session_state.state["messages"][-1]
        write_message(last_message)
        references = st.session_state.state["relevant_docs"]
        if len(references)>0:
            with st.expander("References"):
                st.json(references)
