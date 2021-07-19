import re

import praw
from prawcore.exceptions import ResponseException
from psaw import PushshiftAPI

from detect_anime import get_text_inside_brackets


def validate_url(url):
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


def get_source_from_text_two_links(normal_text: str):
    reg = re.compile(r"(http.*?)(\))")
    result = reg.search(normal_text)
    return result


def get_source_from_text_type_spoiler(text_with_spoiler: str):
    reg = re.compile(r"\]\((http.*?)(?:\))")
    result = reg.search(text_with_spoiler)
    return result


def get_source_from_text(normal_text: str):
    reg = re.compile(r"(http.*)")
    result = reg.search(normal_text)
    return result


def check_if_post_removed_text_in_post(bot_text: str):
    reg = re.compile(r"This post has been removed")
    return reg.search(bot_text)


def parse_filename(url: str):
    file_name: list = url.split("/")
    if len(file_name) == 0:
        file_name = re.findall("/(.*?)", url)
    file_name = file_name[-1]
    if "." not in file_name:
        file_name += ".jpg"

    return file_name


def praw_comments_search(subm_id: int):
    r = praw.Reddit(
        client_id="ArI1mj64JFXxow",
        client_secret="aNXIUjAVtVc6QJCtdejMfWHat6U",
        user_agent="KAS",
        username="AreYouWtf",
        password="112233332211vv",
    )

    submission = r.submission(subm_id)
    try:
        submission.comments.replace_more(limit=None)
    except ResponseException:
        print("Praw comment search 503 response")
        return []

    return submission.comments.list()


def insanity_checks(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        if res:  # not empty
            if any(text in res for text in ["cdn", "saucenao", "reddit", "youtube", "imgur"]):
                return None
            if res.startswith("https://www.pixiv.net/en/artworks/"):
                return res[0:42]
            if "pixiv" in res:
                if res.endswith("&amp;utm_source=share&amp;utm_medium=ios_app"):
                    res = res.replace(
                        "&amp;utm_source=share&amp;utm_medium=ios_app", ""
                    )
                useless_list = [
                    "member_illust.php?mode=medium&amp;illust_id=",
                    "member_illust.php?mode=medium&illust_id=",
                ]
                for useless in useless_list:
                    if useless in res:
                        res = res.replace(useless, r"en/artworks/")
                        return res
            if "\\" in res:
                res = res.replace("\\", "")
            return res

    return wrapper


@insanity_checks
def get_submission_source(subm_id, subm_author):
    def check_result(result):
        if result:
            for group in result.groups():
                if validate_url(group):
                    return group

    api = PushshiftAPI()
    gen = api.search_comments(link_id=subm_id, limit=50, filter=["author", "body"])
    comments = list(gen)
    # pprint(comments)

    if not comments:
        # pushshit, use praw instead
        comments = praw_comments_search(subm_id)

    author_comments = []
    other_comments = []
    for comment in comments:
        if comment.author == subm_author:
            author_comments.append(comment)
        else:
            other_comments.append(comment)

    source_funcs = [
        get_source_from_text_type_spoiler,
        get_source_from_text_two_links,
        get_source_from_text,
    ]

    for comment in author_comments:
        text = comment.body
        for func in source_funcs:
            source = func(text)
            res = check_result(source)
            if res:
                return res

    for comment in other_comments:
        text = comment.body
        res = check_if_post_removed_text_in_post(text)
        if res:
            return None
        # check if author doesnt know sauce but someone in comments does
        for func in source_funcs:
            source = func(text)
            res = check_result(source)
            if res:
                return res


if __name__ == "__main__":
    res = get_text_inside_brackets("[Sponge Bob Square Pants")
    print(res)
