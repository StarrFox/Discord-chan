#  Copyright © 2019 StarrFox
#
#  Discord Chan is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Discord Chan is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Discord Chan.  If not, see <https://www.gnu.org/licenses/>.

from random import choice

import discord
from discord.ext import commands

from discord_chan import Connect4, MasterMindMenu, SliderGame, SubContext


class Games(commands.Cog, name="games"):
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
        game = SliderGame()
        await game.start(ctx, wait=True)


def setup(bot):
    bot.add_cog(Games())
