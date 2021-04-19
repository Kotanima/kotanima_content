import pytest
from src.postgres import connect_to_db
from src.detect_character import detect_character


@pytest.fixture
def setup_database():
    """ Fixture to set up  database """
    conn, _ = connect_to_db()
    print("setup db")
    yield conn


# pytest -x ./tests/test_detect_character.py

@pytest.mark.parametrize(
    "input_text, mal_id, char_name",
    [
        ("( Exceptional Rem With Hair Ribbon And Ornaments ) [ Re:Zero ]", 31240, "Rem"),
        ("I think this is going to be my new thing. [Code Geass]", 1575, None),
        ("Rin [yurucamp]", 34798, 'Shima_Rin'),
        ("Sisters [A Certain Scientific Railgun]", 6213, None),
        ("C.C [Code Geass]", 1575, 'C.C.'),
        ("\"School Girl\" Shinobu Kocho [Kimetsu no Yaiba]",
         38000, 'Kochou_Shinobu'),
        ("Blushing Echidna [Re: Zero]", 39587, 'Echidna'),
        ("Gura Smirk [Hololive]", 44042, 'Gawr_Gura'),
        ("Suisei [Hololive]", 44042, 'Hoshimachi_Suisei'),

    ],
)
def test_detect_anime_from_string(setup_database, input_text, mal_id, char_name):
    conn = setup_database
    res = detect_character(conn, input_text, mal_id, True)
    conn.close()
    assert res == char_name
