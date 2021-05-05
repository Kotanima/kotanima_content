import pytest

from src.detect_anime import (
    connect_to_db,
    text_is_equal_to_column,
    slug_text_is_equal_to_slug_column,
    text_is_in_synonyms_array,
    text_is_substring_of_franchise,
    text_without_spaces_is_equal_to_franchise_column,
    # franchise_is_substring_of_text,
    text_is_substring_of_slug_title,
    text_is_substring_of_slug_title_english,
    text_without_spaces_is_equal_to_title,
    detect_anime_from_string,
)


@pytest.fixture
def setup_database():
    """Fixture to set up  database"""
    conn = connect_to_db()
    print("setup db")
    yield conn


# pytest -x ./tests/test_detect_anime.py


@pytest.mark.parametrize(
    "input_text,expected_id",
    [
        ("Touhou Project", 9875),
        ("K-On!, Kotobuki Tsumugi", 5680),
        ("Disgaea 4", 860),
        ("86", 41457),
        ("Final Fantasy", 426),
        ("Nier Automata", 4),
        ("Persona 4 Golden", 10588),
        ("Persona 5", 36023),
        ("Touhou", 9874),
        ("OriginalHolstein", None),
        ("Original", None),
        ("iDOLM@STER: Cinderella Girls", 21409),
        ("idolmaster", 1694),
        ("Kizuna Ai", None),
        ("Fate", 356),
        ("Tales of Destiny 2", None),
        ("Gekkan Shoujo/Idolmaster", 23289),
        ("VOCALOID", 14359),
        ("Gate", 28907),
        ("Honkai Impact III", None),
        ("http://bns.plaync.com/board/free/article/9672307", None),
        ("Persona", 3366),
        ("FateGO", 38084),
        ("FGO", 38084),
        ("DarliFra", 35849),
        ("Girls und Panzer", 14131),
        ("sweetness &amp; lightning", 32828),
        ("Re: Zero Season 2", 39587),
        ("Kanojo, Okarishimasu", 40839),
        ("Kimi No Nawa", 32281),
        ("5Toubun no Hanayome", 38101),
        ("bnha", 31964),
        ("Spice &amp; Wolf", 2966),
        ("Panty &amp; Stocking with Garterbelt", 8795),
        ("-Monogatari", 5081),
        ("Toaru Series", 4654),
        ("To Aru Kagaku no Railgun S", 16049),
        ("Kagerou Project", 21603),
        ("magi", 14513),
        ("Gate", 28907),
        ("Steins;Gate", 9253),
        ("Madoka magica", 9756),
        ("Higurashi", 41006),
        ("Re:Zero", 31240),
        ("Sword Art Online, 1280×800", 11757),
    ],
)
def test_detect_anime_from_string(setup_database, input_text, expected_id):
    conn = setup_database
    res = detect_anime_from_string(conn, input_text)
    conn.close()
    if res is None:
        assert res == expected_id
    else:
        assert res.anime_id == expected_id


@pytest.mark.parametrize(
    "input_text,result_id",
    [
        ("GateKeepers", 127),
    ],
)
def test_text_without_spaces_is_title(setup_database, input_text, result_id):
    conn = setup_database
    res = text_without_spaces_is_equal_to_title(conn, "anime", input_text)
    conn.close()
    assert res[0][0] == result_id


@pytest.mark.parametrize(
    "input_text,result_id",
    [
        ("How Not to Summon a Demon Lord", 37210),
    ],
)
def test_input_text_is_substring_of_slug_title_english(
    setup_database, input_text, result_id
):
    conn = setup_database
    res = text_is_substring_of_slug_title_english(conn, "anime", input_text)
    conn.close()
    assert res[0][0] == result_id


@pytest.mark.parametrize(
    "input_text,result_id",
    [
        ("shippuuden!Movie=2", 4437),
    ],
)
def test_input_text_is_substring_of_slug_title(setup_database, input_text, result_id):
    conn = setup_database
    res = text_is_substring_of_slug_title(conn, "anime", input_text)
    conn.close()
    assert res[0][0] == result_id


@pytest.mark.parametrize(
    "input_text,result_id",
    [
        ("yurucamp", 34798),
    ],
)
def test_text_without_spaces_is_in_franchise_column(
    setup_database, input_text, result_id
):
    conn = setup_database
    res = text_without_spaces_is_equal_to_franchise_column(conn, "anime", input_text)
    conn.close()
    assert res[0][0] == result_id


@pytest.mark.parametrize(
    "input_text,result_id",
    [
        ("sword_art", 11757),
    ],
)
def test_text_is_substring_of_franchise(setup_database, input_text, result_id):
    conn = setup_database
    res = text_is_substring_of_franchise(conn, "anime", input_text)
    conn.close()
    assert res[0][0] == result_id


@pytest.mark.parametrize(
    "input_text,result_id",
    [
        ("dmmd", 23333),
    ],
)
def test_text_is_in_synonyms_array(setup_database, input_text, result_id):
    conn = setup_database
    res = text_is_in_synonyms_array(conn, "anime", input_text)
    conn.close()

    assert res[0][0] == result_id


@pytest.mark.parametrize(
    "db_column,input_text,result_id",
    [
        ("title", "Kannazuki+no!miko", 143),
        ("title_english", "Ghost-Slayers-àyàshi", 1587),
    ],
)
def test_slug_text_is_in_slug_column(setup_database, db_column, input_text, result_id):
    conn = setup_database
    res = slug_text_is_equal_to_slug_column(conn, "anime", db_column, input_text)
    conn.close()
    assert res[0][0] == result_id


@pytest.mark.parametrize(
    "db_column,input_text,result_id",
    [
        ("title", "kannazuki no miko", 143),
        ("title_english", "ghost slayers ayashi", 1587),
    ],
)
def test_text_is_in_column(setup_database, db_column, input_text, result_id):
    conn = setup_database
    res = text_is_equal_to_column(conn, "anime", db_column, input_text)
    conn.close()
    assert res[0][0] == result_id
