import json
import time
import os
import jikanpy
from jikanpy import Jikan
import pathlib
from ..postgres import connect_to_db


# python -m src.anime_db.update_anime_with_jikan
HOME_PATH = os.environ.get("HOME")
PATH_TO_MAL_ID_CACHE = str(
    pathlib.Path(HOME_PATH, "mal-id-cache/cache/anime_cache.json")
)


def get_all_ids_from_db(conn):
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT anime_id FROM anime")
            data = cursor.fetchall()
            result_list = []
            for item in data:
                result_list.append(item[0])
            return result_list


def get_ids_from_mal_id_cache():
    with open(PATH_TO_MAL_ID_CACHE) as f:
        data = json.load(f)

        sfw_list = data["sfw"]
        nsfw_list = data["nsfw"]
        all_ids = set(sfw_list + nsfw_list)
        return all_ids


def parse_is_airing_status(status: str):
    if status == "Currently Airing":
        return True
    elif status == "Finished Airing":
        return False
    else:
        return None


def check_synonyms(conn):
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT title_synonyms FROM anime WHERE anime_id=28121")
            data = cursor.fetchall()
            return data


def add_jikan_response_to_db(conn, jikan_obj):
    anime_id = jikan_obj["mal_id"]
    title = jikan_obj["title"]
    image_path = jikan_obj["image_url"]
    mpaa_rating = jikan_obj["rating"]
    title_japanese = jikan_obj["title_japanese"]
    title_english = jikan_obj["title_english"]
    title_synonyms = jikan_obj["title_synonyms"]

    status = jikan_obj["status"]
    airing_status = parse_is_airing_status(status)

    genres = jikan_obj["genres"]
    genres = [item["name"] for item in genres]

    studios = jikan_obj["studios"]
    studios = [item["name"] for item in studios]

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO anime (title,anime_id,image_path,mpaa_rating, title_japanese, title_english, title_synonyms, genres,studios, is_airing) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    title,
                    anime_id,
                    image_path,
                    mpaa_rating,
                    title_japanese,
                    title_english,
                    title_synonyms,
                    genres,
                    studios,
                    airing_status,
                ),
            )

    print(f"Added: {title}")


def main():
    conn = connect_to_db()
    db_ids = get_all_ids_from_db(conn)
    cache_ids = get_ids_from_mal_id_cache()
    left_over_ids = [cached_id for cached_id in cache_ids if cached_id not in db_ids]
    print(len(left_over_ids))

    # print(left_over_ids)
    jikan = Jikan()
    for anime_id in left_over_ids:
        try:
            anime = jikan.anime(anime_id)
        except jikanpy.exceptions.APIException:
            continue
        add_jikan_response_to_db(conn, anime)
        time.sleep(2)

    conn.close()


if __name__ == "__main__":
    main()
