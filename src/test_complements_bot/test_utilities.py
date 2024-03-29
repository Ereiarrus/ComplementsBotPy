"""
Tests for utilities.py file
"""

from src.complements_bot.utilities import run_with_appropriate_awaiting, remove_chars


def test_run_with_appropriate_awaiting():
    """
    Tests the 'run_with_appropriate_awaiting' function of utilities
    """

    abba = run_with_appropriate_awaiting
    assert abba


def test_remove_chars():
    """
    Tests the 'remove_chars' function of utilities
    """

    assert remove_chars(" []{{{]/rteybhdrty   .,.5464   thjfg ??>~~``") == "rteybhdrty5464thjfg"
