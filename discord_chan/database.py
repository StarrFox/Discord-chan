import os
import sys
from itertools import count
from typing import NamedTuple, Self

import asyncpg
import pendulum
from discord.ext.commands import CommandError  # type: ignore
from loguru import logger

from discord_chan.snipe import Snipe, SnipeMode

try:
    import pwd
except ImportError:
    pwd = None


def get_current_username() -> str:
    match sys.platform:
        case "win32":
            user = os.environ.get("USERNAME")

            if user is not None:
                return user

            raise ValueError("Couldn't find username")

        case "linux":
            user = os.environ.get("USER")

            if user is not None:
                return user

            # should be there on linux
            assert pwd is not None
            return pwd.getpwuid(os.getuid()).pw_name  # type: ignore (.getpwuid not on windows but we check platform above)
        case _:
            raise NotImplementedError()


# TODO: add environment variables for these
DATABASE_user = get_current_username()
DATABASE_name = "discord_chan"


class CoinsEntry(NamedTuple):
    user_id: int
    coins: int


class CoinStake(NamedTuple):
    bitcoin_price: float
    coins: float


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

CREATE TABLE IF NOT EXISTS enabled_features (
    guild_id BIGINT,
    feature_name TEXT,
    PRIMARY KEY (guild_id, feature_name)
);

CREATE TABLE IF NOT EXISTS stakes (
    user_id BIGINT PRIMARY KEY,
    amount FLOAT,
    bitcoin_price FLOAT
);

CREATE TABLE IF NOT EXISTS word_track (
    server BIGINT,
    author BIGINT,
    word TEXT,
    count INT,
    PRIMARY KEY (server, author, word)
);

