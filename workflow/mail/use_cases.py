from typing import List
import ms.mail as mail_utils
from ms.data import Mail

def receive_mails(filter_read:bool=True) -> List[Mail]:
    """receive mails from mailbox"""
    return mail_utils.receive_mails(filter_read=filter_read)
