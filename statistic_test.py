import pytest

import statistic


def test_statistic_init_not_enough_args():
    """
    Test Statistic.__init__() exception invoking when not enough arguments was provided
    """
    not_enough_arguments_statistic = (
        1,          # id
        2026,       # year
        5,          # month
        20,         # day
        "nickname", # nickname
    )
    with pytest.raises(statistic.StatisticExceptionNotEnoughArgs):
        statistic.Statistic(*not_enough_arguments_statistic)


def test_statistic_init_too_many_args():
    """
    Test Statistic.__init__() exception invoking when too many arguments was provided
    """
    too_many_arguments_statistic = (
        1,          # id
        2026,       # year
        5,          # month
        20,         # day
        "nickname", # nickname
        120,        # alltime (bytes)
        "something_more",
    )
    with pytest.raises(statistic.StatisticExceptionTooManyArgs):
        statistic.Statistic(*too_many_arguments_statistic)
