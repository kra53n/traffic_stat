import os
import typing

import sqlite3


def get(db_src: str, table_name: str) -> list[list[typing.Any]]:
    con = sqlite3.connect(db_src)
    cur = con.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    res = cur.fetchall()
    con.close()
    return res


def src() -> str:
    """
    Return the src to sqlite database from environment variable DB_SRC.

    load_env() before calling src.
    """
    src: typing.Optional[str] = os.getenv("DB_SRC")
    if not src:
        # TODO add logging here
        return ""
    return src


if __name__ == '__main__':
    import pprint
    import statistic

    raw_records = get(db_src="stat.db", table_name="stat")
    statistic_records = statistic.get_list(raw_records)
    pprint.pprint(statistic_records)