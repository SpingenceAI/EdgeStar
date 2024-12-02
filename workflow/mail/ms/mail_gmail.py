import os
import base64
from typing import List
from loguru import logger
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ms.utils import parse_subject, parse_body
from ms.data import Mail, Attachment
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import env

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]


def get_gmail_service():
    """get the gmail service"""
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        raise FileNotFoundError("Gmail token.json not found")

    return build("gmail", "v1", credentials=creds)


def get_attachments(service, message: dict):
    """get attachments from a mail"""
    attachments = []
    # parse attachments
    for part in message["payload"]["parts"]:
        if part["filename"]:
            if "data" in part["body"]:
                data = part["body"]["data"]
            else:
                att_id = part["body"]["attachmentId"]
                att = (
                    service.users()
                    .messages()
                    .attachments()
                    .get(userId="me", messageId=message["id"], id=att_id)
                    .execute()
                )
                data = att["data"]
            file_data = data.encode("UTF-8")
            path = part["filename"]
            size = len(file_data)
            content_type = part["mimeType"]
            attachments.append(
                Attachment(
                    id=att_id,
                    name=path,
                    size=size,
                    contentType=content_type,
                    contentBytes=file_data,
                )
            )
    return attachments


def get_body(message: dict):
    """get the body of a mail and return text and urls"""
    html_data = ""
    text_data = ""
    for part in message["payload"]["parts"]:
        if part["filename"]:
            continue
        if part["mimeType"] == "multipart/alternative":
            for sub_part in part["parts"]:
                if sub_part["mimeType"] == "text/plain":
                    data = sub_part["body"]["data"]
                    byte_code = base64.urlsafe_b64decode(data)
                    text_data = byte_code.decode("utf-8")
                elif sub_part["mimeType"] == "text/html":
                    data = sub_part["body"]["data"]
                    byte_code = base64.urlsafe_b64decode(data)
                    html_data = byte_code.decode("utf-8")
                else:
                    raise Exception(f"Unknown mime type {part['mimeType']}")
        else:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                byte_code = base64.urlsafe_b64decode(data)
                text_data = byte_code.decode("utf-8")
            elif part["mimeType"] == "text/html":
                data = part["body"]["data"]
                byte_code = base64.urlsafe_b64decode(data)
                html_data = byte_code.decode("utf-8")
            else:
                raise Exception(f"Unknown mime type {part['mimeType']}")

    _, urls = parse_body(html_data)
    return text_data, html_data, urls


def mark_mail_as_read(service, message_id: str):
    """mark a mail as read"""
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def get_email_address(service) -> str:
    """get the email address of the user"""
    profile = service.users().getProfile(userId="me").execute()
    return profile["emailAddress"]


def read_mail(service, message_id: str):
    """
    Parse a mail from the Google API
    """
    msg = service.users().messages().get(userId="me", id=message_id).execute()
    email_data = msg["payload"]["headers"]
    for values in email_data:
        name = values["name"]
        if name == "From":
            sender = values["value"]
        if name == "Subject":
            subject = values["value"]
        if name == "Date":
            # Date | Values: Tue, 19 Nov 2024 08:07:35 +0000
            rawDate = values["value"]
            receivedDateTime = rawDate.split(",")[1].strip()
            createdDateTime = rawDate.split(",")[1].strip()
    attachments = get_attachments(service, msg)
    if attachments:
        has_attachments = True
    else:
        has_attachments = False
    text_data, html_data, urls = get_body(msg)
    category, assistant = parse_subject(subject)  # pylint: disable=E0606

    mail = Mail(
        id=message_id,
        category=category,
        assistant=assistant,
        createdDateTime=createdDateTime,  # pylint: disable=E0606
        receivedDateTime=receivedDateTime,  # pylint: disable=E0606
        subject=subject,
        body=text_data,
        urls=urls,
        raw_body=html_data,
        sender=sender,  # pylint: disable=E0606
        is_read=False,  # check
        has_attachments=has_attachments,
        attachments=attachments,
    )
    return mail


def receive_mails(filter_read: bool) -> List[Mail]:
    """
    Receive mails from gmail and return a list of unread mails
    """

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    service = get_gmail_service()
    if filter_read:
        gmail_results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], q="is:unread")
            .execute()
        )
    else:
        gmail_results = (
            service.users().messages().list(userId="me", labelIds=["INBOX"]).execute()
        )
    message_ids = [x["id"] for x in gmail_results.get("messages", [])]
    parsed_mails = []
    if not message_ids:
        print("No messages found.")
    else:
        for message_id in message_ids:
            try:
                mail = read_mail(service, message_id)
                mark_mail_as_read(service, message_id)
                if not mail.is_replied:
                    parsed_mails.append(mail)
            except Exception as e:
                logger.error(f"Failed to parse mail: {message_id}, error: {e}")
    return parsed_mails


def reply_mail(mail: Mail, content: str) -> bool:
    """reply to a mail"""
    service = get_gmail_service()

    message = MIMEMultipart()
    message["to"] = mail.sender
    message["from"] = get_email_address(service)
    message["subject"] = "Re: " + mail.subject

    msg = MIMEText(content, "html")
    message.attach(msg)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    msg_dict = {"raw": raw_message}

    sent_message = service.users().messages().send(userId="me", body=msg_dict).execute()
    return sent_message
