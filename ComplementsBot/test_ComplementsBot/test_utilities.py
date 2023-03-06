from ComplementsBot.utilities import run_with_appropriate_awaiting, remove_chars


def test_run_with_appropriate_awaiting():
    assert run_with_appropriate_awaiting


def test_remove_chars():
    assert remove_chars("rteybhdrty   .,.5464   thjfg ??>~~``") == "rteybhdrty5464thjfg"
