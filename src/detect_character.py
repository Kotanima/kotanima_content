"""
Find if the text contains a character name 
"""

from psycopg2 import sql


def detect_character(conn, text: str, mal_id: int, is_anime: bool):
    words_arr = text.split()
    # delete words with len <= 2
    words_arr = [word for word in words_arr if len(word) > 2]
    # sort the array so the longest words with capital letters come first
    words_arr.sort(key=lambda s: (sum(map(str.isupper, s)), len(s)), reverse=True)

    if is_anime:
        table_name = "anime_characters"
    else:
        table_name = "non_anime_characters"

    for func in [
        _get_main_char_from_db,
        _get_supporting_char_from_db,
        _get_slug_main_char_from_db,
        _get_slug_supporting_char_from_db,
    ]:
        for word in words_arr:
            if res := func(conn, table_name, mal_id, word):
                return "_".join(res[0][0])

    # attempt to find character in the same franchise
    franchise = _get_franchise_from_id(conn, is_anime, mal_id)
    id_list = _get_ids_for_franchise(conn, is_anime, franchise)
    for id_tuple in id_list:
        mal_id = id_tuple[0]
        for func in [
            _get_main_char_from_db,
            _get_supporting_char_from_db,
            _get_slug_main_char_from_db,
            _get_slug_supporting_char_from_db,
        ]:
            for word in words_arr:
                if res := func(conn, table_name, mal_id, word):
                    return "_".join(res[0][0])


def _get_franchise_from_id(conn, is_anime: bool, anime_id: int):
    if is_anime:
        table_name = "anime"
    else:
        table_name = "non_anime"

    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL("""SELECT franchise FROM {0} WHERE anime_id=%s""").format(
                sql.Identifier(table_name)
            )

            cursor.execute(query, (anime_id,))
            data = cursor.fetchone()
            return data


def _get_ids_for_franchise(conn, is_anime: bool, franchise: str):
    if is_anime:
        table_name = "anime"
    else:
        table_name = "non_anime"

    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL("""SELECT anime_id FROM {0} WHERE franchise=%s""").format(
                sql.Identifier(table_name)
            )

            cursor.execute(query, (franchise,))
            data = cursor.fetchall()
            return data


def _get_main_char_from_db(conn, table_name: str, mal_id: int, input_text: str):
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """
                SELECT name_array FROM {0} 
                WHERE lower(%s) = ANY(lower(name_array::text)::text[])
                AND role='Main' 
                AND anime_mal_id= %s"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text, mal_id))
            data = cursor.fetchall()
            if len(data) == 1:
                return data

            else:
                return None


def _get_supporting_char_from_db(conn, table_name: str, mal_id: int, input_text: str):
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """
            SELECT name_array FROM {0} 
            WHERE lower(%s) = ANY(lower(name_array::text)::text[]) 
            AND role='Supporting' 
            AND anime_mal_id= %s"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text, mal_id))
            data = cursor.fetchall()
            if len(data) == 1:
                return data

            else:
                return None


def _get_slug_main_char_from_db(conn, table_name: str, mal_id: int, input_text: str):
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """
            SELECT name_array FROM {0} 
            WHERE slugify(%s) = ANY(slugify_array(name_array)) 
            AND role='Main' 
            AND anime_mal_id= %s"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text, mal_id))
            data = cursor.fetchall()
            if len(data) == 1:
                return data

            else:
                return None


def _get_slug_supporting_char_from_db(
    conn, table_name: str, mal_id: int, input_text: str
):
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """
                SELECT name_array FROM {0} 
                WHERE slugify(%s) = ANY(slugify_array(name_array)) 
                AND role='Supporting' 
                AND anime_mal_id= %s"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text, mal_id))
            data = cursor.fetchall()
            if len(data) == 1:
                return data

            else:
                return None


if __name__ == "__main__":
    pass
