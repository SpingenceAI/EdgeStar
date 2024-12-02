from loguru import logger
import os
import requests
import json
from typing import List, Optional
from ms.utils import parse_subject, parse_body
from ms.data import Mail, Attachment, MailError
from ms.graph import ENV
import env

# INIT MAIL ENVIRONMENT
mail_env = ENV(
    folder_id=os.getenv("BOT_MAIL_FOLDER_ID"),
    user_id=os.getenv("OFFICE_USER_ID"),
    tenant_id=os.getenv("TENANT_ID"),
    client_id=os.getenv("CLIENT_ID"),
    secret=os.getenv("SECRET")
)
logger.debug(f"TOKEN: {mail_env.token}")
logger.debug(f"FOLDER_ID: {mail_env.folder_id}")



def get_attachments(mail_id: str) -> List[Attachment]:
    """get attachments from a mail"""
    url = f"{mail_env.base_url}/users/{mail_env.user_id}/messages/{mail_id}/attachments"
    response = requests.request("GET", url, headers=mail_env.headers)
    if response.status_code != 200:
        raise MailError(
            f"Failed to get attachments: Response code:{response.status_code} - {json.dumps(response.json())}"
        )
    attachments = [Attachment(**x) for x in response.json()["value"]]
    return attachments


def parse_mail(raw_mail: dict) -> Optional[Mail]:
    """
    Parse a mail from the API
    """
    category, assistant = parse_subject(raw_mail.get("subject", ""))
    has_attachments = raw_mail.get("hasAttachments", False)
    attachments = get_attachments(raw_mail.get("id")) if has_attachments else None
    text, urls = parse_body(raw_mail.get("body", {}).get("content"))
    mail = Mail(
        id=raw_mail.get("id"),
        category=category,
        assistant=assistant,
        createdDateTime=raw_mail.get("createdDateTime"),
        receivedDateTime=raw_mail.get("receivedDateTime"),
        subject=raw_mail.get("subject"),
        body=text,
        urls=urls,
        raw_body=raw_mail.get("body", {}).get("content"),
        sender=raw_mail.get("sender", {}).get("emailAddress", {}).get("address"),
        is_read=raw_mail.get("isRead", False),
        has_attachments=has_attachments,
        attachments=attachments,
    )
    return mail


def receive_mails(filter_read: bool) -> List[Mail]:
    """
    Receive mails from a specific folder and return a list of unread mails
    """
    url = f"{mail_env.base_url}/users/{mail_env.user_id}/mailFolders/{mail_env.folder_id}/messages"
    response = requests.request("GET", url, headers=mail_env.headers)
    if response.status_code == 401:
        mail_env.update_token()
        url = f"{mail_env.base_url}/users/{mail_env.user_id}/mailFolders/{mail_env.folder_id}/messages"
        response = requests.request("GET", url, headers=mail_env.headers)
    if response.status_code != 200:
        raise MailError(
            f"Failed to get mails: Response code:{response.status_code} - {json.dumps(response.json())}"
        )
    raw_mails = response.json().get("value", [])
    parsed_mails = []
    for raw_mail in raw_mails:
        if filter_read:
            is_read = raw_mail.get("isRead", False)
        else:
            is_read = False

        # use rul to filter out mails that are not from spingence.com or edge-star.com
        # sender = raw_mail.get("sender", {}).get("emailAddress", {}).get("address", "")
        # if "spingence.com" not in sender and "edge-star.com" not in sender:
        #     logger.warning(
        #         f"Mail {raw_mail.get('id')} Invalid sender: {sender}"
        #     )
        #     continue
        if is_read:
            continue
        try:
            parsed_mail = parse_mail(raw_mail)
            if not parsed_mail.is_replied:
                parsed_mails.append(parsed_mail)
        except MailError as e:
            logger.error(f"Failed to parse mail: {raw_mail.get('id')}, error: {e}")
    return parsed_mails


def reply_mail(mail: Mail, content: str) -> dict:
    url = f"{mail_env.base_url}/users/{mail_env.user_id}/messages/{mail.id}/reply"
    payload = {
        "message": {
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": mail.sender,
                    }
                },
            ]
        },
        "comment": content,
    }

    response = requests.request(
        "POST", url, headers=mail_env.headers, data=json.dumps(payload)
    )

    if response.status_code != 202:
        raise MailError(
            f"Failed to reply mail: Response code:{response.status_code} - {json.dumps(response.json())}"
        )
    return payload


def list_mail_folders() -> List[dict]:
    url = f"{mail_env.base_url}/users/{mail_env.user_id}/mailFolders/?includeHiddenFolders=true"
    response = requests.request("GET", url, headers=mail_env.headers)
    if response.status_code != 200:
        raise MailError(
            f"Failed to list mail folders: Response code:{response.status_code} - {json.dumps(response.json())}"
        )

    return response.json().get("value", [])
