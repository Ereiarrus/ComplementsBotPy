from ComplementsBot import database
from .testing_commons import BOT_ID


def test_channel_exists() -> None:
    assert database.channel_exists(userid=BOT_ID)
