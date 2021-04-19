from shikimori_api import Shikimori
import time
from ..postgres import connect_to_db

# python -m src.anime_db.update_anime_with_shikimori


def get_ids_syn(conn):
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
                f"SELECT anime_id,title_synonyms FROM anime WHERE title_russian IS NULL AND anime_id>{max_ind} ORDER BY anime_id"
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
    res = api.anime(mal_id).GET()
    # pprint(res)

    try:
        russian_title = res["russian"]
        print(russian_title)
    except KeyError:
        pass
    try:
        synonyms = res["synonyms"]
    except KeyError:
        pass

    try:
        franchise = res["franchise"]
    except KeyError:
        pass

    if franchise:
        insert_franchise(conn, franchise, mal_id)

    if russian_title:
        insert_russian_title(conn, russian_title, mal_id)

    if synonyms:
        if existing_synonyms:
            new_syn_list = [
                syn for syn in synonyms if syn not in existing_synonyms]
        else:
            new_syn_list = synonyms

        if new_syn_list:
            insert_synonyms(conn, new_syn_list, mal_id)

    time.sleep(1)


if __name__ == "__main__":
    conn, _ = connect_to_db()
    res = get_ids_syn(conn)
    print(len(res))
    for anime_id, exist_syn_list in res:
        print(anime_id)
        # query_shikimori(conn, anime_id, exist_syn_list)

    conn.close()
