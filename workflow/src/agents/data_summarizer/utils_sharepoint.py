import onedrivedownloader
import os


def download_sharepoint_data(url: str, save_folder: str) -> str:
    """download sharepoint data from url and save to save_folder
    args:
        url: the url of the sharepoint data
        save_folder: the folder to save the sharepoint data
    returns:
        the path of the saved sharepoint data
    """
    accepted_file_extensions = ["docx", "doc", "pdf", "ppt", "pptx", "txt","mp4", "mp3", "wav", "m4a"]
    onedrivedownloader.download(url, save_folder)
    file_list = [x for x in os.listdir(save_folder) if x.split(".")[-1] in accepted_file_extensions]
    if len(file_list) == 0:
        return None
    return os.path.join(save_folder, file_list[0])
