import os
from datetime import datetime

import appdirs
import humanize
import sqlmodel


class Snipe(sqlmodel.SQLModel, table=True):
    id: int = sqlmodel.Field(primary_key=True)
    mode: str = sqlmodel.Field(default="edited", primary_key=True)
    author: int
    content: str
    channel: int
    server: int
    time: datetime = sqlmodel.Field(default_factory=datetime.utcnow, primary_key=True)

    @property
    def readable_time(self) -> str:
        return humanize.naturaltime(datetime.utcnow() - self.time)


# TODO: make database a docker volume for persistent between container builds

data_dir = appdirs.user_data_dir(appname="StarrFox_bot", appauthor="StarrFox")

if not os.path.exists(data_dir):
    os.mkdir(data_dir)

# if it says it can't read the database file, the directory wasn't made correctly
engine = sqlmodel.create_engine(f"sqlite:///{data_dir}/sfb.db")
sqlmodel.SQLModel.metadata.create_all(engine)


# TODO: test if this blocks long enough to be an issue
def add_snipe(snipe: Snipe):
    with sqlmodel.Session(engine) as session:
        session.add(snipe)
        session.commit()


def get_snipes(
        server_id: int = None,
        author: int = None,
        channel: int = None,
        mode: str = None,
) -> list[Snipe]:
    with sqlmodel.Session(engine) as session:
        statement = sqlmodel.select(Snipe)

        statement = statement.order_by(Snipe.time)

        if server_id:
            statement = statement.where(Snipe.server == server_id)

        if author:
            statement = statement.where(Snipe.author == author)

        if channel:
            statement = statement.where(Snipe.channel == channel)

        if mode:
            statement = statement.where(Snipe.mode == mode)

        # reverse them so newer snipes are on top
        return session.exec(statement).all()[::-1]


if __name__ == "__main__":
    # for _snipe in [
    #     Snipe(id=2, author=123, content="an edited message", channel=321, server=1),
    #     Snipe(id=3, author=123, content="an edited message", channel=321, server=1),
    #     Snipe(id=4, author=1234, content="an edited message", channel=321, server=2),
    #     Snipe(id=5, author=1234, content="an edited message", channel=321, server=2),
    #     Snipe(id=6, author=12345, content="an edited message", channel=321, server=3),
    #     Snipe(id=7, author=12345, content="an edited message", channel=321, server=3),
    # ]:
    #     add_snipe(_snipe)

    from pprint import pprint
    pprint(get_snipes())
