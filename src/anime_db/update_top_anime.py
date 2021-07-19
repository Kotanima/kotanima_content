from os import times
import psycopg2
from ..postgres import connect_to_db
import jikanpy
from jikanpy import Jikan
from pprint import pprint
import time

# python -m src.anime_db.update_top_anime


def insert_top_anime_record(conn, mal_id: int) -> None:
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO top_anime (anime_id) VALUES (%s)", (mal_id,))


def main():
    conn = connect_to_db()
    jikan = Jikan()
    for i in range(1, 171):
        anime = jikan.top(type="anime", page=i)
        top_anime = anime["top"]
        for anime in top_anime:
            mal_id = anime["mal_id"]
            try:
                insert_top_anime_record(conn, mal_id=mal_id)
            except psycopg2.errors.UniqueViolation:
                pass

        time.sleep(2)

    conn.close()


if __name__ == "__main__":
    main()
