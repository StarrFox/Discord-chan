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

import discord
from discord.ext import commands

import discord_chan
from discord_chan import DiscordChan, checks


THICK_TABLE = str.maketrans(
    {
        "a": "卂",
        "b": "乃",
        "c": "匚",
        "d": "刀",
        "e": "乇",
        "f": "下",
        "g": "厶",
        "h": "卄",
        "i": "工",
        "j": "丁",
        "k": "长",
        "l": "乚",
        "m": "从",
        "n": "𠘨",
        "o": "口",
        "p": "尸",
        "q": "㔿",
        "r": "尺",
        "s": "丂",
        "t": "丅",
        "u": "凵",
        "v": "リ",
        "w": "山",
        "x": "乂",
        "y": "丫",
        "z": "乙",
        " ": "   ",
    }
)


class Anime(commands.Cog, name="anime"):
    def __init__(self, bot: DiscordChan):
        self.bot = bot

    @commands.command()
    async def thickify(self, ctx: commands.Context, *, message: str):
        """
        thickify text
        """
        await ctx.send(message.lower().translate(THICK_TABLE))

    @commands.command(aliases=["sb"])
    @checks.some_guilds([724060352010125412])
    @commands.is_nsfw()
    async def safebooru(self, ctx: commands.Context, *tags: str):
        if image_url := await discord_chan.get_random_safebooru_post(list(tags)):
            embed = discord.Embed(description="\u200b")
            embed.set_image(url=image_url)
            await ctx.send(embed=embed)
        else:
            await ctx.deny("No posts found")


async def setup(bot):
    await bot.add_cog(Anime(bot))
