from collections import namedtuple

import attr
from jikanpy import Jikan
import jikanpy
from typing import Optional
from ..postgres import connect_to_db

# python -m src.anime_db.update_anime_chars


@attr.s
class AnimeCharacter:
    character_mal_id: int = attr.ib()
    name: str = attr.ib()
    image_url: str = attr.ib()
    role: str = attr.ib()

    @classmethod
    def from_api(cls, obj):
        return cls(obj["mal_id"], obj["name"], obj["image_url"], obj["role"])


def insert_char_into_db(
    conn,
    anime_mal_id: int,
    character_mal_id: int,
    name: str,
    image_url: str,
    role: str,
) -> None:
    name = name.replace(",", " ")
    name_array = name.split()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO anime_characters (anime_mal_id,character_mal_id, name_array, image_url, role) VALUES (%s,%s,%s,%s,%s)",
                (anime_mal_id, character_mal_id, name_array, image_url, role),
            )

    print(f"Added: {name_array}")


def get_characters_for_anime_id(mal_id: int) -> Optional[list[AnimeCharacter]]:
    jikan = Jikan()
    try:
        res = jikan.anime(mal_id, extension="characters_staff")
    except jikanpy.APIException:
        print(f"Character api error for {mal_id=}")
        return None
    chars_list = res["characters"]
    result_chars_list = [AnimeCharacter.from_api(char) for char in chars_list]
    return result_chars_list


def do_chars_exist_in_db(conn, mal_id: int) -> bool:
    """
    Args:
        conn ([type]): database connection
        mal_id (int): myanimelist id

    Returns:
        bool: returns true if there are character records for anime id
    """
    with conn:
        with conn.cursor() as cursor:
            query = """select exists(select 1 from anime_characters where id=(%s))"""
            cursor.execute(query, (mal_id,))
            res = cursor.fetchall()
            return res[0][0]


def find_and_insert_anime_chars_for_mal_id(conn, anime_mal_id: int) -> None:
    if not do_chars_exist_in_db(conn, mal_id=anime_mal_id):
        char_list = get_characters_for_anime_id(anime_mal_id)
        if not char_list:
            return
        for char in char_list:
            insert_char_into_db(
                conn,
                anime_mal_id=anime_mal_id,
                character_mal_id=char.character_mal_id,
                name=char.name,
                image_url=char.image_url,
                role=char.role,
            )
    else:
        print(f"Chars already exist for {anime_mal_id}")


if __name__ == "__main__":
    conn = connect_to_db()
    MAL_ID = 41025
    # find_and_insert_anime_chars_for_mal_id(conn, MAL_ID)
    # insert_char_into_db(
    #     conn,
    #     anime_mal_id=44042,
    #     character_mal_id=-12,
    #     name="IRyS",
    #     image_url=None,
    #     role="Main",
    # )
    conn.close()
