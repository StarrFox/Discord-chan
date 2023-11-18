import asyncio
import random
import typing
from math import floor
from typing import Literal

import aiohttp
import discord
from discord.ext import commands
from loguru import logger

import discord_chan
from discord_chan import DiscordChan, SubContext
from discord_chan.converters import OverConverter
from discord_chan.menus import DCMenuPages, NormalPageSource

BITCOIN_PRICE_URL = "https://api.binance.us/api/v3/ticker/price?symbol=BTCUSDT"


class Gambling(commands.Cog):
    def __init__(self, bot: "DiscordChan") -> None:
        super().__init__()
        self.bot = bot

        self._btcprice: float | None = None
        self._btc_cooldown_task: asyncio.Task | None = None
        self._btc_price_lock = asyncio.Lock()

    async def has_amount(self, user_id: int, amount: int) -> bool:
        balance = await self.bot.database.get_coin_balance(user_id)
        return balance >= amount

    async def get_btc_price(self) -> float:
        async with self._btc_price_lock:
            if self._btc_cooldown_task is not None:
                if self._btcprice is None:
                    raise RuntimeError("btc price unset while cooldown task is ticking")

                return self._btcprice

            async with aiohttp.ClientSession() as session:
                async with session.get(BITCOIN_PRICE_URL) as response:
                    response.raise_for_status()
                    response_json = await response.json()
                    price = float(response_json["price"])

            self._btcprice = price

            async def _cooldown_task():
                await asyncio.sleep(60)
                # is this ok?
                self._btc_cooldown_task = None

            self._btc_cooldown_task = asyncio.create_task(_cooldown_task())
            return self._btcprice

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def coins(self, ctx: "SubContext", member: discord.Member | None = None):
        """
        View another member or your aacoin amount.
        """
        if member is None:
            # the guild_only check should make this always true
            assert isinstance(ctx.author, discord.Member)
            member = ctx.author

        amount = await self.bot.database.get_coin_balance(member.id)
        plural = amount != 1
        await ctx.send(f"{member} has {amount} coin{'s' if plural else ''}")

    # this is called admin_add to not be confused with the give command
    @coins.command()
    @discord_chan.checks.guild_owner()
    async def admin_add(self, ctx: "SubContext", member: discord.Member, amount: int):
        """
        Add coins to a member
        """
        await self.bot.database.add_coins(member.id, amount)
        await ctx.send(f"Added {amount} to {member}'s coin balance")

    @coins.command()
    async def give(
        self,
        ctx: "SubContext",
        member: discord.Member,
        amount: typing.Annotated[int, OverConverter(0)],
    ):
        """Give some of your coins to another member"""
        if not await self.has_amount(ctx.author.id, amount):
            return await ctx.send(f"You don't have enough coins to give {amount}")

        singular = "" if amount == 1 else "s"

        if await ctx.prompt(
            f"Are you sure you want to send {amount} coin{singular} to {member.mention}",
            owner_id=ctx.author.id,
        ):
            await self.bot.database.remove_coins(ctx.author.id, amount)
            await self.bot.database.add_coins(member.id, amount)
            await ctx.send("Sent")
        else:
            await ctx.send("Sending canceled")

    @coins.command(name="all")
    async def view_all_coins(self, ctx: "SubContext"):
        """
        View all coins sorted by amount.
        """
        lb = await self.bot.database.get_all_coin_balances()

        if not lb:
            return await ctx.send("No one has any coins right now")

        entries: list[str] = []
        for user_id, coins in lb:
            assert ctx.guild is not None
            # attempt cache pull first
            if (member := ctx.guild.get_member(user_id)) is not None:
                entries.append(f"{member}: {coins}")
                continue

            try:
                member = str(await ctx.guild.fetch_member(user_id))
            except discord.NotFound:
                logger.warning(f"Unbound user id {user_id} in coin db")
                member = str(user_id)
            except Exception as exc:
                logger.critical(f"Unhandled exception in view all: {exc}")
                member = str(user_id)
            finally:
                entries.append(f"{member}: {coins}")

        source = NormalPageSource(entries, per_page=10)
        menu = DCMenuPages(source)
        await menu.start(ctx)

    @coins.group()
    async def stake(self, ctx: "SubContext", amount: int | None = None):
        """
        Stake some coins against the price of btc
        use stake exit to then exit
        """
        if amount is None:
            stake = await self.bot.database.get_coin_stake(ctx.author.id)

            if stake is None:
                return await ctx.send("You don't have any coins staked")

            adjusted = round(
                await self._adjust_coins(stake.bitcoin_price, stake.coins), 2
            )

            return await ctx.send(f"Current stake is {adjusted}")

        if amount < 1:
            return await ctx.send("Stake must be positive")

        if not await self.has_amount(ctx.author.id, amount):
            return await ctx.send(f"You don't have enough coins to stake {amount}")

        bitcoin_price = await self.get_btc_price()

        stake = await self.bot.database.get_coin_stake(ctx.author.id)

        singular = "" if amount == 1 else "s"

        if stake is None:
            await self.bot.database.add_coin_stake(ctx.author.id, amount, bitcoin_price)
            await self.bot.database.remove_coins(ctx.author.id, amount)
            await ctx.send(f"Staked {amount} coin{singular} at {bitcoin_price}$ BTC")

        else:
            adjusted = await self._adjust_coins(stake.bitcoin_price, stake.coins)
            total = adjusted + amount
            await self.bot.database.set_coin_stake(ctx.author.id, total, bitcoin_price)
            await self.bot.database.remove_coins(ctx.author.id, amount)
            await ctx.send(
                f"Staked {amount} more coin{singular} for a total of {round(total, 2)}; now at {bitcoin_price}$ BTC"
            )

    @coins.command()
    async def exit(self, ctx: "SubContext"):
        """
        Exit from your stake
        """
        stake = await self.bot.database.get_coin_stake(ctx.author.id)

        if stake is None:
            return ctx.send("You have no staked coins")

        exit_coins = floor(await self._adjust_coins(stake.bitcoin_price, stake.coins))
        change = round(((exit_coins / stake.coins) - 1) * 100, 2)

        await self.bot.database.add_coins(ctx.author.id, exit_coins)
        await self.bot.database.clear_coin_stake(ctx.author.id)

        singular = "" if exit_coins == 1 else "s"

        await ctx.send(f"{change}% change resulting in {exit_coins} coin{singular}")

    async def _adjust_coins(self, old_price, coin_amount) -> float:
        new_price = await self.get_btc_price()

        ratio = new_price / old_price
        return coin_amount * ratio

    @commands.command(aliases=["cf"])
    async def coinflip(self, ctx: "SubContext", guess: Literal["h", "t"], bet: int):
        """
        Guess a coinflip with h or t
        win or lose bet amount
        """
        if bet < 1:
            return await ctx.send("Bet must be positive")

        if not await self.has_amount(ctx.author.id, bet):
            return await ctx.send(f"You don't have enough coins to bet {bet}")

        outcome = random.choice(["h", "t"])

        status = "won"
        gain = bet
        if guess != outcome:
            gain = -bet
            status = "lost"

        await self.bot.database.add_coins(ctx.author.id, gain)

        singular = "" if bet == 1 else "s"

        await ctx.send(f"You {status} {bet} coin{singular}")


async def setup(bot):
    await bot.add_cog(Gambling(bot))
