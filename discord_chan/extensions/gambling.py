import random
from typing import TYPE_CHECKING, Literal, Optional
import typing

import discord
from discord.ext import commands
from loguru import logger

import discord_chan
from discord_chan.converters import OverConverter
from discord_chan.menus import DCMenuPages, NormalPageSource

if TYPE_CHECKING:
    from discord_chan import DiscordChan, SubContext


class Gambling(commands.Cog):
    def __init__(self, bot: "DiscordChan") -> None:
        super().__init__()
        self.bot = bot

    async def has_amount(self, user_id: int, amount: int) -> bool:
        balance = await self.bot.database.get_coin_balance(user_id)
        return balance >= amount

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def coins(self, ctx: "SubContext", member: Optional[discord.Member] = None):
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
        amount: typing.Annotated[int, OverConverter(0)]
        ):
        """Give some of your coins to another member"""
        if not await self.has_amount(ctx.author.id, amount):
            return await ctx.send(f"You don't have enough coins to give {amount}")

        singular = "" if amount == 1 else "s"

        if await ctx.prompt(
            f"Are you sure you want to send {amount} coin{singular} to {member.mention}",
            owner_id=ctx.author.id
            ):
            await self.bot.database.remove_coins(ctx.author.id, amount)
            await self.bot.database.add_coins(member.id, amount)
            await ctx.send("sent")
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

        entries = []
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
        await ctx.send(f"You {status} {bet} coins")


async def setup(bot):
    await bot.add_cog(Gambling(bot))
