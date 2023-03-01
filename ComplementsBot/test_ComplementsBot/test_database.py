from ComplementsBot import bot, database
from .testing_commons import BOT_NICK


def test_channel_exists() -> None:
    assert database.channel_exists(BOT_NICK)