CREATE TABLE IF NOT EXISTS minecraft_usernames (
    user_id BIGINT PRIMARY KEY,
    username TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS minecraft_default_servers (
    guild_id BIGINT PRIMARY KEY,
    server_id TEXT
);

CREATE TABLE IF NOT EXISTS minecraft_guild_links (
    first_guild_id BIGINT,
    seconrd_guild_id BIGINT,
    PRIMARY KEY (first_guild_id, seconrd_guild_id)
);
""".strip()


# TODO: this class is dog
class Database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    @classmethod
    async def create(cls, debug_mode: bool = False) -> Self:
        password = "a" if debug_mode else None

        pool = await asyncpg.create_pool(
            user=DATABASE_user, database=DATABASE_name, password=password
        )
        await pool.execute(DBSCHEMA)
        return cls(pool)

    async def update_guild_default_minecraft_server(
        self, *, guild_id: int, server_id: str
    ):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO minecraft_default_servers (guild_id, server_id) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET server_id = EXCLUDED.server_id;",
                guild_id,
                server_id,
            )

    async def get_guild_default_minecraft_server(self, *, guild_id: int) -> str | None:
        if record := await self.pool.fetchrow(
            "SELECT guild_id, server_id FROM minecraft_default_servers where guild_id = $1;",
            guild_id,
        ):
            return record["server_id"]

        return None

    async def update_minecraft_username(self, *, user_id: int, username: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO minecraft_usernames (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username;",
                user_id,
                username,
            )

    async def get_minecraft_usernames(self) -> dict[int, str]:
        async with self.pool.acquire() as connection:
            records: list[asyncpg.Record] = await connection.fetch(
                "SELECT user_id, username FROM minecraft_usernames;"
            )

        result: dict[int, str] = {}

        for record in records:
            result[record["user_id"]] = record["username"]

        return result

    async def get_minecraft_username(self, user_id: int) -> str | None:
        async with self.pool.acquire() as connection:
            record: asyncpg.Record | None = await connection.fetchrow(
                "SELECT user_id, username FROM minecraft_usernames WHERE user_id = $1;",
                user_id,
            )

        if record is not None:
            return record["username"]

        return None

    async def update_word_track_word(
        self, *, server_id: int, author_id: int, word: str, amount: int
    ):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO word_track (server, author, word, count) VALUES ($1, $2, $3, $4) ON CONFLICT (server, author, word) DO UPDATE SET count = EXCLUDED.count + word_track.count;",
                server_id,
                author_id,
                word,
                amount,
            )

    async def get_server_word_track_leaderboard(
        self, *, server_id: int, author_id: int | None = None
    ) -> dict[str, int]:
        params = [server_id]

        if author_id is not None:
            author_condition = "and author = $2"
            params.append(author_id)

        else:
            author_condition = ""

        async with self.pool.acquire() as connection:
            records: list[asyncpg.Record] = await connection.fetch(
                f"SELECT word, sum(count) FROM word_track WHERE server = $1 {author_condition} GROUP BY word ORDER BY sum DESC;",
                *params,
            )

        result: dict[str, int] = {}

        for record in records:
            result[record["word"]] = record["sum"]

        return result

    async def get_member_bound_word_rank(
        self, *, server_id: int, word: str
    ) -> list[tuple[int, int]]:
        async with self.pool.acquire() as connection:
            records: list[asyncpg.Record] = await connection.fetch(
                "SELECT author, count FROM word_track WHERE server = $1 AND word = $2 ORDER BY count DESC;",
                server_id,
                word,
            )

        result: list[tuple[int, int]] = []

        for record in records:
            result.append((record["author"], record["count"]))

        return result

    # user_id: unique words
    async def get_word_track_unique_word_leaderboard(
        self,
        *,
        server_id: int | None = None,
    ):
        params: list[int] = []

        if server_id is not None:
            server_clause = "WHERE server = $1"
            params.append(server_id)
        else:
            server_clause = ""

        async with self.pool.acquire() as connection:
            records: list[asyncpg.Record] = await connection.fetch(
                f"SELECT author, count(word) FROM word_track {server_clause} GROUP BY author ORDER BY count DESC;",
                *params,
            )

        result: list[tuple[int, int]] = []

        for record in records:
            result.append((record["author"], record["count"]))

        return result

    # user_id: total words
    async def get_word_track_total_word_leaderboard(
        self,
        *,
        server_id: int | None = None,
    ):
        params: list[int] = []

        if server_id is not None:
            server_clause = "WHERE server = $1"
            params.append(server_id)
        else:
            server_clause = ""

        async with self.pool.acquire() as connection:
            records: list[asyncpg.Record] = await connection.fetch(
                f"SELECT author, sum(count) FROM word_track {server_clause} GROUP BY author ORDER BY sum DESC;",
                *params,
            )

        result: list[tuple[int, int]] = []

        for record in records:
            result.append((record["author"], record["sum"]))

        return result

    async def get_guild_enabled_features(self, guild_id: int) -> list[str]:
        async with self.pool.acquire() as connection:
            records: list[asyncpg.Record] = await connection.fetch(
                "SELECT feature_name FROM enabled_features WHERE guild_id = $1;",
                guild_id,
            )

            result: list[str] = []

            for record in records:
                result.append(record["feature_name"])

        return result

    async def enable_guild_enabled_feature(self, guild_id: int, feature_name: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO enabled_features (guild_id, feature_name) VALUES ($1, $2);",
                guild_id,
                feature_name,
            )

    async def disable_guild_enabled_feature(self, guild_id: int, feature_name: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "DELETE FROM enabled_features WHERE guild_id = $1 AND feature_name = $2;",
                guild_id,
                feature_name,
            )

    async def purge_feature(self, feature_name: str):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "DELETE FROM enabled_features WHERE feature_name = $1;",
                feature_name,
            )

    async def delete_coin_account(self, user_id: int):
        async with self.pool.acquire() as connection:
            await connection.execute("DELETE FROM coins WHERE user_id = $1;", user_id)

        logger.info(f"Deleted coin account {user_id}")

    async def get_coin_balance(self, user_id: int) -> int:
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM coins WHERE user_id = $1;", user_id
            )

            if row is not None:
                return row["amount"]

            return 0

    async def get_all_coin_balances(self) -> list[CoinsEntry]:
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT user_id, amount FROM coins ORDER BY amount DESC;"
            )

            result: list[CoinsEntry] = []
            for row in rows:
                result.append(CoinsEntry(row["user_id"], row["amount"]))

            return result

    async def set_coins(self, user_id: int, amount: int):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO coins (user_id, amount) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET amount = EXCLUDED.amount;",
                user_id,
                amount,
            )

        logger.info(f"Set coin account {user_id} to {amount}")

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

    async def get_coin_stake(self, user_id: int) -> CoinStake | None:
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                "SELECT * FROM stakes WHERE user_id = $1;", user_id
            )

            if row is not None:
                return CoinStake(
                    bitcoin_price=row["bitcoin_price"], coins=row["amount"]
                )

            # explicit None for non-existing account
            return None

    async def set_coin_stake(self, user_id: int, amount: float, bitcoin_price: float):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "INSERT INTO stakes (user_id, amount, bitcoin_price) VALUES ($1, $2, $3) ON CONFLICT (user_id) DO UPDATE SET amount = EXCLUDED.amount, bitcoin_price = EXCLUDED.bitcoin_price;",
                user_id,
                amount,
                bitcoin_price,
            )

        logger.info(f"Set coin stake for {user_id}: {amount=} {bitcoin_price=}")

    async def clear_coin_stake(self, user_id: int):
        async with self.pool.acquire() as connection:
            await connection.execute(
                "DELETE FROM stakes WHERE user_id = $1;",
                user_id,
            )

        logger.info(f"Cleared coin stake for {user_id}")

    async def add_coin_stake(self, user_id: int, amount: float, bitcoin_price: float):
        current = await self.get_coin_stake(user_id)

        if current is None:
            new_balance = amount
        else:
            new_balance = current.coins + amount

        # TODO: are python floats bit limited?

        await self.set_coin_stake(user_id, new_balance, bitcoin_price)
        return new_balance

    async def remove_coin_stakes(
        self, user_id: int, amount: float, bitcoin_price: float
    ):
        current = await self.get_coin_stake(user_id)

        if current is None:
            new_balance = amount
        else:
            new_balance = current.coins - amount

        await self.set_coin_stake(user_id, new_balance, bitcoin_price)
        return new_balance

    async def add_snipe(self, snipe: Snipe):
        async with self.pool.acquire() as connection:
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

    async def get_snipes(
        self,
        *,
        server: int | None = None,
        author: int | None = None,
        channel: int | None = None,
        contains: str | None = None,
        mode: SnipeMode | None = None,
        limit: int | None = None,
        negative: bool = False,
    ) -> tuple[list[Snipe], int]:
        args: list[int | str] = []
        query_parts: list[str] = []
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

        if contains is not None:
            # the position function returns 1 or above if the substring is within content
            query_parts.append(f"position(${next(counter)} in content) > 0")
            args.append(contains)

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

        async with self.pool.acquire() as connection:
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

            snipes: list[Snipe] = []
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

    async def get_snipe_leaderboard(
        self, server_id: int | None = None
    ) -> dict[int, int]:
        if server_id:
            where = "where server = $1"
            params = [server_id]
        else:
            where = ""
            params = []

        async with self.pool.acquire() as connection:
            records: list[asyncpg.Record] = await connection.fetch(
                f"SELECT author, count(author) from snipes {where} group by author order by count desc;",
                *params,
            )

            result: dict[int, int] = {}

            for record in records:
                result[record["author"]] = record["count"]

        return result
