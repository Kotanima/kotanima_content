import gallery_dl
from gallery_dl.job import DownloadJob, config
import pathlib
from dotenv import load_dotenv, find_dotenv
import os

# load configuration
load_dotenv(find_dotenv(raise_error_if_not_found=True))


def download_pic_from_url(url: str, folder=os.getenv("STATIC_FOLDER_PATH")) -> bool:

    """Download image file

    Args:
        url (str): url to image file

    Returns:
        bool: True if no errors
    """

    config.set(("extractor", "imgur"), "filename", "{id}.{extension}")
    config.set((), "timeout", 7)
    config.set((), "sleep", 1)
    config.set((), "image-range", "1")
    config.set(
        (), "image-filter", "extension in ('jpg', 'png', 'jpeg', 'PNG', 'JPEG', 'webp')"
    )
    config.set((), "directory", [])
    config.set((), "base-directory", folder)
    config.set((), "parent-directory", True)
    config.set(("extractor", "imgur"), "mp4", False)
    config.set(("extractor", "imgur"), "gif", False)
    config.set(("downloader",), "filesize-min", "20k")
    config.set(
        ("extractor", "pixiv"),
        "refresh-token",
        os.getenv("GALLERY_DL_REFRESH_TOKEN"),
    )
    config.set(("extractor", "pixiv"), "avatar", False)
    config.set(("extractor", "pixiv"), "ugoira", False)

    try:
        DownloadJob(url).run()
    except gallery_dl.exception.GalleryDLException:
        return False

    return True
