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

import discord
from discord.ext import commands

from discord_chan import (BetweenConverter, MaxLengthConverter, BotConverter,
                          db, SubContext, EmbedFieldProxy,
                          EmbedFieldsPageSource, DCMenuPages)

STAR = '\N{WHITE MEDIUM STAR}'
ZERO = '0\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}'


class Ratings(commands.Cog, name='ratings'):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Todo: move these to bot class after working, or maybe db file??
    @staticmethod
    async def set_bot_rating(bot_id, user_id, rating, review):
        async with db.get_database() as connection:
            await connection.execute(
                'INSERT OR REPLACE INTO ratings (bot_id, user_id, rating, review) VALUES (?, ?, ?, ?);',
                (bot_id, user_id, rating, review)
            )

            await connection.commit()

    @staticmethod
    async def clear_bot_rating(bot_id, user_id):
        async with db.get_database() as connection:
            await connection.execute(
                'DELETE FROM ratings WHERE bot_id = (?) AND user_id = (?);',
                (bot_id, user_id)
            )

            await connection.commit()

    @staticmethod
    async def get_bot_rating(bot_id, user_id):
        async with db.get_database() as connection:
            cursor = await connection.execute(
                'SELECT rating, review FROM ratings WHERE bot_id = (?) AND user_id = (?);',
                (bot_id, user_id)
            )

            res = await cursor.fetchone()

            if res:
                return res

    @staticmethod
    async def get_bot_ratings(bot_id):
        async with db.get_database() as connection:
            cursor = await connection.execute(
                'SELECT user_id, rating, review FROM ratings WHERE bot_id = (?)',
                (bot_id,)
            )

            return await cursor.fetchall()

    # Todo: leave this

    @staticmethod
    def format_rating(user: discord.User, rating: int, review: str = None) -> EmbedFieldProxy:
        """
        Name: user#discrm
        Rating: <number of stars>

        <review>
        """
        name = str(user)

        if rating > 0:
            value = STAR * rating
        else:
            value = ZERO

        if review:
            value += '\n\n' + review

        return EmbedFieldProxy(name, value)

    @commands.command()
    async def rate(self,
                   ctx: SubContext,
                   bot: BotConverter(),
                   rating: BetweenConverter(0, 5),
                   *, review: MaxLengthConverter(300)
                   ):
        """
        Give a bot a rating 0-5 and an optional review.
        Reviews must be no more than 300 characters.

        Rating an already rated bot will replace your previous rating.
        """
        await self.set_bot_rating(bot.id, ctx.author.id, rating, review)

        await ctx.confirm('Bot rated.')

    @commands.command(name='clear-rating')
    async def clear_rating(self, ctx: SubContext, bot: BotConverter()):
        """
        Remove your rating for a bot.
        """
        await self.clear_bot_rating(bot.id, ctx.author.id)

        await ctx.confirm('Rating cleared.')

    @commands.command(aliases=['view'])
    async def show(self, ctx, *, bot: BotConverter()):
        """
        Show the ratings of a bot.
        """
        ratings = await self.get_bot_ratings(bot.id)

        if not ratings:
            return await ctx.send('No ratings for this bot.')

        title = f'Ratings for {bot}'

        average_holder = []
        entries = []

        for user_id, rating, review in ratings:
            user = ctx.bot.get_user(user_id)
            if not user:
                await self.clear_bot_rating(bot.id, user_id)
                continue

            entries.append(self.format_rating(user, rating, review))
            average_holder.append(rating)

        average = round(sum(average_holder) / len(average_holder), 2)

        description = f'Average: {average}'

        source = EmbedFieldsPageSource(entries, per_page=3,  title=title, description=description)

        menu = DCMenuPages(source)

        await menu.start(ctx)


def setup(bot: commands.Bot):
    bot.add_cog(Ratings(bot))
