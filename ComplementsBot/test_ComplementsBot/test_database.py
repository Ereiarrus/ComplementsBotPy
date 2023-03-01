from ComplementsBot import bot, database
from .testing_commons import BOT_NICK, BOT_ID


def test_channel_exists() -> None:
    assert database.channel_exists(userid=BOT_ID)
