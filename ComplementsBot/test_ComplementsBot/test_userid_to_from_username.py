from ComplementsBot import userid_to_from_username
from ComplementsBot import bot


def test_name_to_id() -> None:
    assert bot.BOT_ID == userid_to_from_username.name_to_id(bot.BOT_NICK)


def test_id_to_name() -> None:
    assert bot.BOT_NICK == userid_to_from_username.id_to_name(bot.BOT_ID)
