import pytest


import tgbot


def test_storage():
    user_telegram_id = 123
    args1 = ["args1", "args2"]
    args2 = ["args1", "args2"]
    args3 = ["args2", "args1"]

    storage = tgbot.Storage()
    assert storage[user_telegram_id] == tgbot.UserStorage()

    storage[user_telegram_id].last_stat_args = args1
    assert storage[user_telegram_id].last_stat_args == args1
    assert storage[user_telegram_id].last_stat_args == args2

    storage[user_telegram_id].last_stat_args = args3
    assert storage[user_telegram_id].last_stat_args == args3
