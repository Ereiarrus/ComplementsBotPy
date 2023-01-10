from ComplementsBot import bot, database


def test_channel_exists() -> None:
    assert database.channel_exists(bot.BOT_NICK)
