from datetime import datetime
from random import choice

import discord
from discord.ext import commands

from discord_chan import (
    Connect4,
    DiscordChan,
    MasterMindMenu,
    SliderGame,
    SubContext,
    utils,
)


class Games(commands.Cog, name="games"):
    def __init__(self, bot: DiscordChan) -> None:
        super().__init__()
        self.bot = bot

    @commands.command(aliases=["c4"])
    @commands.bot_has_permissions(add_reactions=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def connect4(self, ctx: SubContext, member: discord.Member):
        """
        Play connect4 with another member
        Who goes first is random
        """
        # this should probably be a converter
        if member == ctx.author or member.bot:
            return await ctx.send("You cannot play against yourself or a bot.")

        # Command already requires add_reactions so don't need to check for it
        if not await ctx.prompt(f"{member.mention} agree to play?", owner_id=member.id):
            return await ctx.send("Game canceled.")

        player1 = choice([ctx.author, member])
        player2 = member if player1 == ctx.author else ctx.author

        if not isinstance(player1, discord.Member) or not isinstance(
            player2, discord.Member
        ):
            return await ctx.send("connect 4 must be used from a server")

        game = Connect4(player1, player2)
        winner = await game.run(ctx)
        if winner:
            if isinstance(winner, tuple):
                await ctx.send(f"{player1.mention} and {player2.mention} tied")
            else:
                await ctx.send(f"{winner.mention} has won.")
        else:
            await ctx.send("No one made a move.")

    @commands.command(aliases=["mm"])
    @commands.bot_has_permissions(add_reactions=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def mastermind(self, ctx: SubContext):
        """
        Play mastermind.
        """
        game = MasterMindMenu()
        value = await game.run(ctx)

        if value:
            await ctx.send(f"{ctx.author.mention}, You won.")

        elif value == 0:
            return

        else:
            await ctx.send(f"{ctx.author.mention}, MasterMind timed out.")

    @commands.command(aliases=["sg"])
    @commands.bot_has_permissions(add_reactions=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def slidergame(self, ctx: SubContext):
        """
        Play SliderGame.
        """
        # timeout = 10 minutes
        game = SliderGame(timeout=10 * 60)
        # perf_counter didn't work for some reason
        start = datetime.utcnow()
        won_game, moves = await game.run(ctx)
        stop = datetime.utcnow()

        time_delta = stop - start

        time_msg = utils.detailed_human_time(time_delta.total_seconds())

        if won_game:
            await ctx.send(
                f"{ctx.author.mention} has completed the slider in {moves} move(s) within {time_msg};"
                " adding 1 coin for finishing",
                allowed_mentions=discord.AllowedMentions(users=True),
            )

            await self.bot.database.add_coins(ctx.author.id, 1)

        else:
            await ctx.send(
                f"{ctx.author.mention} forfeited or their slidergame timed out."
            )


async def setup(bot):
    await bot.add_cog(Games(bot))
