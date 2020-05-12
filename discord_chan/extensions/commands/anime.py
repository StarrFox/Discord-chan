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

import asyncio
import datetime
from contextlib import suppress
from textwrap import shorten

import discord
from discord.ext import commands

from discord_chan import DiscordChan, WeekdayConverter, checks

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

    @commands.group(name="anime", invoke_without_command=True)
    async def anime_command(self, ctx: commands.Context):
        """
        Base anime command
        """
        await ctx.send_help("anime")

    @checks.cog_loaded("events")
    @anime_command.command()
    async def airing(self, ctx: commands.Context, day: WeekdayConverter = None):
        """
        View anime airing for a given weekday
        defaults to today
        """
        if day is None:
            now = datetime.datetime.utcnow()
            day = now.strftime("%A").lower()

        titles = [i["title"] for i in self.bot.anime_db[day]]

        await ctx.send("\n".join(titles))

    @staticmethod
    def anime_embed(data: dict):
        """
        Makes an embed from anime info
        """
        embed = discord.Embed(
            title=data["title"],
            url=data["url"],
            # 2,048 is the description limit
            description=shorten(data["synopsis"], 2_048, placeholder="...")
            if data["synopsis"]
            else "No synopsis.",
        )

        embed.set_image(url=data["image_url"])

        embed.add_field(name="aired", value=data["aired"]["string"])

        def field_from_key(key: str):
            embed.add_field(name=key, value=data[key])

        keys = [
            "episodes",
            "score",
            "duration",
            "rating",
            "rank",
        ]

        for i in keys:
            field_from_key(i)

        return embed

    @anime_command.command(name="info")
    async def anime_info(self, ctx: commands.Context, *, anime_name: str):
        """
        View info about an anime
        """
        # Todo: replace this with discord.ext.menus when released
        search = await self.bot.jikan.search("anime", anime_name)
        results = search["results"]

        msg = "\n".join(
            [f"{idx + 1}. {i['title']}" for idx, i in enumerate(results[:5])]
        )

        e = discord.Embed(description=msg)

        embed_message = await ctx.send(embed=e)

        reactions = [
            f"{i}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}"
            for i in range(1, 6)
        ]

        for reaction in reactions:
            await embed_message.add_reaction(reaction)

        def check(r, u):
            return all(
                [
                    str(r) in reactions,
                    u == ctx.author,
                    r.message.id
                    == embed_message.id,  # messages still don't have __eq__ for some reason
                ]
            )

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", check=check, timeout=60
            )
        except asyncio.TimeoutError:
            return await ctx.send("Timed out.")

        anime_id = results[reactions.index(str(reaction))]["mal_id"]

        result = await self.bot.jikan.anime(anime_id)

        with suppress(discord.Forbidden):
            await embed_message.clear_reactions()

        await embed_message.edit(embed=self.anime_embed(result))


def setup(bot):
    bot.add_cog(Anime(bot))
