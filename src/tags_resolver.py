import collections
import re
import string
try:
    from src.detect_anime import JUST_USE_TITLE, JUST_USE_SYNONYM_TITLE, JUST_USE_FRANCHISE, MAYBE_USE_FRANCHISE
    from src.detect_anime import detect_anime_from_string, get_text_inside_brackets
    from src.detect_character import detect_character
    from src.postgres import connect_to_db
    from src.extra_tags import get_extra_tags
except ModuleNotFoundError:
    from detect_anime import JUST_USE_TITLE, JUST_USE_SYNONYM_TITLE, JUST_USE_FRANCHISE, MAYBE_USE_FRANCHISE
    from detect_anime import detect_anime_from_string, get_text_inside_brackets
    from detect_character import detect_character
    from postgres import connect_to_db
    from extra_tags import get_extra_tags


# convert function objects to their names
JUST_USE_TITLE_FUNC_NAMES = [func.__name__ for func in JUST_USE_TITLE]
JUST_USE_SYNONYM_TITLE_FUNC_NAMES = [func.__name__ for func in JUST_USE_SYNONYM_TITLE]
JUST_USE_FRANCHISE_FUNC_NAMES = [func.__name__ for func in JUST_USE_FRANCHISE]
MAYBE_USE_FRANCHISE_FUNC_NAMES = [func.__name__ for func in MAYBE_USE_FRANCHISE]

POSTFIX = "@kotanima_arts"


def unslugify_text(text):
    uppercased = string.capwords(text, sep='-')
    return uppercased.replace("-", "_")


def get_tags_by_resolving_function_name(detected_obj):
    """Based on the function name, generate tags for vk
    """

    visible_tags = []
    invisible_tags = []

    if not detected_obj:
        return ["anime_art"], None

    db_data = detected_obj[0][0]
    (anime_id, title, title_english, russian_title, franchise) = db_data

    if russian_title:
        # remove non alpha-numeric symbols
        russian_title = re.sub("[^0-9a-zA-ZА-Яа-яЁё]+", "_", russian_title)
        russian_title = russian_title.split("_")
        russian_title = [x for x in russian_title if x]  # remove empty items
        russian_title = '_'.join(russian_title)
        russian_title = string.capwords(russian_title, sep='_')

    if title:
        title = unslugify_text(title)
        # fuck idolmaster
        if 'idolm_ster' in title.lower():
            title = title.replace('Idolm_Ster', 'Idolmaster')
            title = title.replace('Idolm_ster', 'Idolmaster')
    if title_english:
        title_english = unslugify_text(title_english)
        if 'idolm_ster' in title_english.lower():
            title_english = title_english.replace('Idolm_Ster', 'Idolmaster')
            title_english = title_english.replace('Idolm_ster', 'Idolmaster')
    if franchise:
        franchise = string.capwords(franchise, sep='_')

    # if title english contains the same words as title, we dont need it
    if title and title_english:
        if collections.Counter(title.split('_')) == collections.Counter(title_english.split('_')):
            title_english = None

    func_name = detected_obj[1]
    column_name = None
    if len(detected_obj) == 4:  # detected obj has column name which was direct match
        column_name = detected_obj[2]

    if func_name in JUST_USE_TITLE_FUNC_NAMES + JUST_USE_SYNONYM_TITLE_FUNC_NAMES:
        if russian_title:
            visible_tags.append(russian_title)
            if title_english:
                invisible_tags.append(title_english)
            if title:
                invisible_tags.append(title)
            if franchise:
                invisible_tags.append(franchise)

            invisible_tags = list(set(invisible_tags))
            return visible_tags, invisible_tags

        if column_name == 'title_english':
            return [title_english], invisible_tags

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

    return "anime_art", invisible_tags


def convert_tags_to_vk_string(tag_list):
    if not tag_list:
        return ""
    tag_list = ['#' + tag + POSTFIX for tag in tag_list]
    vk_string = '\n'.join(tag_list)
    return vk_string


def modify_daily_text(input_text):
    if "daily" in input_text.lower() and "#" in input_text:
        pattern = re.compile("daily", re.IGNORECASE)
        input_text = pattern.sub("", input_text)
        input_text = re.sub(r"#\d+", "", input_text)
    return input_text


def get_mal_id_vis_and_invis_tags(conn, title):
    possible_titles = get_text_inside_brackets(title)
    if not possible_titles:
        possible_titles = [title]

    possible_titles = [modify_daily_text(title) for title in possible_titles]
    possible_titles.sort(key=len, reverse=True)

    for temp_title in possible_titles:
        detected_obj = detect_anime_from_string(conn, temp_title)
        if detected_obj:
            break
    print(detected_obj)
    char = None
    anime_id = None
    if detected_obj:
        anime_id = detected_obj[0][0][0]
        is_anime = detected_obj[-1]
        char = detect_character(conn, title, anime_id, is_anime)

    vis_tags, invis_tags = get_tags_by_resolving_function_name(detected_obj)
    if char:
        vis_tags.append(char)

    if invis_tags:
        invis_tags = [tag for tag in invis_tags if tag not in vis_tags]

    # apply tagify tags (#cat/dog etc)
    extra_tags = get_extra_tags(title)
    if extra_tags and invis_tags:
        invis_tags += extra_tags

    return anime_id, vis_tags, invis_tags


if __name__ == "__main__":
    conn, _ = connect_to_db()

    title = "IA is neko so lovely!! One of my favorite [Touhou]"

    anime_id, vis_tags, invis_tags = get_mal_id_vis_and_invis_tags(conn, title)
    # print(anime_id)
    # print(vis_tags)
    # print(invis_tags)

    vis_string = convert_tags_to_vk_string(vis_tags)
    invis_string = convert_tags_to_vk_string(invis_tags)
    print(vis_string)
    print()
    print(invis_string)
