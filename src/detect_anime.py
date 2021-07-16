import re

from psycopg2 import sql
from slugify import slugify

try:
    from postgres import connect_to_db
except ModuleNotFoundError:
    from src.postgres import connect_to_db

from dataclasses import dataclass
from typing import Optional

AnimeInfo = tuple[int, str, str, str, str]


@dataclass
class AnimeDetection:
    anime_info: AnimeInfo
    func_name : str
    is_from_anime: bool
    column: Optional[str] = None

    def __post_init__(self):
        self.anime_id = self.anime_info[0]


def get_text_inside_brackets(text: str) -> list[str]:
    # returns all text inside (multiple) brackets
    # example: My fav anime picture [Sponge Bob Square Pants] -> returns only: Sponge Bob Square Pants
    square_brackets_pattern = r"\[(.*?)\]"
    round_brackets_pattern = r"\((.*?)\)"

    result_list = []
    for pattern in [square_brackets_pattern, round_brackets_pattern]:
        res = re.findall(pattern, text)
        result_list += res

    # attempt to fix missing brackets
    if not result_list:
        if "[" in text and "]" not in text:
            text += "]"
            res = re.findall(square_brackets_pattern, text)
            result_list += res
            return result_list

        elif "(" in text and ")" not in text:
            text += ")"
            res = re.findall(round_brackets_pattern, text)
            result_list += res
            return result_list

    return result_list


def is_valid_url(url: str):
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return re.match(regex, url)


def get_number_count_from_string(input_string: str):
    return sum(c.isdigit() for c in input_string)


def text_is_equal_to_column(
    conn, table_name: str, column_name: str, input_text: str
) -> AnimeInfo:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT anime_id,slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
                WHERE {1} NOT LIKE '%%PV%%' 
                AND lower({1})=lower(%s) 
                ORDER BY anime_id ASC"""
            ).format(sql.Identifier(table_name), sql.Identifier(column_name))

            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            return data


def slug_text_is_equal_to_slug_column(
    conn, table_name: str, column_name: str, input_text: str
) -> AnimeInfo:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT anime_id,slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
                WHERE slugify(%s) != '' 
                AND {1} NOT LIKE '%%PV%%' 
                AND slugify({1})=slugify(%s) 
                ORDER BY anime_id ASC"""
            ).format(sql.Identifier(table_name), sql.Identifier(column_name))

            cursor.execute(query, (input_text, input_text))
            data = cursor.fetchall()
            return data


def text_is_in_synonyms_array(conn, table_name: str, input_text: str) -> AnimeInfo:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT anime_id,slugify(title_syn), slugify(title_english), title_russian, franchise 
                FROM {0}, UNNEST(lower({0}.title_synonyms::text)::text[]) AS title_syn
                WHERE lower(%s) = title_syn
                ORDER BY anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            return data


def text_is_in_slugified_synonyms_array(
    conn, table_name: str, input_text: str
) -> AnimeInfo:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT anime_id, slugify(slug_title_syn), slugify(title_english), title_russian, franchise 
                FROM {0}, UNNEST(slugify_array({0}.title_synonyms)) as slug_title_syn
                WHERE slugify(%s) = slug_title_syn
                ORDER BY anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            return data


