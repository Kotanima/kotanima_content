"""
Use praw/psaw api to scrape reddit, store the data in the db,
and delete the pictures to save space.
Fire module is used to turn this into a cli.
"""
import glob
import os
import time
import warnings
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, List, Tuple, Optional

import fire
import imagehash
import praw
import psycopg2
import psycopg2.errors as psql_err
from dotenv import find_dotenv, load_dotenv
from PIL import Image, ImageFile
from psaw import PushshiftAPI

from src.gallery_dl_helper import download_pic_from_url


ImageFile.LOAD_TRUNCATED_IMAGES = True  # else OsError

load_dotenv(find_dotenv(raise_error_if_not_found=True))


class PostSearchType(Enum):
    NEW = 1
    HOT = 2
    TOP = 3


def connect_to_postgres():
    connection = psycopg2.connect(
        user=os.environ.get("DB_USER_NAME"),
        password=os.environ.get("DB_USER_PASSWORD"),
        host="localhost",
        port=int(os.environ.get("DB_PORT")),
        database=os.environ.get("DB_NAME"),
    )
    connection.autocommit = True
    cursor = connection.cursor()
    return connection, cursor


def postgres_access(func):
    def wrapper(*args, **kwargs):
        conn, cur = connect_to_postgres()
        data = func(conn, cur, *args, **kwargs)
        close_postgres_connection(conn, cur)
        return data

    return wrapper


