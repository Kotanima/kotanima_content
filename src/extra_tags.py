import re

try:
    from postgres import connect_to_db
except ModuleNotFoundError:
    from src.postgres import connect_to_db


def get_tag_rules(conn):
    with conn:
        with conn.cursor() as cursor:
            query = """SELECT check_type, check_words, anime_name, visible_tags, invisible_tags FROM tagify ORDER BY id"""
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_extra_tags(title: str):
    conn = connect_to_db()
    tag_rules = get_tag_rules(conn)

    extra_tags = []

    # replace non alphanumeric characters with space
    title = re.sub("[^0-9a-zA-Z]", " ", title)
    # delete all extra whitespace characters (space, tab, newline, return, formfeed)
    title = " ".join(set(title.split()))

    for rule in tag_rules:
        check_type, check_words, _, visible_tags, invisible_tags = rule

        if check_type == "any":
            if any(word in title for word in check_words):
                extra_tags += visible_tags + invisible_tags
                continue
        else:
            if all(word in title for word in check_words):
                extra_tags += visible_tags + invisible_tags
                continue

    # remove duplicates
    extra_tags = list(set(extra_tags))
    return extra_tags


if __name__ == "__main__":
    title = "IA is neko so lovely!! One of my favorite"
    res = get_extra_tags(title)
    print(res)