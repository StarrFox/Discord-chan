import os
import sys
from typing import NamedTuple, Self

from sqlalchemy import (
    BigInteger,
    Integer,
    Float,
    Text,
    select,
    func,
    delete,
    desc,
    and_,
    distinct,
)
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import insert
import pendulum
from discord.ext.commands import CommandError
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


class Base(DeclarativeBase):
    pass


class SnipeRow(Base):
    __tablename__ = "snipes"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mode: Mapped[int] = mapped_column(Integer)
    server: Mapped[int] = mapped_column(BigInteger)
    author: Mapped[int] = mapped_column(BigInteger)
    channel: Mapped[int] = mapped_column(BigInteger)
    time: Mapped[float] = mapped_column(Float)
    content: Mapped[str] = mapped_column(Text)


class Coin(Base):
    __tablename__ = "coins"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    amount: Mapped[int] = mapped_column(BigInteger)


class EnabledFeature(Base):
    __tablename__ = "enabled_features"
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    feature_name: Mapped[str] = mapped_column(Text, primary_key=True)


class Stake(Base):
    __tablename__ = "stakes"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    amount: Mapped[float] = mapped_column(Float)
    bitcoin_price: Mapped[float] = mapped_column(Float)


class WordTrack(Base):
    __tablename__ = "word_track"
    server: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    author: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    word: Mapped[str] = mapped_column(Text, primary_key=True)
    count: Mapped[int] = mapped_column(Integer)


class MinecraftUsername(Base):
    __tablename__ = "minecraft_usernames"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(Text, unique=True)


class MinecraftDefaultServer(Base):
    __tablename__ = "minecraft_default_servers"
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    server_id: Mapped[str] = mapped_column(Text)


class MinecraftGuildLink(Base):
    __tablename__ = "minecraft_guild_links"
    first_guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # keep original column name typo to match existing DB
    seconrd_guild_id: Mapped[int] = mapped_column(
        "seconrd_guild_id", BigInteger, primary_key=True
    )


