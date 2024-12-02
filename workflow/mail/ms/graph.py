"""microsoft graph api"""

import requests
import json


from loguru import logger
import env

from ms.data import MailError


class MSGraphError(Exception):
    pass


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


def get_access_token(tenant_id: str, client_id: str, secret: str) -> str:
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    scope = "https://graph.microsoft.com/.default"
    payload = {
        "client_id": client_id,
        "scope": scope,
        "client_secret": secret,
        "grant_type": "client_credentials",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code != 200:
        raise MailError(
            f"Failed to get access token: Response code:{response.status_code} - {json.dumps(response.json())}"
        )
    return response.json()["access_token"]


@singleton
class ENV:
    def __init__(
        self,
        folder_id: str = None,
        user_id: str = None,
        tenant_id: str = None,
        client_id: str = None,
        secret: str = None,
    ):
        self._token = None
        self.folder_id = folder_id
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.secret = secret
        self.base_url = "https://graph.microsoft.com/v1.0"
        # self.folder_id = os.getenv("BOT_MAIL_FOLDER_ID")
        # self.base_url = "https://graph.microsoft.com/v1.0"
        # self.user_id = os.getenv("OFFICE_USER_ID")
        # self.tenant_id = os.getenv("TENANT_ID")
        # self.client_id = os.getenv("CLIENT_ID")
        # self.secret = os.getenv("SECRET")
        # self.data_folder = env.DATA_MOUNT_PATH
        # if any of the env is not set, raise an error
        if (
            not self.folder_id
            or not self.user_id
            or not self.tenant_id
            or not self.client_id
            or not self.secret
        ):
            raise MailError("Environment variables are not set")

    def update_token(self):
        self._token = get_access_token(self.tenant_id, self.client_id, self.secret)
        logger.debug(f"Token updated: {self._token}")

    @property
    def token(self):
        if self._token is None:
            self.update_token()
        return self._token

    @property
    def headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }


def get_users(token: str):
    url = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.request("GET", url, headers=headers)
    if response.status_code != 200:
        raise MSGraphError(
            f"Response code:{response.status_code} - {json.dumps(response.json())}"
        )
    return response.json()


def list_mail_folders(token: str, user_id: str):
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/mailFolders"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.request("GET", url, headers=headers)
    return response.json()


if __name__ == "__main__":

    from dotenv import load_dotenv
    import os

    load_dotenv()

    token = get_access_token(
        os.getenv("TENANT_ID"), os.getenv("CLIENT_ID"), os.getenv("SECRET")
    )
    print(token)
    users = get_users(token)

    user_id = os.getenv("OFFICE_USER_ID")
    folders = list_mail_folders(token, user_id)
    print(folders)