def text_is_substring_of_franchise(
    conn, table_name: str, input_text: str
) -> Optional[AnimeInfo]:
    """Example: input is 'sword_art' which is substring of franchise 'sword_art_online'

    Returns:
        int: anime_id
    """
    input_text = slugify(input_text)
    input_text = input_text.replace("-", "_")
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT DISTINCT ON(franchise) anime_id, slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
                WHERE franchise LIKE '%%' || (%s) || '%%' 
                ORDER BY franchise,anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_without_spaces_is_equal_to_franchise_column(
    conn, table_name: str, input_text: str
) -> Optional[AnimeInfo]:
    input_text = slugify(input_text)
    input_text = input_text.replace("-", "")
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT DISTINCT ON(franchise) anime_id, slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
                WHERE REPLACE(franchise, '_', '') = (%s) 
                ORDER BY franchise,anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_without_spaces_is_equal_to_title(
    conn, table_name: str, input_text: str
) -> Optional[AnimeInfo]:
    input_text = slugify(input_text)
    input_text = input_text.replace("-", "")
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT anime_id, slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
                WHERE REPLACE(slugify(title), '-', '') = (%s) 
                ORDER BY anime_id ASC"""
            ).format(sql.Identifier(table_name))
            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_without_spaces_is_equal_to_title_english(
    conn, table_name: str, input_text: str
) -> Optional[AnimeInfo]:
    input_text = slugify(input_text)
    input_text = input_text.replace("-", "")
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT anime_id, slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
                WHERE REPLACE(slugify(title_english), '-', '') = (%s) 
                ORDER BY anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_without_spaces_is_in_synonyms(
    conn, table_name: str, input_text: str
) -> Optional[AnimeInfo]:
    input_text = slugify(input_text)
    input_text = input_text.replace("-", "")
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT DISTINCT ON(franchise) anime_id,slugify(slug_title_syn), slugify(title_english), title_russian, franchise 
                FROM {0}, UNNEST(slugify_array({0}.title_synonyms)) as slug_title_syn
                WHERE REPLACE(slugify(slug_title_syn), '-', '') = (%s)
                ORDER BY franchise, anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (input_text,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_is_substring_of_slug_title(
    conn, table_name: str, text_input: str
) -> Optional[AnimeInfo]:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT DISTINCT ON(franchise) anime_id,slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
            WHERE slugify(title) LIKE '%%' || slugify(%s) || '%%' 
            ORDER BY franchise,anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (text_input,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_is_substring_of_slug_title_english(
    conn, table_name: str, text_input: str
) -> Optional[AnimeInfo]:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT DISTINCT ON(franchise) anime_id, slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
            WHERE slugify(title_english) LIKE '%%' || slugify(%s) || '%%' 
            ORDER BY franchise,anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (text_input,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_is_substring_of_slug_synonym_array(
    conn, table_name: str, text_input: str
) -> Optional[AnimeInfo]:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT DISTINCT ON(franchise) anime_id,slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
            WHERE EXISTS (SELECT FROM unnest(slugify_array(title_synonyms)) elem 
            WHERE  elem LIKE '%%' || slugify(%s) || '%%') 
            ORDER BY franchise, anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (text_input,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def text_is_substring_of_synonym_array(
    conn, table_name: str, text_input: str
) -> Optional[AnimeInfo]:
    with conn:
        with conn.cursor() as cursor:
            query = sql.SQL(
                """SELECT DISTINCT ON(franchise) anime_id, slugify(title), slugify(title_english), title_russian, franchise FROM {0} 
            WHERE EXISTS (SELECT FROM unnest(title_synonyms) elem 
            WHERE  elem LIKE '%%' || slugify(%s) || '%%') 
            ORDER BY franchise, anime_id ASC"""
            ).format(sql.Identifier(table_name))

            cursor.execute(query, (text_input,))
            data = cursor.fetchall()
            if len(data) == 1:
                return data
            else:
                return None


def deal_with_resolutions(input_string: str):
    # solve [Sword Art Online, 1280×800] - delete resolution numbers
    # get rid of ×
    input_string = input_string.replace("×", "x")
    input_str = re.sub(r"(\d{2,4}x\d{2,4})+", "", input_string)
    return input_str


#########################################################
# the order of functions below is very (!) important and
# they are used locally in this file
#########################################################
DIRECT_SEARCH_FUNCS: list = [text_is_equal_to_column, slug_text_is_equal_to_slug_column]

LESS_ACCURATE_SEARCH_FUNCS: list = [
    text_is_in_synonyms_array,
    text_is_in_slugified_synonyms_array,
    text_without_spaces_is_equal_to_title,
    text_without_spaces_is_equal_to_title_english,
    text_without_spaces_is_equal_to_franchise_column,
    # inaccurate from now on
    text_without_spaces_is_in_synonyms,
    text_is_substring_of_slug_title,
    text_is_substring_of_slug_title_english,
    text_is_substring_of_synonym_array,
    text_is_substring_of_slug_synonym_array,
    text_is_substring_of_franchise,
]
#########################################################
# the functions below are used in other file
# for judgement algorithm
# we need to make sure that they are the same
# as the ones used for detection
#########################################################
JUST_USE_TITLE: list = [
    text_is_equal_to_column,
    slug_text_is_equal_to_slug_column,
    text_without_spaces_is_equal_to_title,
    text_without_spaces_is_equal_to_title_english,
    text_is_substring_of_slug_title,
    text_is_substring_of_slug_title_english,
]

JUST_USE_SYNONYM_TITLE: list = [
    text_is_in_synonyms_array,
    text_is_in_slugified_synonyms_array,
    text_without_spaces_is_in_synonyms,
]

JUST_USE_FRANCHISE: list = [
    text_without_spaces_is_equal_to_franchise_column,
    text_is_substring_of_franchise,
]

MAYBE_USE_FRANCHISE: list = [
    text_is_substring_of_synonym_array,
    text_is_substring_of_slug_synonym_array,
]

# make sure the functions that are used for judgement algorithm
# are the same ones used detection locally
assert len(DIRECT_SEARCH_FUNCS + LESS_ACCURATE_SEARCH_FUNCS) == len(
    JUST_USE_TITLE + JUST_USE_SYNONYM_TITLE + JUST_USE_FRANCHISE + MAYBE_USE_FRANCHISE
)


def detect_anime_from_string(conn, input_text) -> Optional[AnimeDetection]:
    """
    0) Prepare text:
        0.0) lowercase and strip leading and trailing whitespace
        0.1) remove multiple whitespaces
        0.2) solve [Sword Art Online, 1280×800]
        0.3) idolm@@@ster
        0.4) only numbers title - is garbage
        0.5) replace &amp; with &
        0.6)  daily idolmaster --> Daily iDOLM@STER #236

    Then attempt to find anime, with methods ordered from highest accuracy to lowest

    """
    if not input_text:
        return None

    if is_valid_url(input_text):
        return None

    input_text = input_text.lower()

    # do deletions first
    if get_number_count_from_string(input_text) > 4:
        input_text = deal_with_resolutions(input_text)

    if "@" in input_text:
        input_text = input_text.replace("@", "a")

    if "&amp;" in input_text:
        input_text = input_text.replace("&amp;", "&")

    input_text = input_text.strip()
    input_text = " ".join(input_text.split())

    for table in ["non_anime", "anime"]:
        # check direct equality to column
        column_names = ["title", "title_english"]
        for column in column_names:
            for count, func in enumerate(DIRECT_SEARCH_FUNCS):
                if anime_info := func(conn, table, column, input_text):
                    # we need to store the function that found the anime
                    func_name = DIRECT_SEARCH_FUNCS[count].__name__
                    # we have 2 different tables with similar structure, we need to know where to look
                    detected_anime = AnimeDetection(
                        anime_info=anime_info[0],
                        func_name=func_name,
                        is_from_anime=True if table == "anime" else False,
                        column=column,
                    )

                    return detected_anime

    for table in ["non_anime", "anime"]:
        for count, func in enumerate(LESS_ACCURATE_SEARCH_FUNCS):
            func_name = LESS_ACCURATE_SEARCH_FUNCS[count].__name__
            if anime_info := func(conn, table, input_text):
                detected_anime = AnimeDetection(
                    anime_info=anime_info[0],
                    func_name=func_name,
                    is_from_anime=True if table == "anime" else False,
                )

                return detected_anime

    if "&" in input_text:
        input_text = input_text.replace("&", "and")
        res = detect_anime_from_string(conn, input_text)
        if res:
            return res

    if "series" in input_text:
        input_text = input_text.replace("series", "")
        res = detect_anime_from_string(conn, input_text)
        if res:
            return res

    # sometimes there are two titles split by comma, or slash
    try_again_chars = [",", "/", " x ", "-", ":"]
    for char in try_again_chars:
        if char in input_text and input_text.count(char) < 2:
            possible_titles = input_text.split(char)
            for title in possible_titles:
                res = detect_anime_from_string(conn, title)
                if res:
                    return res

    # or by some words
    try_again_words = ["from", "and", "or"]
    for word in try_again_words:
        if word in input_text.split(" ") and input_text.split(" ").count(word) < 2:
            possible_titles = input_text.split(word)
            for title in possible_titles:
                res = detect_anime_from_string(conn, title)
                if res:
                    return res

    return None


def main():
    conn = connect_to_db()
    input_str = "Girl's Last Tour"
    res = detect_anime_from_string(conn, input_str)
    print(res)


if __name__ == "__main__":
    main()
