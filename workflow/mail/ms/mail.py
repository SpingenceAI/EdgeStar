"""
This file contains the mail class and functions for interacting with the Microsoft Graph API.
"""

from typing import List
from ms.data import Mail
import datetime
import os
import env

SAVE_FOLDER = env.DATA_FOLDER
MAIL_PROVIDER = env.MAIL_PROVIDER
if MAIL_PROVIDER == "graph":
    import ms.mail_graph as mail_provider
elif MAIL_PROVIDER == "gmail":
    import ms.mail_gmail as mail_provider
else:
    raise ValueError(f"Invalid mail provider: {MAIL_PROVIDER}")



def receive_mails(filter_read: bool) -> List[Mail]:
    """receive mails"""
    mails = mail_provider.receive_mails(filter_read)
    for mail in mails:

        # setup mail save folder
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        mail_folder = os.path.join(SAVE_FOLDER, today_str, mail.id)
        mail.set_data_folder(mail_folder)

        # save mail to file if not saved
        if not mail.is_saved:
            mail.save_to_file(mail_folder)
    return mails


def reply_mail(mail: Mail, content: str):
    """reply to a mail
    content: html formatted string
    """
    payload = mail_provider.reply_mail(mail, content)
    mail.save_reply(payload)
