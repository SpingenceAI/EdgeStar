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
    st.session_state.graph = utils.get_chatbot_graph()


if "kb_name" not in st.session_state:
    init_session_state()


def on_kb_change():
    print(st.session_state.kb_select)
    value = st.session_state.kb_select
    if value in ["", None]:
        init_session_state()
    st.session_state.kb_name = value


# side bar
with st.sidebar:
    st.image(LOGO)
    with st.popover("Create a new knowledge base"):
        kb_name = st.text_input("Enter the name of the knowledge base")
        
        
        if st.button("Create"):
            if 3 < len(kb_name) < 63:
                if " " in kb_name:
                    st.error("The name of the knowledge base cannot contain spaces")
                else:
                    utils.create_knowledge_base(kb_name)
                    st.rerun()
            else:
                st.error("The name of the knowledge base must be between 3 and 63 characters")
    kb_list = utils.list_kb()
    st.selectbox(
        "Select a knowledge base",
        kb_list,
        index=None,
        on_change=on_kb_change,
        key="kb_select",
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


def write_message(message, role: str = None):
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
if st.session_state.state["messages"]:
    if st.session_state.kb_name not in ["", None]:
        collection_titile = f"Knowledge Base : {st.session_state.kb_name}"
        st.write(collection_titile)
    for msg in st.session_state.state["messages"]:
        write_message(msg)
user_query = st.chat_input("Enter your message")
if user_query:
    write_message({"role": "user", "content": user_query})
    st.session_state.state["messages"].append({"role": "user", "content": user_query})
    session_id = utils.get_st_session_id()
    thread_config = {"configurable": {"thread_id": session_id}}
    with st.spinner("processing..."):
        st.session_state.state = st.session_state.graph.invoke(
            st.session_state.state, thread_config
        )
    last_message = st.session_state.state["messages"][-1]
    write_message(last_message)
    references = st.session_state.state.get("relevant_docs", [])
    if len(references) > 0:
        with st.expander("References"):
            st.json(references)
