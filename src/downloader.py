"""
Delete disliked images to free up space and
Download and optimize new images 
"""
import glob
import os
import pathlib
from pathlib import Path
from typing import Optional

import psycopg2
from dotenv import find_dotenv, load_dotenv
from PIL import Image, ImageFile

from gallery_dl_helper import download_pic_from_url
from models import RedditPost
from postgres import (
    connect_to_db,
    get_disliked_posts,
    set_downloaded_status_by_phash,
    set_wrong_format_status_by_phash,
)
from verify_file_integrity import verify_downloaded_files

# load configuration
load_dotenv(find_dotenv(raise_error_if_not_found=True))


ImageFile.LOAD_TRUNCATED_IMAGES = True  # else OsError


MEGABYTE = 1000000
GIGABYTE = 1000000000

STATIC_FOLDER_PATH = os.getenv("STATIC_FOLDER_PATH")


# stop downloading files when it gets to the size limit
FOLDER_SIZE_LIMIT = 5 * GIGABYTE


def get_reddit_post_data(cursor, limit: int):
    query = """select mar.post_id, mar.author, mar.created_utc, mar.title, mar.url, mar.phash, mar.sub_name from my_app_redditpost mar 
            left join my_app_vkpost mav on mar.phash=mav.phash where mav.phash is null
            and (mar.phash NOT IN (SELECT DISTINCT phash FROM my_app_redditpost where is_disliked=true))
            AND (mar.sub_name IN ('awwnime','fantasymoe','patchuu','awenime','moescape'))
            AND mar.is_downloaded=false
            AND mar.is_checked=false
            AND mar.wrong_format=false
            ORDER BY created_utc DESC
            LIMIT (%s)
            """

    try:
        cursor.execute(query, (limit,))
    except psycopg2.errors.ProtocolViolation as exc:
        print(f"DB error: {exc}")
        return
    data = cursor.fetchall()
    return data


def optimize_image(file_path: str) -> None:
    """convert to jpg, reduce filesize

    Args:
        file_path (str): path to image
    """
    #
    new_path = file_path
    if not file_path.endswith(".jpg"):
        new_path = os.path.splitext(file_path)[0] + ".jpg"

    with Image.open(file_path) as img:
        img.convert("RGB").save(new_path, optimize=True)

    # remove old file
    if file_path != new_path:
        try:
            os.remove(file_path)
        except OSError as ex:
            print(ex)
            pass


def rename_latest_file_in_folder(folder: str, new_filename: str) -> Optional[Path]:
    """Gallery-dl loads images with random names, rename the latest downloaded one
    to {new_filename} + {.ext}

    Args:
        new_filename (str): {created_utc} + '_' + {post.id}

    Returns:
        [type]: new path to renamed file
    """
    file_path = get_latest_filename_in_folder(folder)
    if not file_path:
        print("No file path found")
        return None
    old_ext = file_path.suffix
    old_path = Path(file_path).resolve().parent
    new_path = Path(old_path, new_filename + old_ext)
    try:
        file_path.rename(new_path)
    except FileExistsError:
        print("File already exists")
    return new_path


def get_latest_filename_in_folder(folder: str) -> Optional[Path]:
    download_folder = str(Path(folder + "/*").absolute())
    try:
        last_file = max(glob.glob(download_folder), key=os.path.getctime)
    except ValueError:
        print("Couldnt find a file")
        return None

    return Path(last_file)


def get_static_folder_size() -> int:
    # this is non recursive
    assert isinstance(STATIC_FOLDER_PATH, str)
    root_directory = Path(STATIC_FOLDER_PATH)
    return sum(f.stat().st_size for f in root_directory.glob("**/*") if f.is_file())


def download_images(amount: int) -> None:
    # get N random entries from db
    # download them, rename, optimize size
    connection = connect_to_db()

    with connection:
        with connection.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        ) as cursor:
            try:
                posts = get_reddit_post_data(cursor, amount)
            except (
                psycopg2.InterfaceError,
                psycopg2.errors.ProtocolViolation,
            ):  # connection errors
                print("DB Connection error")
                return

    try:
        for post in posts:
            reddit_post = RedditPost.from_downloader_db(post)
            print(f"Downloading: {post.url}")
            did_load = download_pic_from_url(reddit_post.url)
            if not did_load:
                print("Couldnt download file, with ", f"{reddit_post.url=}")
                set_wrong_format_status_by_phash(
                    connection, status=True, phash=reddit_post.phash
                )
                continue
            else:
                assert isinstance(STATIC_FOLDER_PATH, str)
                file_path = rename_latest_file_in_folder(
                    STATIC_FOLDER_PATH, f"{reddit_post.sub_name}_{reddit_post.post_id}"
                )

            optimize_image(file_path=str(file_path))
            # mark as selected in db
            set_downloaded_status_by_phash(
                connection, status=True, phash=reddit_post.phash
            )

    finally:
        if connection:
            connection.close()


def delete_disliked_posts():
    conn = connect_to_db()
    disliked_posts = get_disliked_posts(conn)

    for post in disliked_posts:
        (sub_name, post_id, phash) = post
        # mark as not downloaded in db
        set_downloaded_status_by_phash(conn, status=False, phash=phash)

        # delete file
        filename = pathlib.Path(STATIC_FOLDER_PATH, f"{sub_name}_{post_id}.jpg")
        filename.unlink(missing_ok=True)

    if conn:
        conn.close()


def main():
    folder_size = get_static_folder_size()
    print(folder_size / MEGABYTE)

    delete_disliked_posts()

    if folder_size > FOLDER_SIZE_LIMIT:
        print("Enough files")
    else:
        print("Downloading more")
        download_images(5)
        verify_downloaded_files()


if __name__ == "__main__":
    main()
