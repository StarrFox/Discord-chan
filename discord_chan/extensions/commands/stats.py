# -*- coding: utf-8 -*-
#  Copyright © 2020 StarrFox
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

from discord.ext import commands


class Stats(commands.Cog, name="stats"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Todo: message and activity stat graphs
    # Todo: command_uses show times of day

    # @commands.command()
    # async def uses(self, ctx: commands.Context):
    #     """View top used commands"""
    #     pass


def setup(bot: commands.Bot):
    bot.add_cog(Stats(bot))
