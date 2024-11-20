import streamlit as st
import env
import os
from PIL import Image
import time
import utils
import requests
import components

AVATAR_AI = Image.open(env.AI_ICON_PATH)
AVATAR_USER = Image.open(env.USER_ICON_PATH)
LOGO = Image.open(env.ES_LOGO_PATH)
SP_ICON = Image.open(env.SP_ICON_PATH)

# title
st.set_page_config(page_title="Spingence Data Extractor", page_icon=SP_ICON)
TITLE_HTML = """
    <h1 style="color:#1D65A6;">Welcome to the journey of LLM</h1>
"""
st.markdown(TITLE_HTML, unsafe_allow_html=True)

def gen_session_id():
    return str(time.time())

def init_session_state():
    st.session_state.state = {
        "data_source_list": [],
        "data_content_list": [],
        "summary_list": [],
        "answer": "",
        "format_instruction": "",
        "user_query": "",
        "extract_error": False,
    }
    st.session_state.show_text = ""
    st.session_state.graph = utils.get_graph()
    st.session_state.id = gen_session_id()


if "graph" not in st.session_state:
    init_session_state()
# side bar
with st.sidebar:
    st.image(LOGO)

    components.footer()
def update_data_source():
    value = st.session_state.data_source_input
    st.session_state.state["data_source_list"] = [value]
# SOURCE DATA AREA
with st.container():
    source_data = st.text_input("Enter data source (url or file path):",on_change=update_data_source,key="data_source_input")
    if st.button("Extract Data"):

        init_session_state()
        st.session_state.state["data_source_list"] = [st.session_state.data_source_input]

        thread_config = {"configurable": {"thread_id": st.session_state.id}}
        current_state = st.session_state.state
        with st.spinner("Extracting data..."):
            new_state = st.session_state.graph.invoke(
                current_state, thread_config
            )
            if new_state["extract_error"]:
                st.error("Failed to extract data")
            else:
                st.session_state.state = new_state
                st.session_state.show_text = st.session_state.state["summary_list"][0]
if st.session_state.state['data_content_list']:
    with st.expander("Data Source"):
        if "youtube" in st.session_state.data_source_input:
            video_id = st.session_state.data_source_input.split("v=")[1].split("&")[0]
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)
        st.write(st.session_state.state["data_content_list"][0].content)
    with st.container():
        input_text = st.text_area("Enter your instruction")
        col1, col2 = st.columns([0.3,1])
        with col1:
            if st.button("Summarize :clipboard:") and input_text != "":
                st.session_state.state["user_query"] = ""
                st.session_state.state["format_instruction"] = input_text
                session_id = st.session_state.id
                thread_config = {"configurable": {"thread_id": session_id}}
                with st.spinner("processing..."):
                    st.session_state.state = st.session_state.graph.invoke(
                        st.session_state.state, thread_config
                    )
                    st.session_state.show_text = st.session_state.state["summary_list"][0]
        with col2:
            if st.button("Question 	:question:") and input_text != "":
                st.session_state.state["format_instructon"] = ""
                st.session_state.state["user_query"] = input_text
                session_id = st.session_state.id
                thread_config = {"configurable": {"thread_id": session_id}}
                with st.spinner("processing..."):
                    st.session_state.state = st.session_state.graph.invoke(
                        st.session_state.state, thread_config
                    )
                    st.session_state.show_text = st.session_state.state["answer"]

with st.container():
    st.write(st.session_state.show_text)
