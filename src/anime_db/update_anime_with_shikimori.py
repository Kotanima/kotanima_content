import requests
from shikimori_api import Shikimori
import time
from ..postgres import connect_to_db

# python -m src.anime_db.update_anime_with_shikimori


def get_anime_ids_and_title_synonyms_list(conn):
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT anime_id FROM anime WHERE title_russian IS NOT NULL ORDER BY anime_id desc LIMIT 1"
            )
            max_ind = cursor.fetchone()
            max_ind = max_ind[0]
            print(f"{max_ind=}")

    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT anime_id,title_synonyms FROM anime WHERE title_russian IS NULL AND anime_id>(%s) ORDER BY anime_id",
                (max_ind,),
            )
            data = cursor.fetchall()
            return data


def insert_franchise(conn, input_franchise, anime_id):
    with conn:
        with conn.cursor() as cursor:
            query = "UPDATE anime SET franchise=%s WHERE anime_id=%s"
            cursor.execute(query, (input_franchise, anime_id))


def insert_russian_title(conn, input_title, anime_id):
    with conn:
        with conn.cursor() as cursor:
            query = "UPDATE anime SET title_russian=%s WHERE anime_id=%s"
            cursor.execute(query, (input_title, anime_id))


def insert_synonyms(conn, one_synonym, anime_id):
    with conn:
        with conn.cursor() as cursor:
            query = "UPDATE anime SET title_synonyms = title_synonyms || (%s) WHERE anime_id=(%s)"
            cursor.execute(query, (one_synonym, anime_id))


def query_shikimori(conn, mal_id, existing_synonyms):
    session = Shikimori()
    api = session.get_api()
    try:
        api_response = api.anime(mal_id).GET()
    except requests.exceptions.HTTPError:
        print(f"Http error for {mal_id=}")
        return

    russian_title = api_response.get("russian")
    print(russian_title)
    synonyms = api_response.get("synonyms")
    franchise = api_response.get("franchise")

    if franchise:
        insert_franchise(conn, franchise, mal_id)

    if russian_title:
        insert_russian_title(conn, russian_title, mal_id)

    if synonyms:
        if existing_synonyms:
            new_syn_list = [syn for syn in synonyms if syn not in existing_synonyms]
        else:
            new_syn_list = synonyms

        if new_syn_list:
            insert_synonyms(conn, new_syn_list, mal_id)

    time.sleep(1)


if __name__ == "__main__":
    conn = connect_to_db()
    anime_info = get_anime_ids_and_title_synonyms_list(conn)
    print(len(anime_info))
    for anime_id, exist_syn_list in anime_info:
        print(anime_id)
        query_shikimori(conn, anime_id, exist_syn_list)

    conn.close()
