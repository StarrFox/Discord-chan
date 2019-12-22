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

from logic.games import Connect4


class games(commands.Cog):

    # Todo: test this
    @commands.command(aliases=['c4'])
    @commands.bot_has_permissions(add_reactions=True)
    async def connect4(self, ctx, member: discord.Member):
        """
        Play connect4 with another member
        First move is random
        """
        # this should probably be a converter
        if member == ctx.author or member.bot:
            return await ctx.send("You cannot play against yourself or a bot")

        player1 = choice([ctx.author, member])
        player2 = member if player1 == ctx.author else ctx.author

        game = Connect4(ctx, player1, player2)
        await game.run()


def setup(bot):
    bot.add_cog(games())
