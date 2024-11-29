import requests
import os


def download_google_drive_data(url: str, save_folder: str) -> str:
    if "drive.google.com" in url:
        return download_file(url, save_folder)
    elif "docs.google.com" in url:
        return download_doc(url, save_folder)


def download_file(url: str, save_folder: str) -> str:
    """download from drive.google.com"""
    response = requests.get(url)
    file_name = (
        response.headers["Content-Disposition"].split("filename=")[1].replace('"', "")
    )
    file_path = os.path.join(save_folder, file_name)
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path


def download_doc(url: str, save_folder: str) -> str:
    """download from docs.google.com"""
    # convert to drive.google.com url
    file_id = url.split("/d/")[-1].split("/")[0]
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    return download_file(download_url, save_folder)
