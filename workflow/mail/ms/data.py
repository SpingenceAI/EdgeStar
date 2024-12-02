from pydantic import BaseModel
from typing import List, Optional
import os
import base64
import json
import env


class MailError(Exception):
    pass


class Attachment(BaseModel):
    id: str
    name: str  # with file extension
    size: int
    contentType: str  # mime type
    contentBytes: str  # base64 encoded

    def save_to_file(self, save_folder: str):
        """save the attachment to a file"""
        os.makedirs(save_folder, exist_ok=True)
        save_path = os.path.join(save_folder, self.name)
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(self.contentBytes))
        return save_path

    def to_bytes(self):
        """return the attachment as bytes"""
        return base64.b64decode(self.contentBytes)


class Mail(BaseModel):
    id: str
    category: str  # category name
    assistant: str  # assistant name
    createdDateTime: str  # YYYY-MM-DDT.....
    receivedDateTime: str  # YYYY-MM-DDT.....
    subject: str  # [category-assistant]
    body: str  # parsed body
    raw_body: str  # raw body
    sender: str
    is_read: bool
    has_attachments: bool
    urls: List[str] = None  # list of urls in the body
    attachments: Optional[List[Attachment]] = None
    data_folder: str = None

    @property
    def reply_path(self):
        if self.data_folder is None:
            return None
        return os.path.join(self.data_folder, "reply.json")

    @property
    def mail_content_path(self):
        if self.data_folder is None:
            return None
        return os.path.join(self.data_folder, "mail.json")

    def set_data_folder(self, data_folder: str):
        self.data_folder = data_folder

    def save_reply(self, data: dict):
        """save the reply to a file"""
        if self.data_folder is None:
            raise MailError("data folder is not set")
        reply_path = self.reply_path
        with open(reply_path, "w") as f:
            f.write(json.dumps(data, indent=4))

    @property
    def is_replied(self):
        if self.data_folder is None:
            return False
        reply_path = self.reply_path
        return os.path.exists(reply_path)

    @property
    def is_saved(self):
        """check if the mail is saved to a file"""
        mail_content_path = self.mail_content_path
        return os.path.exists(mail_content_path)

    def save_to_file(self, data_folder: str):
        """save the mail to a file"""
        self.data_folder = data_folder
        os.makedirs(data_folder, exist_ok=True)
        mail_content_path = self.mail_content_path
        with open(mail_content_path, "w") as f:
            f.write(
                json.dumps(
                    {
                        "id": self.id,
                        "category": self.category,
                        "assistant": self.assistant,
                        "createdDateTime": self.createdDateTime,
                        "receivedDateTime": self.receivedDateTime,
                        "subject": self.subject,
                        "body": self.body,
                        "urls": self.urls,
                        "raw_body": self.raw_body,
                        "sender": self.sender,
                        "is_read": self.is_read,
                        "has_attachments": self.has_attachments,
                    },
                    indent=4,
                )
            )
        if self.attachments:
            for attachment in self.attachments:
                attachment.save_to_file(data_folder)
