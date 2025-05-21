import os
import zipfile
import shutil


def extract_archive(archive_path: str, extract_to: str):
    os.makedirs(extract_to, exist_ok=True)
    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith(".rar"):
        raise NotImplementedError("RAR extraction not implemented (install unrar lib or use .zip)")
    else:
        raise ValueError("Unsupported archive type.")


def create_archive(folder_path: str, output_path: str):
    shutil.make_archive(output_path.replace('.zip', ''), 'zip', folder_path)

