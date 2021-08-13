import pytest
from src.vk_scheduler import VkPost
from src.models import IdentifiedRedditPost
from src.postgres import get_approved_anime_posts, connect_to_db

# pytest -n auto
# OR
# pytest -x ./tests/test_vk_scheduler.py


@pytest.mark.parametrize(
    "anime_posts, result_display_message, result_hidden_messages",
    [
        (
            [
                {
                    "post_id": "k4sfyd",
                    "sub_name": "awwnime",
                    "source_link": "https://www.pixiv.net/en/artworks/86035852",
                    "visible_tags": ["Hololive", "Minato_Aqua"],
                    "invisible_tags": None,
                    "phash": "e1d86596c8c69bc5",
                },
                {
                    "post_id": "ha64th",
                    "sub_name": "awwnime",
                    "source_link": "https://www.pixiv.net/en/artworks/82372378",
                    "visible_tags": ["Hololive", "Inugami_Korone"],
                    "invisible_tags": None,
                    "phash": "e2b19852a7d2692f",
                },
                {
                    "post_id": "hex3jb",
                    "sub_name": "awwnime",
                    "source_link": "https://twitter.com/frengchiano2/status/1275694907261321216?s=19",
                    "visible_tags": ["Hololive", "Uruha_Rushia"],
                    "invisible_tags": None,
                    "phash": "abd095f30d9266cc",
                },
            ],
            "#Hololive@kotanima_arts",
            [
                "#MinatoAqua@kotanima_arts\n https://www.pixiv.net/en/artworks/86035852",
                "#InugamiKorone@kotanima_arts\n https://www.pixiv.net/en/artworks/82372378",
                "#UruhaRushia@kotanima_arts\n https://twitter.com/frengchiano2/status/1275694907261321216?s=19",
            ],
        ),
        (
            [
                {
                    "post_id": "k4sfyd",
                    "sub_name": "awwnime",
                    "source_link": "https://www.pixiv.net/en/artworks/86035852",
                    "visible_tags": ["Hololive", "Minato_Aqua"],
                    "invisible_tags": None,
                    "phash": "e1d86596c8c69bc5",
                },
                {
                    "post_id": "ha64th",
                    "sub_name": "awwnime",
                    "source_link": "https://www.pixiv.net/en/artworks/82372378",
                    "visible_tags": ["Hololive", "Inugami_Korone"],
                    "invisible_tags": None,
                    "phash": "e2b19852a7d2692f",
                },
            ],
            "#Hololive@kotanima_arts",
            [
                "#MinatoAqua@kotanima_arts\n https://www.pixiv.net/en/artworks/86035852",
                "#InugamiKorone@kotanima_arts\n https://www.pixiv.net/en/artworks/82372378",
            ],
        ),
        (
            [
                {
                    "post_id": "k4sfyd",
                    "sub_name": "awwnime",
                    "source_link": "https://www.pixiv.net/en/artworks/86035852",
                    "visible_tags": ["Hololive", "Minato_Aqua"],
                    "invisible_tags": None,
                    "phash": "e1d86596c8c69bc5",
                },
            ],
            "#Hololive@kotanima_arts\n#MinatoAqua@kotanima_arts",
            ["\n https://www.pixiv.net/en/artworks/86035852"],
        ),
    ],
)
def test_VkPost(anime_posts, result_display_message, result_hidden_messages):
    anime_posts = [IdentifiedRedditPost.from_dict(post) for post in anime_posts]
    # print(anime_posts)
    vk_post = VkPost(owner_id=0, last_post_date=-1, reddit_posts=anime_posts)

    display_message = vk_post._get_main_post_message(anime_posts)
    assert display_message == result_display_message
    print(display_message)

    hidden_messages = vk_post._get_list_of_hidden_messages(anime_posts)
    assert hidden_messages == result_hidden_messages
    print(hidden_messages)
