from itertools import count

import asyncpg
import pendulum

from discord_chan.snipe import Snipe, SnipeMode

# TODO: add enviorment variables for these
DATABASE_user = "starr"
DATABASE_name = "discord_chan"


DATABASE_snipe_table = """
CREATE TABLE IF NOT EXISTS snipes (
    id BIGINT,
    mode INT,
    server BIGINT,
    author BIGINT,
    channel BIGINT,
    time FLOAT,
    content TEXT
);
""".strip()


class Database:
    def __init__(self):
        self._connection: asyncpg.Pool = None
        self._ensured: bool = False

    async def _ensure_tables(self, pool: asyncpg.Pool):
        if self._ensured:
            return

        self._ensured = True

        async with pool.acquire() as connection:
            await connection.execute(DATABASE_snipe_table)

    async def connect(self) -> asyncpg.Pool:
        if self._connection is not None:
            return self._connection

        self._connection = await asyncpg.create_pool(
            user=DATABASE_user, database=DATABASE_name
        )
        await self._ensure_tables(self._connection)
        return self._connection

    async def add_snipe(self, snipe: Snipe):
        pool = await self.connect()

        async with pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO snipes(id, server, author, channel, mode, time, content) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                snipe.id,
                snipe.server,
                snipe.author,
                snipe.channel,
                snipe.mode.value,
                snipe.time.timestamp(),
                snipe.content,
            )

    # TODO: add contains
    async def get_snipes(
        self,
        *,
        server: int = None,
        author: int = None,
        channel: int = None,
        mode: SnipeMode = None,
        limit: int = None,
        negative: bool = False,
    ) -> tuple[list[Snipe], int]:
        pool = await self.connect()

        args = []
        query_parts = []
        row_limit = ""
        counter = count(start=1, step=1)

        if server is not None:
            query_parts.append(f"server = ${next(counter)}")
            args.append(server)

        if author is not None:
            query_parts.append(f"author = ${next(counter)}")
            args.append(author)

        if channel is not None:
            query_parts.append(f"channel = ${next(counter)}")
            args.append(channel)

        if mode is not None:
            query_parts.append(f"server = ${next(counter)}")
            args.append(mode.value)

        if query_parts:
            query = "WHERE " + " and ".join(query_parts) + " "
        else:
            query = ""

        if limit is not None:
            if limit > 10_000_000:
                raise RuntimeError(
                    f"requested limit of {limit} when the max is 10,000,000"
                )

            row_limit = f"LIMIT {limit}"

        if negative:
            order = "ASC"
        else:
            order = "DESC"

        async with pool.acquire() as connection:
            connection: asyncpg.Connection
            snipe_records = await connection.fetch(
                "SELECT * FROM snipes "
                + query
                + f"ORDER BY time {order} "
                + row_limit
                + ";",
                *args,
            )

            snipe_count_record = await connection.fetchrow(
                "SELECT count(*) FROM snipes " + query + ";", *args
            )
            snipe_count = snipe_count_record["count"]

            snipes = []
            for snipe_record in snipe_records:
                snipes.append(
                    Snipe(
                        id=snipe_record["id"],
                        mode=SnipeMode(snipe_record["mode"]),
                        author=snipe_record["author"],
                        content=snipe_record["content"],
                        server=snipe_record["server"],
                        channel=snipe_record["channel"],
                        time=pendulum.from_timestamp(snipe_record["time"]),
                    )
                )

            return snipes, snipe_count
