"""
Get all files in database where is_downloaded=True
check if they actually exist on disk
"""

import psycopg2
from dotenv import load_dotenv, find_dotenv

from postgres import connect_to_db, set_downloaded_status_by_phash, get_downloaded_posts
from models import IdentifiedRedditPost
from pathlib import Path
import os

# load configuration
load_dotenv(find_dotenv(raise_error_if_not_found=True))

STATIC_FOLDER_PATH = os.getenv("STATIC_FOLDER_PATH")


def verify_downloaded_files():
    conn = connect_to_db()
    database_marked_downloaded_files = get_downloaded_posts(conn)
    for post_info in database_marked_downloaded_files:
        reddit_post = IdentifiedRedditPost(
            post_id=post_info[0],
            sub_name=post_info[1],
            phash=post_info[2],
            is_downloaded=post_info[3],
        )
        if not reddit_post.is_downloaded:
            raise Exception(
                "Posts gathered from database should have been marked as downloaded"
            )

        current_file = Path(STATIC_FOLDER_PATH, reddit_post.get_image_name())
        if not current_file.is_file():
            print(f"File DOESNT EXIST: {str(current_file)}")
            set_downloaded_status_by_phash(conn, status=False, phash=reddit_post.phash)

    if conn:
        conn.close()


if __name__ == "__main__":
    verify_downloaded_files()
