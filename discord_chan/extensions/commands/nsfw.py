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

from aiohttp import ClientSession as session
from discord.ext import commands

NEKO_URL = "https://nekos.life/api/v2/img/lewd"


class Nsfw(commands.Cog, name="nsfw"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_check(self, ctx: commands.Context):
        if ctx.channel.is_nsfw():
            return True

        raise commands.NSFWChannelRequired(ctx.channel)

    @commands.cooldown(10, 60, commands.BucketType.user)
    @commands.command()
    async def neko(self, ctx: commands.Context):
        """Get a random lewd neko"""
        async with session() as sess:
            async with sess.get(NEKO_URL) as res:
                url = (await res.json())["url"]
                await ctx.send(url)


def setup(bot: commands.Bot):
    bot.add_cog(Nsfw(bot))
