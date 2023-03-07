"""
Tests for bot.py file
"""

from typing import List
from src.complements_bot.bot import ComplementsBot


def test_is_bot_name_ends_in_bot() -> None:
    """
    Tests the 'is_bot_name_ends_in_bot' function of ComplementsBot
    """

    names_to_test: List[str] = ["somebot", "ThatBot", "someOTHERBOT", "bOT"]
    for name in names_to_test:
        assert ComplementsBot.is_bot(name)
