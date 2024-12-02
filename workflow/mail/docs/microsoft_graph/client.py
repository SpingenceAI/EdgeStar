import argparse
import requests
import os
from dotenv import load_dotenv
import json


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
    return response.json()["access_token"]


def list_users(access_token: str):
    url = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.request("GET", url, headers=headers)
    return response.json()["value"]


def list_mail_folders(token: str, user_id: str):
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/mailFolders"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.request("GET", url, headers=headers)
    return response.json()


def list_mails(token: str, user_id: str, folder_id: str):
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.request("GET", url, headers=headers)
    return response.json()["value"]


def main(mode: str, env_path: str, output_path: str):
    load_dotenv(env_path)

    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    secret = os.getenv("SECRET")
    user_id = os.getenv("OFFICE_USER_ID")
    if tenant_id in [None, ""]:
        raise Exception("TENANT_ID is not set")
    if client_id in [None, ""]:
        raise Exception("CLIENT_ID is not set")
    if secret in [None, ""]:
        raise Exception("SECRET is not set")
    access_token = get_access_token(tenant_id, client_id, secret)
    if mode == "list_users":
        with open(output_path, "w") as f:
            f.write(json.dumps(list_users(access_token),indent=4))
    elif mode == "list_mail_folders":
        if user_id in [None, ""]:
            raise Exception("OFFICE_USER_ID is not set")
        with open(output_path, "w") as f:
            f.write(json.dumps(list_mail_folders(access_token, user_id),indent=4))
    elif mode == "test_connection":
        if user_id in [None, ""]:
            raise Exception("OFFICE_USER_ID is not set")
        bot_mail_folder_id = os.getenv("BOT_MAIL_FOLDER_ID")
        if bot_mail_folder_id in [None, ""]:
            raise Exception("BOT_MAIL_FOLDER_ID is not set")
        mails = list_mails(access_token, user_id, bot_mail_folder_id)
        print(f"Get {len(mails)} mail from folder {bot_mail_folder_id}")
    else:
        raise Exception(f"Mode {mode} is not supported")
if __name__ == "__main__":

    args = argparse.ArgumentParser()
    args.add_argument("--mode", type=str, required=False,default="list_users")
    args.add_argument("--env_path", type=str, required=True)
    args.add_argument("--output_path", type=str, required=False,default=None)
    args = args.parse_args()

    env_path = args.env_path
    mode = args.mode
    output_path = args.output_path
    main(mode, env_path, output_path)
