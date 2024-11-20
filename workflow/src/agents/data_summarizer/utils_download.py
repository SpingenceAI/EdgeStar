import requests
import os
from loguru import logger


def download_data(url: str, save_folder: str) -> str:
    """download data from url and save to save_folder
    args:
        url: the url of the data
        save_folder: the folder to save the data
    returns:
        the path of the saved data
    """
    os.makedirs(save_folder, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    logger.debug(f"Downloading data from {url}")
    response = requests.head(url, headers=headers)
    response.raise_for_status()
    mime_type = response.headers["Content-Type"].split(";")[0]
    logger.debug(f"Mime type: {mime_type}")

    # mine_type is text/html or json or xml
    if "text" in mime_type or mime_type in ["application/json", "application/xml"]:
        file_extension = mime_type.split("/")[-1]
        response = requests.get(url, headers=headers)
        save_path = os.path.join(save_folder, f"data.{file_extension}")
        with open(save_path, "w") as f:
            f.write(response.text)
    else:
        if mime_type in [
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]:
            file_extension = "docx"
        elif mime_type in [
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ]:
            file_extension = "xlsx"
        elif mime_type in [
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]:
            file_extension = "pptx"
        else:
            file_extension = mime_type.split("/")[-1]
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        save_path = os.path.join(save_folder, f"data.{file_extension}")
        with open(save_path, "wb") as f:
            f.write(response.content)
    return save_path
