import os

import psycopg2
import psycopg2.extras
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def connect_to_db():
    connection = psycopg2.connect(
        user=os.environ.get("DB_USER_NAME"),
        password=os.environ.get("DB_USER_PASSWORD"),
        host="localhost",
        port=int(os.environ.get("DB_PORT")),
        database=os.environ.get("DB_NAME"),
    )
    connection.autocommit = True
    return connection


def insert_vk_record(conn, scheduled_date: str, phash: str):
    with conn:
        with conn.cursor() as cursor:
            query = (
                """INSERT INTO my_app_vkpost (scheduled_date, phash) VALUES (%s, %s)"""
            )
            cursor.execute(query, (scheduled_date, phash))


def set_selected_status_by_phash(conn, status: bool, phash: str):
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET selected=(%s) WHERE phash=(%s) """
            cursor.execute(query, (status, phash))


def set_wrong_format_status_by_phash(conn, status: bool, phash: str):
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET wrong_format=(%s) WHERE phash=(%s) """
            cursor.execute(query, (status, phash))


def set_img_source_link_by_phash(conn, phash: str, source_link: str):
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET source_link=(%s) WHERE phash=(%s) """
            cursor.execute(query, (source_link, phash))


def set_visible_tags_by_phash(conn, phash: str, visible_tags: list):
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET visible_tags=(%s) WHERE phash=(%s) """
            cursor.execute(query, (visible_tags, phash))


def set_invisible_tags_by_phash(
    conn, phash: str, invisible_tags: list
):
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET invisible_tags=(%s) WHERE phash=(%s) """
            cursor.execute(query, (invisible_tags, phash))


def set_mal_id_by_phash(conn, phash: str, mal_id: int):
    with conn:
        with conn.cursor() as cursor:
            query = """UPDATE my_app_redditpost SET mal_id=(%s) WHERE phash=(%s) """
            cursor.execute(query, (mal_id, phash))


def get_approved_original_posts(conn):
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT post_id, sub_name, source_link, visible_tags, invisible_tags, phash
                    FROM my_app_redditpost 
                    WHERE selected=false 
                    AND dislike=false 
                    AND (mal_id=31687 OR mal_id IS NULL) 
                    ORDER BY random() 
                """
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_approved_anime_posts(conn, mal_id):
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT post_id, sub_name, source_link, visible_tags, invisible_tags, phash
                    FROM my_app_redditpost  
                    WHERE mal_id=(%s) 
                    AND selected=false 
                    AND dislike=false 
                """
            cursor.execute(query, (mal_id,))
            data = cursor.fetchall()
            return data


def get_all_approved_posts(conn):
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT mal_id, title, post_id, author, sub_name, phash, source_link, visible_tags 
                    FROM my_app_redditpost
                    WHERE selected=false 
                    AND dislike=false 
                    AND phash IS NOT NULL"""
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def aggregate_approved_mal_id_counts(conn):
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT DISTINCT COUNT(mal_id) 
                    OVER(PARTITION BY mal_id) AS id_count, mal_id 
                    FROM my_app_redditpost
                    WHERE selected=false
                    AND dislike=false 
                    ORDER BY id_count desc"""
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_disliked_posts(conn):
    with conn:
        with conn.cursor() as cursor:
            query = """SELECT sub_name, post_id, phash
                    FROM my_app_redditpost
                    WHERE selected=false
                    AND dislike=true 
                    """
            cursor.execute(query)
            data = cursor.fetchall()
            return data
