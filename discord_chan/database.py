import asyncio
import os
import pwd
from itertools import count
from typing import NamedTuple, Optional

import asyncpg
import pendulum
from discord.ext.commands import CommandError
from loguru import logger

from discord_chan.snipe import Snipe, SnipeMode


def get_current_username() -> str:
    return pwd.getpwuid(os.getuid()).pw_name


# TODO: add enviorment variables for these
DATABASE_user = get_current_username()
DATABASE_name = "discord_chan"


class CoinsEntry(NamedTuple):
    user_id: int
    coins: int


DBSCHEMA = """
CREATE TABLE IF NOT EXISTS snipes (
    id BIGINT,
    mode INT,
    server BIGINT,
    author BIGINT,
    channel BIGINT,
    time FLOAT,
    content TEXT
);

CREATE TABLE IF NOT EXISTS coins (
    user_id BIGINT PRIMARY KEY,
    amount BIGINT
);
""".strip()


class Database:
    def __init__(self):
        self._connection: Optional[asyncpg.Pool] = None
        self._ensured: bool = False
        self._connection_lock = asyncio.Lock()

    async def _ensure_tables(self, pool: asyncpg.Pool):
        # A lock isnt needed here because .connect is already locked
        if self._ensured:
            return

        self._ensured = True

        async with pool.acquire() as connection:
            await connection.execute(DBSCHEMA)

    async def connect(self) -> asyncpg.Pool:
        async with self._connection_lock:
            if self._connection is not None:
                return self._connection

            self._connection = await asyncpg.create_pool(
                user=DATABASE_user, database=DATABASE_name
            )
            assert self._connection is not None
            await self._ensure_tables(self._connection)
            return self._connection

    async def delete_coin_account(self, user_id: int):
        pool = await self.connect()

        async with pool.acquire() as connection:
            await connection.execute("DELETE FROM coins WHERE user_id = $1;", user_id)

        logger.info(f"Deleted coin account {user_id}")

    async def get_coin_balance(self, user_id: int) -> int:
        pool = await self.connect()

        async with pool.acquire() as connection:
            connection: asyncpg.Connection
            row = await connection.fetchrow(
                "SELECT * FROM coins WHERE user_id = $1;", user_id
            )

            if row is not None:
                return row["amount"]

            return 0

    async def get_all_coin_balances(self) -> list[CoinsEntry]:
        pool = await self.connect()

        async with pool.acquire() as connection:
            connection: asyncpg.Connection
            rows = await connection.fetch(
                "SELECT user_id, amount FROM coins ORDER BY amount DESC;"
            )

            result = []
            for row in rows:
                result.append((row["user_id"], row["amount"]))

            return result

    async def set_coins(self, user_id: int, amount: int):
        pool = await self.connect()

        async with pool.acquire() as connection:
            connection: asyncpg.Connection
            await connection.execute(
                "INSERT INTO coins (user_id, amount) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET amount = EXCLUDED.amount;",
                user_id,
                amount,
            )

        logger.info(f"Set coin account {user_id} to {amount}.")

    async def add_coins(self, user_id: int, amount: int):
        current = await self.get_coin_balance(user_id)
        new_balance = current + amount
        if new_balance.bit_length() >= 64:
            raise CommandError(
                "New balance would be over int64, are you sure you need that many coins?"
            )
        await self.set_coins(user_id, new_balance)
        return new_balance

    async def remove_coins(self, user_id: int, amount: int):
        current = await self.get_coin_balance(user_id)
        new_balance = current - amount
        if new_balance.bit_length() >= 64:
            raise CommandError(
                "New balance would be over int64, are you sure you need that many coins?"
            )
        await self.set_coins(user_id, new_balance)
        return new_balance

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
        server: Optional[int] = None,
        author: Optional[int] = None,
        channel: Optional[int] = None,
        mode: Optional[SnipeMode] = None,
        limit: Optional[int] = None,
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
            query_parts.append(f"mode = ${next(counter)}")
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
            if snipe_count_record is None:
                snipe_count = 0
            else:
                snipe_count: int = snipe_count_record["count"]

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
