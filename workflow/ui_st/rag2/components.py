import streamlit as st

def footer():

    FOOTER_HTML = """
    <div style="position: fixed;bottom: 0;">
        <hr></hr>
        <div style='text-align: left;'>
            <p style='color:gray;'>Developed by Spingence</p>
            <p style='color:gray;'>For extended needs or inquiries, <br>contact: edgeai.service@spingence.com</p>
        </div>
    </div>
    """
    st.markdown(FOOTER_HTML, unsafe_allow_html=True)
