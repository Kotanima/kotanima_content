"""
Most of the common interactions with the postgres database are stored here
"""
from collections import namedtuple
import os
from typing import Type
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def connect_to_db() -> connection:
    connection = psycopg2.connect(
        user=os.environ.get("DB_USER_NAME"),
        password=os.environ.get("DB_USER_PASSWORD"),
        host="localhost",
        port=int(os.environ.get("DB_PORT")),  # type: ignore
        database=os.environ.get("DB_NAME"),  # type: ignore
    )
    connection.autocommit = True
    return connection


def is_top_anime(anime_id: int) -> bool:
    """Check if input anime id is in top_anime postgres table
    Args:
        anime_id (int): MyAnimeList anime id

    Returns:
        bool: True if anime is/was popular
    """
    conn = connect_to_db()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM top_anime WHERE anime_id=(%s))",
                (anime_id,),
            )
            data = cursor.fetchone()

    conn.close()
    return data[0]


def insert_vk_record(conn, scheduled_date: str, phash: str) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = (
                """INSERT INTO my_app_vkpost (scheduled_date, phash) VALUES (%s, %s)"""
            )
            cursor.execute(query, (scheduled_date, phash))


def set_downloaded_status_by_phash(conn, status: bool, phash: str) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = (
                """UPDATE my_app_redditpost SET is_downloaded=(%s) WHERE phash=(%s) """
            )
            cursor.execute(query, (status, phash))


def set_checked_status_by_phash(conn, status: bool, phash: str) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET is_checked=(%s) WHERE phash=(%s) """
            cursor.execute(query, (status, phash))


def set_disliked_status_by_phash(conn, status: bool, phash: str) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = (
                """UPDATE my_app_redditpost SET is_disliked=(%s) WHERE phash=(%s) """
            )
            cursor.execute(query, (status, phash))


def set_wrong_format_status_by_phash(conn, status: bool, phash: str) -> None:
    # somewhere around here i wish i used an ORM
    with conn:
        with conn.cursor() as cursor:
            query = (
                """UPDATE my_app_redditpost SET wrong_format=(%s) WHERE phash=(%s) """
            )
            cursor.execute(query, (status, phash))


def set_img_source_link_by_phash(conn, phash: str, source_link: str) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = (
                """UPDATE my_app_redditpost SET source_link=(%s) WHERE phash=(%s) """
            )
            cursor.execute(query, (source_link, phash))


def set_visible_tags_by_phash(conn, phash: str, visible_tags: list) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = (
                """UPDATE my_app_redditpost SET visible_tags=(%s) WHERE phash=(%s) """
            )
            cursor.execute(query, (visible_tags, phash))


def set_invisible_tags_by_phash(conn, phash: str, invisible_tags: list) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = (
                """UPDATE my_app_redditpost SET invisible_tags=(%s) WHERE phash=(%s) """
            )
            cursor.execute(query, (invisible_tags, phash))


def set_mal_id_by_phash(conn, phash: str, mal_id: int) -> None:
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET mal_id=(%s) WHERE phash=(%s) """
            cursor.execute(query, (mal_id, phash))


def get_approved_original_posts(conn) -> dict:
    """
    Get orginal reddit posts that were manually checked and approved.
    """
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            query = """SELECT post_id, sub_name, source_link, visible_tags, invisible_tags, phash
                    FROM my_app_redditpost 
                    WHERE is_downloaded=true
                    AND (phash NOT IN (SELECT phash FROM my_app_vkpost))
                    AND (phash NOT IN (SELECT DISTINCT phash FROM my_app_redditpost where is_disliked=true))
                    AND is_checked=true
                    AND is_disliked=false 
                    AND (mal_id=31687 OR mal_id IS NULL) 
                    ORDER BY random() 
                """
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_downloaded_posts(conn) -> dict:
    """
    Get reddit posts where images were loaded into static folder
    """
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            query = """
                    SELECT post_id, sub_name, phash, is_downloaded
                    FROM my_app_redditpost  
                    WHERE is_downloaded=true
                    """
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_approved_anime_posts(conn, mal_id) -> dict:
    """
    Get reddit posts for some anime, that were manually checked and approved.
    """
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            query = """SELECT post_id, sub_name, source_link, visible_tags, invisible_tags, phash
                    FROM my_app_redditpost  
                    WHERE mal_id=(%s) 
                    AND (phash NOT IN (SELECT phash FROM my_app_vkpost))
                    AND (phash NOT IN (SELECT DISTINCT phash FROM my_app_redditpost where is_disliked=true))
                    AND is_downloaded=true
                    AND is_checked=true
                    AND is_disliked=false 

                """
            cursor.execute(query, (mal_id,))
            data = cursor.fetchall()
            return data


def get_posts_for_metadata(conn):
    """
    Approved posts that dont have any metadata yet.
    """
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT mal_id, title, post_id, author, sub_name, phash, source_link, visible_tags, invisible_tags
                    FROM my_app_redditpost
                    WHERE visible_tags is NULL
                    AND is_downloaded=true 
                    AND (phash NOT IN (SELECT phash FROM my_app_vkpost))
                    AND (phash NOT IN (SELECT DISTINCT phash FROM my_app_redditpost where is_disliked=true))
                    AND is_checked=true
                    AND is_disliked=false
                    AND phash IS NOT NULL
                    AND wrong_format=false
                    """
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_all_approved_posts(conn):
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT mal_id, title, post_id, author, sub_name, phash, source_link, visible_tags, invisible_tags
                    FROM my_app_redditpost
                    WHERE is_downloaded=true 
                    AND (phash NOT IN (SELECT phash FROM my_app_vkpost))
                    AND (phash NOT IN (SELECT DISTINCT phash FROM my_app_redditpost where is_disliked=true))
                    AND is_checked=true
                    AND is_disliked=false
                    AND phash IS NOT NULL"""
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def aggregate_approved_mal_id_counts(conn) -> Type[tuple]:
    """
    Returns most frequent MAL ids (aka most popular shows)
    """
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT DISTINCT COUNT(mal_id) 
                    OVER(PARTITION BY mal_id) AS id_count, mal_id 
                    FROM my_app_redditpost
                    WHERE is_downloaded=true
                    AND (phash NOT IN (SELECT phash FROM my_app_vkpost))
                    AND (phash NOT IN (SELECT DISTINCT phash FROM my_app_redditpost where is_disliked=true))
                    AND is_checked=true
                    AND is_disliked=false 
                    ORDER BY id_count desc"""
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_disliked_posts(conn):
    # for deleting them, so get only the ones that are actually downloaded
    with conn:
        with conn.cursor() as cursor:
            query = """SELECT sub_name, post_id, phash
                    FROM my_app_redditpost
                    WHERE is_downloaded=true
                    AND is_disliked=true 
                    """
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def main():
    conn = connect_to_db()
    res = get_approved_anime_posts(conn, 44042)
    print(res)
    print(dir(res))
    print(type(res))
    print(res[0])
    print(type(res[0]))
    print(list(res[0].keys()))
    conn.close()


if __name__ == "__main__":
    main()
