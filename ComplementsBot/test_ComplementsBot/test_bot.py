from ComplementsBot import bot
from typing import List


def test_is_bot_name_ends_in_bot() -> None:
    names_to_test: List[str] = ["somebot", "ThatBot", "someOTHERBOT", "bOT"]
    for name in names_to_test:
        assert bot.ComplementsBot.is_bot(name)
