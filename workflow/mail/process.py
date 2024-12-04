import sys
import os
# add workflow to sys path
sys.path.append("..")
from src.agents.meeting_recap.agent import init_graph as init_meeting_recap_graph
from src.agents.data_summarizer.agent import init_graph as init_data_summarizer_graph
from src.agents.chatbot.agent import init_graph as init_chatbot_graph
from src.agents.web_search.agent import init_graph as init_web_search_graph
import tempfile
from ms import mail as mail_utils
from utils import format_error_message, logger
import markdown
import env


def process_ask_chatbot_mail(mail: mail_utils.Mail):

    agent_config = env.CHATBOT_CONFIG
    graph, _ = init_chatbot_graph(agent_config)
    state = {"messages": [{"role": "user", "content": mail.body}]}
    thread_config = {"configurable": {"thread_id": mail.id}}
    state = graph.invoke(state, thread_config)
    reply = state["messages"][-1].content
    try:
        reply = markdown.markdown(reply)
    except Exception as e:
        logger.error(f"process_ask_chatbot_mail failed to convert markdown: {reply}")
        reply = reply
    mail_utils.reply_mail(mail, reply)


def process_tool_ms_mail(mail: mail_utils.Mail):
    """MEETING RECAP"""
    agent_config = env.MEETING_RECAP_CONFIG
    graph, _ = init_meeting_recap_graph(agent_config)
    thread_config = {"configurable": {"thread_id": mail.id}}
    file_path = None
    with tempfile.TemporaryDirectory() as temp_folder:
        for attachment in mail.attachments:
            extension = attachment.name.split(".")[-1]
            if extension.lower() in ["mp4", "mp3", "m4a", "wav"]:
                temp_folder = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_folder, f"{mail.id}.{extension}")
                with open(temp_file_path, "wb") as f:
                    f.write(attachment.to_bytes())
                file_path = temp_file_path
                break
        if file_path is None:
            raise Exception("No audio file found in the mail")
        state = {"messages": [], "file_path": file_path}
        state = graph.invoke(state, thread_config)
        reply = state["summary"]
        mail_utils.reply_mail(mail, reply)


def process_tool_data_summarizer_mail(mail: mail_utils.Mail):
    agent_config = env.DATA_SUMMARIZER_CONFIG
    with tempfile.TemporaryDirectory() as temp_folder:
        graph, _ = init_data_summarizer_graph(agent_config)
        thread_config = {"configurable": {"thread_id": mail.id}}

        data_source_list = []
        if mail.attachments:
            for attachment in mail.attachments:
                name = attachment.name
                extension = name.split(".")[-1].lower()
                if extension in [
                    "mp3",
                    "mp4",
                    "m4a",
                    "wav",
                    "pdf",
                    "pptx",
                    "docx",
                    "xlsx",
                    "txt",
                ]:
                    save_path = attachment.save_to_file(temp_folder)
                    data_source_list.append(save_path)
        if mail.urls:
            for url in mail.urls:
                data_source_list.append(url)

        state = {
            "answer": "",
            "data_source_list": data_source_list,
            "summary_list": [],
            "data_content_list": [],
            "format_instruction": "",
            "user_query": "",
        }
        state = graph.invoke(state, thread_config)
        reply = f"# DATA SUMMARY\n{state['summary_list'][0]}"
        user_query = mail.body.strip()
        if user_query != "":
            state["user_query"] = user_query
            state = graph.invoke(state, thread_config)
            reply += f"\n# USER QUERY\n{state['answer']}"
        reply += f"\n# DATA CONTENT\n"
        for data_content in state["data_content_list"]:
            reply += f"{data_content.title}\n{data_content.content}\n"
        try:
            reply = markdown.markdown(reply)
        except Exception as e:
            logger.error(
                f"process_tool_data_summarizer_mail failed to convert markdown: {reply}"
            )
            reply = reply
        mail_utils.reply_mail(mail, reply)


def process_tool_web_search_mail(mail: mail_utils.Mail):
    agent_config = env.WEB_SEARCH_CONFIG
    graph, _ = init_web_search_graph(agent_config)
    thread_config = {"configurable": {"thread_id": mail.id}}
    state = {"user_query": mail.body.strip(), "answer": ""}
    try:
        state = graph.invoke(state, thread_config)
    except Exception as e:
        logger.error(f"process_web_search_mail failed: {e}")
        reply = format_error_message(e)
    else:
        reply = state["answer"]
    try:
        reply = markdown.markdown(reply)
    except Exception as e:
        logger.error(f"process_web_search_mail failed to convert markdown: {reply}")
        reply = reply
    mail_utils.reply_mail(mail, reply)


def process_mail(mail: mail_utils.Mail):
    try:
        category = mail.category.replace("BotTest", "").upper()
        assistant = mail.assistant.upper()
        if category == "ASK":
            if assistant == "CHATBOT":
                process_ask_chatbot_mail(mail)
            else:
                raise Exception(f"Unknown assistant: {assistant}")
        elif category == "TOOL":
            if assistant == "MS":
                process_tool_ms_mail(mail)
            elif assistant == "DS":
                process_tool_data_summarizer_mail(mail)
            elif assistant == "WS":
                process_tool_web_search_mail(mail)
            elif assistant == "CHATBOT":
                process_ask_chatbot_mail(mail)
            else:
                raise Exception(f"Unknown assistant: {assistant}")
        else:
            raise Exception(f"Unknown category: {category}")
    except Exception as e:
        try:
            mail_utils.reply_mail(mail, format_error_message(e))
        except Exception as e:
            logger.error(
                f"process_mail_error[{mail.id}]: {format_error_message(e)}",
                extra={"mail_id": mail.id},
            )


def process_mail_debug(mail: mail_utils.Mail):
    category = mail.category.upper()
    assistant = mail.assistant.upper()
    if category == "ASK":
        process_ask_chatbot_mail(mail)
    elif category == "TOOL":
        if assistant == "MS":
            process_tool_ms_mail(mail)
        elif assistant == "DS":
            process_tool_data_summarizer_mail(mail)
        elif assistant == "WS":
            process_tool_web_search_mail(mail)
        elif assistant == "CHATBOT":
            process_ask_chatbot_mail(mail)
        else:
            raise Exception(f"Unknown assistant: {assistant}")
    else:
        raise Exception(f"Unknown category: {category}")
