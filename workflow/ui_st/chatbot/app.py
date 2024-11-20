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
    }
    st.session_state.graph = utils.get_graph()
if "graph" not in st.session_state:
    init_session_state()
# side bar
with st.sidebar:
    st.image(LOGO)

    components.footer()

def write_message(message):
    """write message to chat"""
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
    for msg in st.session_state.state["messages"]:
        write_message(msg)

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
