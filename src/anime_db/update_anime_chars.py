from jikanpy import Jikan

from ..postgres import connect_to_db

# python -m src.anime_db.update_anime_chars


def insert_char_into_db(conn, anime_mal_id, character_mal_id, name, image_url, role):
    name = name.replace(",", " ")
    name_array = name.split()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO anime_characters (anime_mal_id,character_mal_id, name_array, image_url, role) VALUES (%s,%s,%s,%s,%s)",
                (anime_mal_id, character_mal_id, name_array, image_url, role),
            )

    print(f"Added: {name_array}")


def get_characters_for_anime_id(mal_id):
    jikan = Jikan()
    res = jikan.anime(mal_id, extension="characters_staff")
    chars_list = res["characters"]
    # pprint(chars_list)
    result_list = [
        (char["mal_id"], char["name"], char["image_url"], char["role"])
        for char in chars_list
    ]
    # pprint(result_list)
    return result_list


if __name__ == "__main__":
    conn = connect_to_db()
    res = get_characters_for_anime_id(426)
    print(res)
    # insert_char_into_db(conn, 14359, -12, 'Hatsune, Miku', image_url=None, role='Main')
