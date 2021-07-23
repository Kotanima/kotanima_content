"""
Add misc tags like maid/neko etc, based on presence of any/all certain words
"""
from dataclasses import dataclass
from enum import Enum
import re

try:
    from postgres import connect_to_db
except ModuleNotFoundError:
    from src.postgres import connect_to_db

from enum import Enum, auto
import psycopg2


class CheckType(Enum):
    any = (auto(),)
    all = auto()


@dataclass
class TagAddingRule:
    """based on check type(any/all)
    If any/all check words are present in the input string,
    add specified tags.
    """
    check_type: CheckType
    check_words: list[str]
    visible_tags: list[str]
    invisible_tags: list[str]

    @classmethod
    def from_db(cls, obj):
        return cls(
            obj.check_type,
            obj.check_words,
            obj.visible_tags,
            obj.invisible_tags,
        )


def get_tag_rules(conn):
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor) as cursor:
            query = """SELECT check_type, check_words, visible_tags, invisible_tags FROM tagify ORDER BY id"""
            cursor.execute(query)
            data = cursor.fetchall()
            return data


def get_extra_tags(conn, title: str):

    tag_rules = get_tag_rules(conn)
    extra_tags = []

    # replace non alphanumeric characters with space
    title = re.sub("[^0-9a-zA-Z]", " ", title)
    # delete all extra whitespace characters (space, tab, newline, return, formfeed)
    title = " ".join(set(title.split()))

    for rule in tag_rules:
        tag_rule = TagAddingRule.from_db(rule)

        if tag_rule.check_type == CheckType.any:
            if any(word in title for word in tag_rule.check_words):
                extra_tags += tag_rule.visible_tags + tag_rule.invisible_tags
                continue
        else:
            if all(word in title for word in tag_rule.check_words):
                extra_tags += tag_rule.visible_tags + tag_rule.invisible_tags
                continue

    # remove empty strings
    extra_tags = [x for x in extra_tags if x]
    # remove duplicates
    extra_tags = list(set(extra_tags))
    return extra_tags


if __name__ == "__main__":
    conn = connect_to_db()
    title = "IA is elf so lovely!! One of my favorite"
    res = get_extra_tags(conn, title)
    print(res)
