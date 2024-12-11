from typing import List
import onedrivedownloader
import os


def download_sharepoint_data(url: str, save_folder: str) -> List[str]:
    """download sharepoint data from url and save to save_folder
    args:
        url: the url of the sharepoint data
        save_folder: the folder to save the sharepoint data
    returns:
        the path of the saved sharepoint data
    """
    # accepted_file_extensions = ["docx", "doc", "pdf", "ppt", "pptx", "txt","mp4", "mp3", "wav", "m4a","aac"]
    onedrivedownloader.download(url, save_folder)
    return [x.path for x in os.scandir(save_folder) if x.is_file()]
