
from ..postgres import connect_to_db

# python -m src.anime_db.update_non_anime


def insert_non_anime_record(conn,
                            title,
                            title_japanese,
                            title_english,
                            title_russian,
                            title_synonyms,
                            franchise):
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO non_anime (title, title_japanese, title_english, title_russian, title_synonyms, franchise)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (
                    title,
                    title_japanese,
                    title_english,
                    title_russian,
                    title_synonyms,
                    franchise,
                ),
            )


if __name__ == "__main__":
    pass
    # conn, _ = connect_to_db()
    # insert_non_anime_record(conn, title="Katawa Shoujo",
    #                         title_japanese=None,
    #                         title_english=None,
    #                         title_russian=None,
    #                         title_synonyms=None,
    #                         franchise=None)

    # conn.close()
