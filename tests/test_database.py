import pytest
import pendulum

from discord_chan.database import Database, Base
from discord_chan.snipe import Snipe, SnipeMode


@pytest.fixture
async def db():
    db = await Database.create(debug_mode=True)
    # fresh database (drop and recreate all tables)
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield db


@pytest.mark.asyncio
async def test_coins(db: Database):
    # initial balance is zero
    assert await db.get_coin_balance(1) == 0

    # set and get
    await db.set_coins(1, 100)
    assert await db.get_coin_balance(1) == 100

    # add and remove
    assert await db.add_coins(1, 50) == 150
    assert await db.get_coin_balance(1) == 150

    assert await db.remove_coins(1, 25) == 125
    assert await db.get_coin_balance(1) == 125

    # multiple users and leaderboard ordering
    await db.set_coins(2, 300)
    await db.set_coins(3, 200)
    balances = await db.get_all_coin_balances()
    assert [b.user_id for b in balances] == [2, 3, 1]
    assert [b.coins for b in balances] == [300, 200, 125]

    # delete account
    await db.delete_coin_account(1)
    assert await db.get_coin_balance(1) == 0


@pytest.mark.asyncio
async def test_stakes(db: Database):
    # none initially
    assert await db.get_coin_stake(10) is None

    await db.set_coin_stake(10, 1.5, 42000.0)
    stake = await db.get_coin_stake(10)
    assert stake is not None
    assert stake.coins == 1.5
    assert stake.bitcoin_price == 42000.0

    # add and remove
    assert await db.add_coin_stake(10, 0.5, 43000.0) == 2.0
    stake = await db.get_coin_stake(10)
    assert stake is not None
    assert stake.coins == 2.0

    assert await db.remove_coin_stakes(10, 0.25, 41000.0) == 1.75
    stake = await db.get_coin_stake(10)
    assert stake is not None
    assert stake.coins == 1.75

    await db.clear_coin_stake(10)
    assert await db.get_coin_stake(10) is None


@pytest.mark.asyncio
async def test_enabled_features(db: Database):
    guild = 111
    # enable two features
    await db.enable_guild_enabled_feature(guild, "alpha")
    await db.enable_guild_enabled_feature(guild, "beta")

    feats = await db.get_guild_enabled_features(guild)
    assert set(feats) == {"alpha", "beta"}

    # idempotent insert
    await db.enable_guild_enabled_feature(guild, "alpha")
    feats = await db.get_guild_enabled_features(guild)
    assert set(feats) == {"alpha", "beta"}

    await db.disable_guild_enabled_feature(guild, "alpha")
    feats = await db.get_guild_enabled_features(guild)
    assert feats == ["beta"]

    # purge by feature name across guilds
    await db.enable_guild_enabled_feature(222, "beta")
    await db.purge_feature("beta")
    assert await db.get_guild_enabled_features(guild) == []
    assert await db.get_guild_enabled_features(222) == []


@pytest.mark.asyncio
async def test_minecraft_data(db: Database):
    # usernames
    await db.update_minecraft_username(user_id=1, username="Steve")
    await db.update_minecraft_username(user_id=2, username="Alex")
    assert await db.get_minecraft_username(1) == "Steve"
    assert await db.get_minecraft_username(2) == "Alex"

    # overwrite username
    await db.update_minecraft_username(user_id=1, username="Herobrine")
    assert await db.get_minecraft_username(1) == "Herobrine"

    all_usernames = await db.get_minecraft_usernames()
    assert all_usernames[1] == "Herobrine"
    assert all_usernames[2] == "Alex"

    # default server per guild
    assert await db.get_guild_default_minecraft_server(guild_id=123) is None
    await db.update_guild_default_minecraft_server(
        guild_id=123, server_id="mc.example.com"
    )
    assert await db.get_guild_default_minecraft_server(guild_id=123) == "mc.example.com"
    # update
    await db.update_guild_default_minecraft_server(
        guild_id=123, server_id="mc2.example.com"
    )
    assert (
        await db.get_guild_default_minecraft_server(guild_id=123) == "mc2.example.com"
    )


@pytest.mark.asyncio
async def test_word_track(db: Database):
    # server 1, user 1 and 2
    await db.update_word_track_word(server_id=1, author_id=1, word="hello", amount=2)
    await db.update_word_track_word(server_id=1, author_id=1, word="world", amount=5)
    await db.update_word_track_word(server_id=1, author_id=2, word="hello", amount=3)
    # server 2
    await db.update_word_track_word(server_id=2, author_id=1, word="hello", amount=7)

    # server-specific leaderboard
    lb = await db.get_server_word_track_leaderboard(server_id=1)
    assert lb == {"world": 5, "hello": 5}

    # author-specific within server
    lb_auth = await db.get_server_word_track_leaderboard(server_id=1, author_id=1)
    assert lb_auth == {"world": 5, "hello": 2}

    # member bound rank for a word in a server
    ranks = await db.get_member_bound_word_rank(server_id=1, word="hello")
    assert ranks == [(2, 3), (1, 2)]

    # unique word leaderboard (across servers)
    unique_lb = await db.get_word_track_unique_word_leaderboard()
    assert unique_lb == [(1, 2), (2, 1)]

    # total word leaderboard filtered by server
    total_lb_s1 = await db.get_word_track_total_word_leaderboard(server_id=1)
    assert total_lb_s1 == [(1, 7), (2, 3)]

    total_lb_all = await db.get_word_track_total_word_leaderboard()
    assert total_lb_all == [(1, 14), (2, 3)]


@pytest.mark.asyncio
async def test_snipes(db: Database):
    now = pendulum.now()
    snipes = [
        Snipe(
            id=1,
            mode=SnipeMode.edited,
            author=100,
            content="hello world",
            server=10,
            channel=1000,
            time=now.subtract(seconds=3),
        ),
        Snipe(
            id=2,
            mode=SnipeMode.deleted,
            author=100,
            content="goodbye",
            server=10,
            channel=1000,
            time=now.subtract(seconds=2),
        ),
        Snipe(
            id=3,
            mode=SnipeMode.purged,
            author=200,
            content="HELLO",
            server=20,
            channel=2000,
            time=now.subtract(seconds=1),
        ),
    ]
    for s in snipes:
        await db.add_snipe(s)

    # basic fetch count and default ordering (desc by time)
    fetched, total = await db.get_snipes()
    assert total == 3
    assert [s.id for s in fetched] == [3, 2, 1]

    # filters
    fetched, total = await db.get_snipes(server=10)
    assert total == 2
    assert [s.id for s in fetched] == [2, 1]

    fetched, total = await db.get_snipes(author=100)
    assert total == 2
    assert [s.id for s in fetched] == [2, 1]

    fetched, total = await db.get_snipes(channel=2000)
    assert total == 1
    assert [s.id for s in fetched] == [3]

    fetched, total = await db.get_snipes(contains="hello")
    # case-sensitive .contains in SQLAlchemy maps to LIKE which is case-sensitive depending on collation; our inserted one is lowercase only id=1
    assert [s.id for s in fetched] == [1]

    fetched, total = await db.get_snipes(mode=SnipeMode.deleted)
    assert [s.id for s in fetched] == [2]

    # limit and negative ordering (asc)
    fetched, total = await db.get_snipes(limit=2, negative=True)
    assert [s.id for s in fetched] == [1, 2]

    # leaderboard
    lb = await db.get_snipe_leaderboard()
    assert lb == {100: 2, 200: 1}

    lb10 = await db.get_snipe_leaderboard(server_id=10)
    assert lb10 == {100: 2}
