from jikanpy import Jikan
import psycopg2
from ..postgres import connect_to_db


# python -m src.anime_db.update_non_anime_chars


def insert_non_anime_character(conn, non_anime_id, name_array, image_url):
    """Insert only 1 character at a time. Name array - because 1 character can have nicknames/other names"""
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO non_anime_characters (anime_mal_id,name_array,image_url)
                   VALUES (%s,%s,%s)""",
                (non_anime_id, name_array, image_url),
            )


char_list = [
    "Kazuha",
    "Ayaka",
    "Yoimiya",
    "Sayu",
    "Gorou",
    "Thoma",
    "Yae Miko",
    "Kajou Sara",
    "Shogun",
    "Sangonomiya Kokomi",
    "Aloy",
    "Dainsleif",
    "Yunjin",
    "Yaoyao",
    "Kate",
    "Shenhe",
    "Baizhu",
    "Cyno",
    "Collei",
    "Lyney and Lynette",
    "Iansan",
    "Signora",
    "Scaramouche",
    "Dottore",
    "Pulcinella",
]

if __name__ == "__main__":
    pass
    conn = connect_to_db()

    for char in char_list:
        insert_non_anime_character(
            conn, non_anime_id=7, name_array=[f"{char}"], image_url=None
        )

    conn.close()
