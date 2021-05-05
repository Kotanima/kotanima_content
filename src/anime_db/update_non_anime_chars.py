from jikanpy import Jikan
import psycopg2
from ..postgres import connect_to_db


# python -m src.anime_db.update_non_anime_chars


def insert_non_anime_character(conn, non_anime_id, name_array, image_url):
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO non_anime_characters (non_anime_id,name_array,image_url)
                   VALUES (%s,%s,%s)""",
                (non_anime_id, name_array, image_url),
            )


if __name__ == "__main__":
    pass
    # conn = connect_to_db()

    # insert_non_anime_character(conn, non_anime_id=7, name_array=["Lumine"],
    #                            image_url=None)
