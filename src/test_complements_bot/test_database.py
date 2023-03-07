"""
Tests for database.py file
"""

from src.complements_bot import database
from .testing_commons import BOT_ID


def test_channel_exists() -> None:
    """
    Tests the 'channel_exists' function of database
    """

    assert database.channel_exists(userid=BOT_ID)
