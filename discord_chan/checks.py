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

from typing import List

from discord.ext import commands


class CogNotLoaded(commands.CheckFailure):
    def __init__(self, cog_name):
        super().__init__(f"{cog_name} is not loaded.")


def cog_loaded(cog_name: str):
    def pred(ctx):
        if ctx.bot.get_cog(cog_name):
            return True

        raise CogNotLoaded(cog_name)

    return commands.check(pred)


async def some_guilds(guilds: List[int]):
    def pred(ctx):
        return ctx.guild.id in guilds

    return commands.check(pred)