# TODO: this class is dog
class Database:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    @classmethod
    async def create(cls, debug_mode: bool = False) -> Self:
        password = "a" if debug_mode else None
        if password is None:
            url = f"postgresql+asyncpg://{DATABASE_user}@localhost/{DATABASE_name}"
        else:
            url = f"postgresql+asyncpg://{DATABASE_user}:{password}@localhost/{DATABASE_name}"

        engine = create_async_engine(url, future=True)
        async with engine.begin() as conn:
            # Create tables if they don't exist using ORM metadata
            await conn.run_sync(Base.metadata.create_all)
        return cls(engine)

    async def update_guild_default_minecraft_server(
        self, *, guild_id: int, server_id: str
    ):
        async with self.sessionmaker() as session:
            stmt = insert(MinecraftDefaultServer).values(
                guild_id=guild_id, server_id=server_id
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[MinecraftDefaultServer.guild_id],
                set_={"server_id": stmt.excluded.server_id},
            )
            await session.execute(stmt)
            await session.commit()

    async def get_guild_default_minecraft_server(self, *, guild_id: int) -> str | None:
        async with self.sessionmaker() as session:
            stmt = select(MinecraftDefaultServer).where(
                MinecraftDefaultServer.guild_id == guild_id
            )
            row = (await session.execute(stmt)).scalars().first()
            if row is not None:
                return row.server_id
        return None

    async def update_minecraft_username(self, *, user_id: int, username: str):
        async with self.sessionmaker() as session:
            stmt = insert(MinecraftUsername).values(user_id=user_id, username=username)
            stmt = stmt.on_conflict_do_update(
                index_elements=[MinecraftUsername.user_id],
                set_={"username": stmt.excluded.username},
            )
            await session.execute(stmt)
            await session.commit()

    async def get_minecraft_usernames(self) -> dict[int, str]:
        async with self.sessionmaker() as session:
            rows = (
                await session.execute(
                    select(MinecraftUsername.user_id, MinecraftUsername.username)
                )
            ).all()
        result: dict[int, str] = {}
        for user_id, username in rows:
            result[int(user_id)] = str(username)
        return result

    async def get_minecraft_username(self, user_id: int) -> str | None:
        async with self.sessionmaker() as session:
            row = await session.get(MinecraftUsername, user_id)
        if row is not None:
            return str(row.username)
        return None

    async def update_word_track_word(
        self, *, server_id: int, author_id: int, word: str, amount: int
    ):
        async with self.sessionmaker() as session:
            stmt = insert(WordTrack).values(
                server=server_id, author=author_id, word=word, count=amount
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[WordTrack.server, WordTrack.author, WordTrack.word],
                set_={"count": WordTrack.count + stmt.excluded.count},
            )
            await session.execute(stmt)
            await session.commit()

    async def get_server_word_track_leaderboard(
        self, *, server_id: int, author_id: int | None = None
    ) -> dict[str, int]:
        async with self.sessionmaker() as session:
            stmt = select(WordTrack.word, func.sum(WordTrack.count).label("sum")).where(
                WordTrack.server == server_id
            )
            if author_id is not None:
                stmt = stmt.where(WordTrack.author == author_id)
            stmt = stmt.group_by(WordTrack.word).order_by(
                desc(func.sum(WordTrack.count))
            )
            rows = (await session.execute(stmt)).all()
        result: dict[str, int] = {}
        for word, total in rows:
            result[str(word)] = int(total)
        return result

    async def get_member_bound_word_rank(
        self, *, server_id: int, word: str
    ) -> list[tuple[int, int]]:
        async with self.sessionmaker() as session:
            stmt = (
                select(WordTrack.author, WordTrack.count)
                .where(and_(WordTrack.server == server_id, WordTrack.word == word))
                .order_by(desc(WordTrack.count))
            )
            rows = (await session.execute(stmt)).all()
        return [(int(author), int(count)) for author, count in rows]

    # user_id: unique words
    async def get_word_track_unique_word_leaderboard(
        self,
        *,
        server_id: int | None = None,
    ):
        async with self.sessionmaker() as session:
            stmt = select(
                WordTrack.author, func.count(distinct(WordTrack.word)).label("count")
            )
            if server_id is not None:
                stmt = stmt.where(WordTrack.server == server_id)
            stmt = stmt.group_by(WordTrack.author).order_by(
                desc(func.count(distinct(WordTrack.word)))
            )
            rows = (await session.execute(stmt)).all()
        result: list[tuple[int, int]] = []
        for author, count_val in rows:
            result.append((int(author), int(count_val)))
        return result

    # user_id: total words
    async def get_word_track_total_word_leaderboard(
        self,
        *,
        server_id: int | None = None,
    ):
        async with self.sessionmaker() as session:
            stmt = select(WordTrack.author, func.sum(WordTrack.count).label("sum"))
            if server_id is not None:
                stmt = stmt.where(WordTrack.server == server_id)
            stmt = stmt.group_by(WordTrack.author).order_by(
                desc(func.sum(WordTrack.count))
            )
            rows = (await session.execute(stmt)).all()
        result: list[tuple[int, int]] = []
        for author, sum_val in rows:
            result.append((int(author), int(sum_val)))
        return result

    async def get_guild_enabled_features(self, guild_id: int) -> list[str]:
        async with self.sessionmaker() as session:
            rows = (
                (
                    await session.execute(
                        select(EnabledFeature.feature_name).where(
                            EnabledFeature.guild_id == guild_id
                        )
                    )
                )
                .scalars()
                .all()
            )
        return [str(name) for name in rows]

    async def enable_guild_enabled_feature(self, guild_id: int, feature_name: str):
        async with self.sessionmaker() as session:
            stmt = insert(EnabledFeature).values(
                guild_id=guild_id, feature_name=feature_name
            )
            stmt = stmt.on_conflict_do_nothing(
                index_elements=[EnabledFeature.guild_id, EnabledFeature.feature_name]
            )
            await session.execute(stmt)
            await session.commit()

    async def disable_guild_enabled_feature(self, guild_id: int, feature_name: str):
        async with self.sessionmaker() as session:
            await session.execute(
                delete(EnabledFeature).where(
                    and_(
                        EnabledFeature.guild_id == guild_id,
                        EnabledFeature.feature_name == feature_name,
                    )
                )
            )
            await session.commit()

    async def purge_feature(self, feature_name: str):
        async with self.sessionmaker() as session:
            await session.execute(
                delete(EnabledFeature).where(
                    EnabledFeature.feature_name == feature_name
                )
            )
            await session.commit()

    async def delete_coin_account(self, user_id: int):
        async with self.sessionmaker() as session:
            await session.execute(delete(Coin).where(Coin.user_id == user_id))
            await session.commit()
        logger.info(f"Deleted coin account {user_id}")

    async def get_coin_balance(self, user_id: int) -> int:
        async with self.sessionmaker() as session:
            amount = (
                await session.execute(
                    select(Coin.amount).where(Coin.user_id == user_id)
                )
            ).scalar_one_or_none()
            if amount is not None:
                return int(amount)
            return 0

    async def get_all_coin_balances(self) -> list[CoinsEntry]:
        async with self.sessionmaker() as session:
            rows = (
                await session.execute(
                    select(Coin.user_id, Coin.amount).order_by(desc(Coin.amount))
                )
            ).all()
        result: list[CoinsEntry] = []
        for user_id, amount in rows:
            result.append(CoinsEntry(int(user_id), int(amount)))
        return result

    async def set_coins(self, user_id: int, amount: int):
        async with self.sessionmaker() as session:
            stmt = insert(Coin).values(user_id=user_id, amount=amount)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Coin.user_id],
                set_={"amount": stmt.excluded.amount},
            )
            await session.execute(stmt)
            await session.commit()

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
        async with self.sessionmaker() as session:
            row = (
                await session.execute(
                    select(Stake.amount, Stake.bitcoin_price).where(
                        Stake.user_id == user_id
                    )
                )
            ).first()
            if row is not None:
                amount, btc = row
                return CoinStake(bitcoin_price=float(btc), coins=float(amount))
            return None

    async def set_coin_stake(self, user_id: int, amount: float, bitcoin_price: float):
        async with self.sessionmaker() as session:
            stmt = insert(Stake).values(
                user_id=user_id, amount=amount, bitcoin_price=bitcoin_price
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Stake.user_id],
                set_={
                    "amount": stmt.excluded.amount,
                    "bitcoin_price": stmt.excluded.bitcoin_price,
                },
            )
            await session.execute(stmt)
            await session.commit()
        logger.info(f"Set coin stake for {user_id}: {amount=} {bitcoin_price=}")

    async def clear_coin_stake(self, user_id: int):
        async with self.sessionmaker() as session:
            await session.execute(delete(Stake).where(Stake.user_id == user_id))
            await session.commit()
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
        async with self.sessionmaker() as session:
            row = SnipeRow(
                id=snipe.id,
                server=snipe.server,
                author=snipe.author,
                channel=snipe.channel,
                mode=snipe.mode.value,
                time=snipe.time.timestamp(),
                content=snipe.content,
            )
            session.add(row)
            await session.commit()

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
        order_desc = not negative

        async with self.sessionmaker() as session:
            conditions = []
            if server is not None:
                conditions.append(SnipeRow.server == server)
            if author is not None:
                conditions.append(SnipeRow.author == author)
            if channel is not None:
                conditions.append(SnipeRow.channel == channel)
            if contains is not None:
                conditions.append(SnipeRow.content.contains(contains))
            if mode is not None:
                conditions.append(SnipeRow.mode == mode.value)

            base_stmt = select(SnipeRow)
            if conditions:
                base_stmt = base_stmt.where(and_(*conditions))

            filtered = base_stmt.cte("filtered")

            order_expr = (
                filtered.c.time.desc() if order_desc else filtered.c.time.asc()
            )

            stmt = (
                select(
                    filtered.c.id,
                    filtered.c.mode,
                    filtered.c.server,
                    filtered.c.author,
                    filtered.c.channel,
                    filtered.c.time,
                    filtered.c.content,
                    select(func.count()).select_from(filtered).label("total_count"),
                )
                .order_by(order_expr)
            )

            if limit is not None:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                return [], 0

            total_count = int(rows[0].total_count)

            snipes: list[Snipe] = []
            for r in rows:
                snipes.append(
                    Snipe(
                        id=int(r.id),
                        mode=SnipeMode(int(r.mode)),
                        author=int(r.author),
                        content=str(r.content),
                        server=int(r.server),
                        channel=int(r.channel),
                        time=pendulum.from_timestamp(float(r.time)),
                    )
                )

            return snipes, total_count

    async def get_snipe_leaderboard(
        self, server_id: int | None = None
    ) -> dict[int, int]:
        async with self.sessionmaker() as session:
            stmt = select(SnipeRow.author, func.count(SnipeRow.author).label("count"))
            if server_id is not None:
                stmt = stmt.where(SnipeRow.server == server_id)
            stmt = stmt.group_by(SnipeRow.author).order_by(
                desc(func.count(SnipeRow.author))
            )
            rows = (await session.execute(stmt)).all()

        result: dict[int, int] = {}
        for author, count_val in rows:
            result[int(author)] = int(count_val)

        return result
