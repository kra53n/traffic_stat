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
        arg: typing.Sequence[typing.Any],
        *args,
        **kwargs,
    ):
        # TODO check kwargs and parse fields from kwargs
        # TODO think should we have *args

        # NOTE we can panic when arg is not a sequnce and when we are go out of range 
        self.id = arg[0]
        self.year = arg[1]
        self.month = arg[2]
        self.day = arg[3]
        self.nickname = arg[4]
        self.alltime = arg[5]


def get_list(iter: typing.Iterable) -> list[Statistic]:
    return [Statistic(i) for i in iter]


def group_by(attrname: str, records: typing.Iterable[Statistic]) -> dict[str, list]:
    groups: dict[str, list] = {}
    for record in records:
        key = getattr(record, attrname)
        if key in groups:
            groups[key].append(record)
        else:
            groups[key] = [record]
    return groups