def close_postgres_connection(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()


def rename_latest_file_in_folder(folder: str, new_filename: str):
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
        return
    old_ext = file_path.suffix
    old_path = Path(file_path).resolve().parent
    new_path = Path(old_path, new_filename + old_ext)
    file_path.rename(new_path)
    return new_path


def get_latest_filename_in_folder(folder: str) -> Optional[Path]:
    download_folder = str(Path(f"./{folder}/*").absolute())
    try:
        last_file = max(glob.glob(download_folder), key=os.path.getctime)
    except ValueError:
        print("Couldnt find a file")
        return None

    return Path(last_file)


def get_filename_from_subm(subm):
    return str(int(subm.created_utc)) + "_" + str(subm.id)


def insert_pic_record(
    cursor,
    sub_name: str,
    post_id: str,
    author: str,
    title: str,
    url: str,
    created_utc: str,
    phash: str,
    wrong_format: bool,
):
    query = """INSERT INTO my_app_redditpost (sub_name, post_id, author, title, url, created_utc, phash, wrong_format)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(
        query,
        (
            sub_name,
            post_id,
            author,
            title,
            url,
            created_utc,
            phash,
            wrong_format,
        ),
    )


def does_post_id_exist(cursor, table_name: str, post_id: str) -> bool:
    """
    Returns True if post_id exists in database
    """
    query = """SELECT post_id FROM my_app_redditpost WHERE post_id=%s AND sub_name=%s"""

    cursor.execute(query, (post_id, table_name))
    data = cursor.fetchall()
    if data:
        return True
    else:
        return False


def get_last_post_time(cursor, table_name):
    query = """SELECT created_utc FROM my_app_redditpost WHERE sub_name=%s 
            ORDER BY created_utc DESC LIMIT 1"""

    cursor.execute(query, (table_name,))
    data = cursor.fetchall()
    return data


class Scraper:
    download_folder = "scrape_download"
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    def praw_scrape(
        self, subreddit_name: str, PRAW_MODE=PostSearchType.NEW, amount: int = 100
    ):
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn, cur = connect_to_postgres()
        r = praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent=os.environ.get("REDDIT_USER_AGENT"),
            username=os.environ.get("REDDIT_USERNAME"),
            password=os.environ.get("REDDIT_PASSWORD"),
        )

        # delete files in downloads folder
        clear_folder(self.download_folder)

        iter = r.subreddit(subreddit_name).new(limit=amount)

        if PRAW_MODE == PostSearchType.HOT:
            iter = r.subreddit(subreddit_name).hot(limit=amount)
        elif PRAW_MODE == PostSearchType.TOP:
            iter = r.subreddit(subreddit_name).top(limit=amount)

        filtered_submissions: List[Tuple[Any, bool, Optional[str]]] = []

        with cur:
            for subm in iter:
                # check if post id is already in database
                if does_post_id_exist(cur, subreddit_name, subm.id):
                    # print(f"Subm id already exists: {subm.id}")
                    continue

                if "minus.com" in subm.url:
                    filtered_submissions.append((subm, True, None))
                    continue

                did_load = download_pic_from_url(
                    url=subm.url, folder=self.download_folder
                )
                if did_load:
                    new_name = get_filename_from_subm(subm)
                    new_path = rename_latest_file_in_folder(
                        self.download_folder, new_name
                    )
                    is_wrong_format, phash = check_validity_and_phash(new_path)
                    filtered_submissions.append((subm, is_wrong_format, phash))
                else:
                    filtered_submissions.append((subm, True, None))

        clear_folder(self.download_folder)

        # add them to database
        inserted = add_filtered_submissions_to_db(
            conn, filtered_submissions, subreddit_name
        )

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"[{start_time}] {subreddit_name}: inserted {inserted} posts [{end_time}]"
        )
        close_postgres_connection(conn, cur)

    def psaw_scrape(self, subreddit_name: str, amount: int = 100):
        """
        0) Get latest created_utc from db or use the one provided by const
        1) Download pics
        2) Check if they can be opened with PIL and have sane dimensions etc
        3) Add them to database
        4) If inserted amount is 0 - exit, otherwise re:start.

        Args:
            amount (int, optional): Pushshift query amount. Defaults to 100.
        """
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn, cur = connect_to_postgres()

        # delete files in downloads folder
        clear_folder(self.download_folder)

        # get latest date from db and start downloading after it
        since_date = get_latest_created_utc_time_from_db(subreddit_name)
        # print(f"Starting download from: {since_date}")

        submissions = get_submissions(subreddit_name, since_date, amount)

        # try to download pics
        filtered_submissions: List[Tuple[Any, bool, Optional[str]]] = []
        with cur:
            for subm in submissions:
                if does_post_id_exist(cur, subreddit_name, subm.id):
                    continue
                if "minus.com" in subm.url:
                    filtered_submissions.append((subm, True, None))
                    continue

                did_load = download_pic_from_url(
                    url=subm.url, folder=self.download_folder
                )
                if did_load:
                    new_name = get_filename_from_subm(subm)
                    new_path = rename_latest_file_in_folder(
                        self.download_folder, new_name
                    )
                    is_wrong_format, phash = check_validity_and_phash(new_path)
                    filtered_submissions.append((subm, is_wrong_format, phash))
                else:
                    filtered_submissions.append((subm, True, None))

        clear_folder(self.download_folder)

        # add them to database
        inserted = add_filtered_submissions_to_db(
            conn, filtered_submissions, subreddit_name
        )

        close_postgres_connection(conn, cur)

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"[{start_time}] {subreddit_name}: inserted {inserted} posts [{end_time}]"
        )

        if inserted == 0:
            return
        else:
            self.psaw_scrape(subreddit_name)


def get_submissions(sub, sdate, amount):
    api = PushshiftAPI()
    gen = api.search_submissions(
        sort="asc",
        after=sdate,
        before=int(time.time()),
        subreddit=sub,
        filter=["title", "url", "author", "id", "created_utc"],
        limit=amount,
    )
    return list(gen)


@postgres_access
def get_latest_created_utc_time_from_db(_, cursor, subreddit_name):
    # TIME_OFFSET because reddit records may overlap
    TIME_OFFSET = 30
    with cursor:
        # this returns a tuple inside a list ...
        try:
            last_time = get_last_post_time(cursor, subreddit_name)
            since_date = str(int(last_time[0][0]) - TIME_OFFSET)
        except IndexError:  # if table is empty
            since_date = 111111  # random small number

    return since_date


def add_filtered_submissions_to_db(
    connection, filtered_submissions: list, subreddit_name: str
):
    inserted = 0
    for subm, wrong_format, img_hash in filtered_submissions:
        with connection:
            with connection.cursor() as cur:
                try:
                    insert_pic_record(
                        cursor=cur,
                        sub_name=subreddit_name,
                        post_id=str(subm.id),
                        author=str(subm.author),
                        title=str(subm.title),
                        url=str(subm.url),
                        created_utc=str(int(subm.created_utc)),
                        phash=img_hash,
                        wrong_format=wrong_format,
                    )

                    inserted += 1
                except psql_err.UniqueViolation:
                    connection.rollback()
                    continue
                except psql_err.StringDataRightTruncation:
                    connection.rollback()
                    continue

    return inserted


def clear_folder(folder_path):
    import os
    import shutil

    folder = folder_path
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))


def check_validity_and_phash(file_path: Path) -> Tuple[bool, Optional[str]]:
    """Go through reddit submission objects and check if the image is actually loaded.
    Then check if it open with PIL.Image() and has correct dimensions etc
    If everything is ok, return is_wrong_format=False and phash value of image.

    Returns:
        [type]: is_wrong_format, phash
    """
    warnings.simplefilter("error", Image.DecompressionBombWarning)

    try:  # if it DID load the picture, try to open it with PIL
        with Image.open(file_path) as im:
            width, height = im.size
            img_phash = str(imagehash.phash(im))
        # check image dimensions
        if not 500 < width + height < 14000:
            return True, img_phash

    except Exception:
        return True, None

    return False, img_phash


if __name__ == "__main__":
    fire.Fire(Scraper)
