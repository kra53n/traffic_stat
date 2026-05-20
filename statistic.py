import dataclasses
import typing


@dataclasses.dataclass
class Statistic:
    """
    Represents a statistical record.

    Attributes:
        id (int): Unique identifier for the statistic entry.
        year (int): Year of the statistic.
        month (int): Month of the statistic.
        day (int): Day of the statistic.
        nickname (int): Nickname identifier.
        alltime (int): Total network usage in bytes.
    """
    id: int
    year: int
    month: int
    day: int
    nickname: str
    alltime: int

    def __init__(
        self,
        *args: typing.Any,
    ):
        if len(args) < 6:
            raise StatisticExceptionNotEnoughArgs(args)
        if len(args) > 6:
            raise StatisticExceptionTooManyArgs(args)
        self.id = args[0]
        self.year = args[1]
        self.month = args[2]
        self.day = args[3]
        self.nickname = args[4]
        self.alltime = args[5]


class StatisticExceptionNotEnoughArgs(Exception):
    def __init__(self, args: typing.Sequence[typing.Any]):
        super().__init__(f"got {len(args)} args{args}, should be 6 (id, year, month, day, nickname, alltime)")


class StatisticExceptionTooManyArgs(Exception):
    def __init__(self, args: typing.Sequence[typing.Any]):
        super().__init__(f"got {len(args)} args{args}, should be 6(id, year, month, day, nickname, alltime)")


def get_list(iter: typing.Iterable[typing.Sequence]) -> list[Statistic]:
    return [Statistic(*i) for i in iter]


def group_by(attrname: str, records: typing.Iterable[Statistic]) -> dict[str, list]:
    groups: dict[str, list] = {}
    for record in records:
        key = getattr(record, attrname)
        if key in groups:
            groups[key].append(record)
        else:
            groups[key] = [record]
    return groups
