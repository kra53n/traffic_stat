import pytest


import tgbot


def test_storage():
    user_telegram_id = 123
    args1 = ["args1", "args2"]
    args2 = ["args1", "args2"]
    args3 = ["args2", "args1"]

    storage = tgbot.Storage()
    assert storage[user_telegram_id] == tgbot.UserStorage()

    storage[user_telegram_id].last_input_nicknames = args1
    assert storage[user_telegram_id].last_input_nicknames == args1
    assert storage[user_telegram_id].last_input_nicknames == args2

    storage[user_telegram_id].last_input_nicknames = args3
    assert storage[user_telegram_id].last_input_nicknames == args3


def test_format_bytes():
    assert tgbot.format_bytes(0) == "0 bytes"
    assert tgbot.format_bytes(125) == "125 bytes"

    assert tgbot.format_bytes(1023) == "1023 bytes"
    assert tgbot.format_bytes(1024) == "1 KiB"

    assert tgbot.format_bytes(126_976) == "124 KiB"
    assert tgbot.format_bytes(130_000) == "126 KiB"