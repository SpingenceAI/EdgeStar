import subprocess
import os
import logging
import json
import math
import shutil


def convert_video_to_mp3(input_video, output_audio=None):
    """convert video to mp3"""
    if output_audio is None:
        # If no output filename is provided, use the same name as the input video with an .mp3 extension
        output_audio = os.path.splitext(input_video)[0] + ".mp3"

    # ffmpeg command to convert video to mp3
    cmd = f"ffmpeg -i {input_video} -q:a 0 -map a {output_audio}"

    try:
        subprocess.run(cmd, shell=True, check=True)
        logging.info(f"Conversion successful: {output_audio}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during conversion: {e}")


def repackage_audio(input_file:str, output_file:str):
    """repackage audio to avoid audio can't get duration
    ffmpeg -y -i {input_file} {output_file}
    Args:
        input_file (str): input file path
        output_file (str): output file path
    """
    cmd = f"ffmpeg -y -i {input_file} {output_file}"
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"Repackaged: {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during repackaging: {e}")


def get_audio_duration(input_file:str):
    """get audio duration
    Args:
        input_file (str): input file path
    Returns:
        float: audio duration in seconds
    """
    cmd = f"ffprobe -v quiet -print_format json -show_format -show_streams {input_file}"
    result = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    info = json.loads(result.stdout.decode("utf-8"))
    # Extract duration in seconds from the format section
    duration = float(info["format"]["duration"])
    return duration


def split_audio_with_overlap(
    input_file: str, output_dir: str, chunk_length: int, overlap: int
):
    """split audio with overlap
    Args:
        input_file (str): input file path
        output_dir (str): output directory
        chunk_length (int): chunk length in seconds
        overlap (int): overlap in seconds
    Returns:
        list: list of audio file paths
    """
    audio_path_list = []
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(input_file):
        raise FileExistsError(f"File {input_file} not exists")
    total_seconds = get_audio_duration(input_file)
    # Calculate the number of chunks
    step = chunk_length - overlap
    chunks = int(math.ceil((total_seconds - overlap) / step))
    for i in range(chunks):
        start_time = i * step
        end_time = start_time + chunk_length

        # if last chunk is less than chunk_length, set it to total_seconds
        if i == chunks - 1:
            end_time = total_seconds

        output_file = os.path.join(output_dir, f"{int(start_time)}-{int(end_time)}.mp3")

        # ffmpeg command to extract the chunk
        cmd = (
            f"ffmpeg -i {input_file} -ss {start_time} "
            f"-t {chunk_length} -c copy {output_file} -y"
        )
        subprocess.run(cmd, shell=True)
        logging.info(f"Created: {output_file}")
        audio_path_list.append(os.path.abspath(output_file))
    logging.info(f"Audio splitting into {len(audio_path_list)} files.")
    return audio_path_list
