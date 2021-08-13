"""
Generates vk tags for images.
Logic for parsing the detected object and based on titles/english title/russian title
decide which one to use in the VK post body and in image descriptions.
The imports are doubled because of pytest import errors.
"""

import collections
import re
import string

try:
    from src.detect_anime import (
        JUST_USE_FRANCHISE,
        JUST_USE_SYNONYM_TITLE,
        JUST_USE_TITLE,
        MAYBE_USE_FRANCHISE,
        detect_anime_from_string,
        get_text_inside_brackets,
        AnimeDetection,
    )
    from src.detect_character import detect_character
    from src.extra_tags import get_extra_tags
    from src.postgres import connect_to_db
except ModuleNotFoundError:
    from detect_anime import (
        JUST_USE_FRANCHISE,
        JUST_USE_SYNONYM_TITLE,
        JUST_USE_TITLE,
        MAYBE_USE_FRANCHISE,
        detect_anime_from_string,
        get_text_inside_brackets,
        AnimeDetection,
    )
    from detect_character import detect_character
    from extra_tags import get_extra_tags
    from postgres import connect_to_db


# convert function objects to their names
JUST_USE_TITLE_FUNC_NAMES = [func.__name__ for func in JUST_USE_TITLE]
JUST_USE_SYNONYM_TITLE_FUNC_NAMES = [func.__name__ for func in JUST_USE_SYNONYM_TITLE]
JUST_USE_FRANCHISE_FUNC_NAMES = [func.__name__ for func in JUST_USE_FRANCHISE]
MAYBE_USE_FRANCHISE_FUNC_NAMES = [func.__name__ for func in MAYBE_USE_FRANCHISE]

POSTFIX = "@kotanima_arts"
DEFAULT_STRING = "AnimeArt"


def unslugify_text(text):
    uppercased = string.capwords(text, sep="-")
    return uppercased.replace("-", "_")


def get_tags_by_resolving_function_name(detected_obj):
    """Based on the function name that was used for creating a detected object, generate tags for vk"""

    visible_tags = []
    invisible_tags = []

    if not detected_obj or not detected_obj.anime_info:
        return [DEFAULT_STRING], []

    (anime_id, title, title_english, russian_title, franchise) = detected_obj.anime_info

    if russian_title:
        # remove non alpha-numeric symbols
        russian_title = re.sub("[^0-9a-zA-ZА-Яа-яЁё]+", "_", russian_title)
        russian_title = russian_title.split("_")
        russian_title = [x for x in russian_title if x]  # remove empty items
        russian_title = "_".join(russian_title)
        russian_title = string.capwords(russian_title, sep="_")

    if title:
        title = unslugify_text(title)
        # fuck idolmaster
        if "idolm_ster" in title.lower():
            title = title.replace("Idolm_Ster", "Idolmaster")
            title = title.replace("Idolm_ster", "Idolmaster")
    if title_english:
        title_english = unslugify_text(title_english)
        if "idolm_ster" in title_english.lower():
            title_english = title_english.replace("Idolm_Ster", "Idolmaster")
            title_english = title_english.replace("Idolm_ster", "Idolmaster")
    if franchise:
        franchise = string.capwords(franchise, sep="_")

    # if title english contains the same words as title, we dont need it
    if title and title_english:
        if collections.Counter(title.split("_")) == collections.Counter(
            title_english.split("_")
        ):
            title_english = None

    func_name = detected_obj.func_name
    column_name = None
    if detected_obj.column:  # detected obj has column name which was direct match
        column_name = detected_obj.column

    if func_name in JUST_USE_TITLE_FUNC_NAMES + JUST_USE_SYNONYM_TITLE_FUNC_NAMES:
        if russian_title:
            visible_tags.append(russian_title)
            for arg in [title, title_english, franchise]:
                if arg:
                    invisible_tags.append(arg)
            invisible_tags = list(set(invisible_tags))
            return visible_tags, invisible_tags

        if column_name == "title_english":
            if title_english:
                return [title_english], invisible_tags
            else:
                return [title], invisible_tags
        else:
            return [title], invisible_tags

    elif func_name in JUST_USE_FRANCHISE_FUNC_NAMES:
        return [franchise], invisible_tags

    elif func_name in MAYBE_USE_FRANCHISE_FUNC_NAMES:
        if franchise:
            return [franchise], invisible_tags

        elif title_english:
            # visible_string += title_english
            return [title_english], invisible_tags
        else:
            return [title], invisible_tags

    return DEFAULT_STRING, invisible_tags


def convert_tags_to_vk_string(tag_list: list[str]) -> str:
    if not tag_list:
        return ""
    # nobody uses underscore in tags, replace it ..
    tag_list = [tag.replace("_", "") for tag in tag_list]
    tag_list = ["#" + tag + POSTFIX for tag in tag_list]
    vk_string = "\n".join(tag_list)
    return vk_string


def modify_daily_text(input_text: str) -> str:
    if "daily" in input_text.lower() and "#" in input_text:
        pattern = re.compile("daily", re.IGNORECASE)
        input_text = pattern.sub("", input_text)
        input_text = re.sub(r"#\d+", "", input_text)
    return input_text


def get_mal_id_vis_and_invis_tags(conn, title: str):
    invis_tags = None
    vis_tags = None
    detected_obj = None

    possible_titles = get_text_inside_brackets(title)
    if not possible_titles:
        possible_titles = [title]

    possible_titles = [modify_daily_text(title) for title in possible_titles]
    possible_titles = [
        title for title in possible_titles if "x-post" not in title.lower()
    ]
    possible_titles.sort(key=len, reverse=True)

    # iterate through possible titles and attempt to find anime name
    for temp_title in possible_titles:
        detected_obj = detect_anime_from_string(conn, temp_title)
        if detected_obj:
            break

    # detect anime
    vis_tags, invis_tags = get_tags_by_resolving_function_name(detected_obj)

    if detected_obj is not None:
        # detect char name
        if char := detect_character(
            conn, title, detected_obj.anime_id, detected_obj.is_from_anime
        ):
            vis_tags.append(char)

    # dont store duplicate tags
    if invis_tags is not None and vis_tags is not None:
        invis_tags = [tag for tag in invis_tags if tag not in vis_tags]

    # apply tagify tags (#cat/dog etc)
    extra_tags = get_extra_tags(conn, title)

    if extra_tags is not None:
        if invis_tags is not None:
            invis_tags += extra_tags
        else:
            invis_tags = extra_tags

    if detected_obj is not None:
        return detected_obj.anime_id, vis_tags, invis_tags
    else:
        return None, vis_tags, invis_tags


def main():
    conn = connect_to_db()
    title = """Orie [Under Night In-Birth]"""
    _, vis_tags, invis_tags = get_mal_id_vis_and_invis_tags(conn, title)
    vis_string = convert_tags_to_vk_string(vis_tags)
    invis_string = convert_tags_to_vk_string(invis_tags)
    print(f"{vis_string=}")
    print()
    print(f"{invis_string=}")
    conn.close()


if __name__ == "__main__":
    main()
