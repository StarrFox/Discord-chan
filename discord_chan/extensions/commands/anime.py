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

import asyncio
import datetime
import logging
from calendar import day_name, day_abbr
from textwrap import shorten

import discord
from discord.ext import commands

try:
    from jikanpy import AioJikan
except ImportError:
    AioJikan = False

days = map(str.lower, list(day_name) + list(day_abbr))

logger = logging.getLogger(__name__)

class Weekday(commands.Converter):

    async def convert(self, ctx, argument):
        # Todo: 3.8 switch to walrus
        converted = str(argument).lower()
        if converted in days:
            return converted

        raise commands.BadArgument(f"{argument} is not a valid weekday.")

class Anime(commands.Cog, name='anime'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.jikan = AioJikan()
        self.anime_db = {}
        self.db_update_task = bot.loop.create_task(self.get_anime_db())

    def cog_unload(self):
        self.db_update_task.cancel()

    # Not using tasks ext because 7 days isn't always next monday
    async def get_anime_db(self):
        """
        Updates self.anime_db with fresh info
        """
        try:
            self.anime_db = await self.jikan.schedule()

            now = datetime.datetime.utcnow()
            next_monday = datetime.timedelta(
                days=(7 - now.weekday())
            )

            await asyncio.sleep(next_monday.total_seconds())

        except asyncio.CancelledError:
            pass

    @commands.group(name='anime', invoke_without_command=True)
    async def anime_command(self, ctx: commands.Context):
        """
        Base anime command
        """
        await ctx.send_help('anime')

    @anime_command.command()
    async def airing(self, ctx: commands.Context, day: Weekday = None):
        """
        View anime airing for a given weekday
        defaults to today
        """
        if day is None:
            now = datetime.datetime.utcnow()
            day = now.strftime("%A").lower()

        titles = [i['title'] for i in self.anime_db[day]]

        await ctx.send('\n'.join(titles))

    @staticmethod
    def anime_embed(data: dict):
        """
        Makes an embed from anime info
        """
        # Todo: should this be a paginator for long synopsises?
        embed = discord.Embed(
            title=data['title'],
            url=data['url'],
            description=shorten(data['synopsis'], 2_048, placeholder='...')  # description limit
        )

        embed.set_image(url=data['image_url'])

        embed.add_field(name='aired', value=data['aired']['string'])

        def field_from_key(key: str):
            embed.add_field(name=key, value=data[key])

        keys = [
            'episodes',
            'score',
            'duration',
            'rating',
            'rank',
        ]

        for i in keys:
            field_from_key(i)

        return embed

    @anime_command.command(name='info')
    async def anime_info(self, ctx: commands.Context, *, anime_name: str):
        """
        View info about an anime
        """
        # Todo: replace this with discord.ext.menus when released
        search = await self.jikan.search('anime', anime_name)
        results = search['results']

        msg = '\n'.join([f"{idx+1}. {i['title']}" for idx, i in enumerate(results[:5])])

        e = discord.Embed(
            description=msg
        )

        embed_message = await ctx.send(embed=e)

        reactions = [f"{i}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}" for i in range(1, 6)]

        for reaction in reactions:
            await embed_message.add_reaction(reaction)

        def check(r, u):
            return all([
                str(r) in reactions,
                u == ctx.author,
                r.message.id == embed_message.id  # messages still don't have __eq__ for some reason
            ])

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=check, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send('Timed out.')

        anime_id = results[reactions.index(str(reaction))]['mal_id']

        result = await self.jikan.anime(anime_id)

        try:
            await embed_message.clear_reactions()
        except discord.Forbidden:
            pass

        await embed_message.edit(embed=self.anime_embed(result))

def setup(bot):
    if AioJikan:
        bot.add_cog(Anime(bot))
    else:
        logger.warning('Jikan is not installed, Anime cog will not be loaded.')
