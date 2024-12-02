import env

from use_cases import receive_mails
from process import process_mail
from utils import logger,format_error_message
import time
def main():
    while True:
        # receive mails
        try:
            mails = receive_mails(filter_read=True)
            logger.info(f"Received {len(mails)} mails")
        except Exception as e:
            logger.error(f"Receive mails error: {format_error_message(e)}")
            time.sleep(1)
            continue
        # # process and reply mails
        for mail in mails:
            logger.info(f"Processing mail: {mail.subject}")
            process_mail(mail)
        time.sleep(10)


if __name__ == "__main__":
    main()
