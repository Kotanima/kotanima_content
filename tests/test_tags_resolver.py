import collections
import pytest
from src.tags_resolver import get_mal_id_vis_and_invis_tags, connect_to_db


@pytest.fixture
def setup_database():
    """Fixture to set up  database"""
    conn = connect_to_db()
    print("setup db")
    yield conn


# pytest -x ./tests/test_tags_resolver.py


@pytest.mark.parametrize(
    "title,res_anime,res_char, res_invis_tags",
    [
        ("Smiling Miku [Vocaloid]", "Vocaloid", "Hatsune_Miku", None),
        ("Smiling Miku [Vocaloid]", "Vocaloid", "Hatsune_Miku", None),
        ("Keeping warm neko [Original]", "AnimeArt", None, None),
        (
            "Degeso~! (Ika Musume or Shinryaku! Ika Musume)",
            "Вторжение_Кальмарки",
            "Ika_Musume",
            ["The_Squid_Girl", "Shinryaku_Ika_Musume"],
        ),
        (
            "Asuna taking over - (Sword art Online",
            "Мастера_Меча_Онлайн",
            "Yuuki_Asuna",
            ["Sword_Art_Online"],
        ),
        (
            "Five years [Hatsune Miku].",
            "Хатсуне_Мику",
            "Hatsune_Miku",
            ["Suna_No_Wakusei_Feat_Hatsune_Miku"],
        ),
        (
            "Hanyuu and Rika [Higurashi]",
            "Когда_Плачут_Цикады",
            "Furude_Rika",
            [
                "Higurashi_No_Naku_Koro_Ni_2020",
                "When_They_Cry",
                "Higurashi_When_They_Cry_New",
            ],
        ),
        (
            "Daily Yuri #640][Kiniro Mosaic]",
            "Золотая_Мозаика",
            None,
            ["Kiniro_Mosaic", "Kinmoza"],
        ),
        ("test [Daily iDOLM@STER #236]", "Idolmaster", None, None),
        ("Saber [Fate Series] by ￦ANKE", "Fate", "Saber", None),
        ("ACHZARIT [Touhou Project]", "Тохо", None, ["Touhou", "Touhou_Project"]),
        (
            "Honoka with twintails. [Love Live! School Idol Project]",
            "Живая_Любовь_Проект_Школьный_Идол",
            "Kousaka_Honoka",
            ["Love_Live_School_Idol_Project", "Love_Live"],
        ),
        (
            "I think this is going to be my new thing. [Code Geass]",
            "Код_Гиас_Восставший_Лелуш",
            None,
            ["Code_Geass_Lelouch_Of_The_Rebellion", "Code_Geass"],
        ),
        ("Ballpoint Pen (K-On!!)[Movie]", "Кэйон", None, ["K_On_Season_2", "K_On"]),
        (
            "Keeping warm [Kantai Collection]",
            "Флотская_Коллекция",
            None,
            ["Kancolle", "Kantai_Collection_Kancolle"],
        ),
        (
            "Happy Birthday, Yukari! [The iDOLM@STER: Cinderella Girls]",
            "Идолмастер_Девушки_Золушки",
            "Mizumoto_Yukari",
            None,
        ),
    ],
)
def test_get_vis_and_invis_tags(
    setup_database, title, res_anime, res_char, res_invis_tags
):
    conn = setup_database
    anime_id, vis_tags, invis_tags = get_mal_id_vis_and_invis_tags(conn, title)
    conn.close()
    try:
        main_anime = vis_tags[0]
    except IndexError:
        main_anime = None
    try:
        char_name = vis_tags[1]
    except IndexError:
        char_name = None

    assert main_anime == res_anime
    assert char_name == res_char
    if res_invis_tags:
        assert collections.Counter(invis_tags) == collections.Counter(res_invis_tags)
