import pytest
from src.postgres import connect_to_db
from src.extra_tags import get_extra_tags

# pytest -n auto
# OR
# pytest -x ./tests/test_extra_tags.py


@pytest.fixture
def setup_database():
    """Fixture to set up  database"""
    conn = connect_to_db()
    print("setup db")
    yield conn


@pytest.mark.parametrize(
    "input_text, extra_tags",
    [
        ("Something text neko", ["неко", "neko"]),
        ("Something text maid something", ["горничная", "maid"]),
        ("Something text elf something", ["elf"]),
    ],
)
def test_get_extra_tags(setup_database, input_text, extra_tags):
    conn = setup_database
    res = get_extra_tags(conn, input_text)
    conn.close()
    assert res.sort() == extra_tags.sort()
