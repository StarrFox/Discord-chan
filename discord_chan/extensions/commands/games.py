# -*- coding: utf-8 -*-
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

from discord_chan import Connect4, SubContext, MasterMindMenu


class Games(commands.Cog, name='games'):

    @commands.command(aliases=['c4'])
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

        player1 = choice([ctx.author, member])
        player2 = member if player1 == ctx.author else ctx.author

        game = Connect4(player1, player2)
        winner = await game.run(ctx)
        if winner:
            await ctx.send(f"{winner.mention} has won.", escape_mentions=False, no_edit=True)
        else:
            await ctx.send('No one made a move.', no_edit=True)

    @commands.command(aliases=['mm'])
    @commands.bot_has_permissions(add_reactions=True)
    @commands.max_concurrency(1, commands.BucketType.user)
    async def mastermind(self, ctx: SubContext):
        """
        Play mastermind.
        """
        game = MasterMindMenu()
        value = await game.run(ctx)

        if value:
            await ctx.send(f'{ctx.author.mention}, You won.', escape_mentions=False, no_edit=True)

        elif value == 0:
            return

        else:
            await ctx.send(f'{ctx.author.mention}, MasterMind timed out.', escape_mentions=False, no_edit=True)


def setup(bot):
    bot.add_cog(Games())
