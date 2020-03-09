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

import re
from calendar import day_name, day_abbr

import discord
from discord.ext import commands

DAYS = map(str.lower, list(day_name) + list(day_abbr))


def _get_from_guilds(bot, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result


class ImageFormatConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if argument in ('png', 'gif', 'jpeg', 'webp'):
            return argument
        else:
            raise commands.BadArgument('{} is not a valid image format.'.format(argument))


class BetweenConverter(commands.Converter):

    def __init__(self, num1: int, num2: int):
        self.num1 = num1
        self.num2 = num2

    async def convert(self, ctx: commands.Context, argument: str) -> int:
        try:
            argument = int(argument)
        except ValueError:
            raise commands.BadArgument('{} is not a valid number.'.format(argument))
        if self.num1 <= argument <= self.num2:
            return argument

        raise commands.BadArgument('{} is not between {} and {}'.format(argument, self.num1, self.num2))


class MaxLengthConverter(commands.Converter):

    def __init__(self, max_size: int = 2000):
        self.max_size = max_size

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        if len(argument) <= self.max_size:
            return argument

        raise commands.BadArgument('Argument over max size of {}'.format(self.max_size))


class WeekdayConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        # Todo: 3.8 switch to walrus
        converted = str(argument).lower()
        if converted in DAYS:
            return converted

        raise commands.BadArgument("{} is not a valid weekday.".format(argument))


class CrossGuildTextChannelConverter(commands.TextChannelConverter):
    """
    Makes the DM behavior the default
    """

    async def convert(self, ctx, argument):
        bot = ctx.bot

        match = self._get_id_match(argument) or re.match(r'<#([0-9]+)>$', argument)

        if match is None:
            # not a mention
            def check(c):
                return isinstance(c, discord.TextChannel) and c.name == argument

            result = discord.utils.find(check, bot.get_all_channels())

        else:
            channel_id = int(match.group(1))

            result = _get_from_guilds(bot, 'get_channel', channel_id)

        if not isinstance(result, discord.TextChannel):
            raise commands.BadArgument('Channel "{}" not found.'.format(argument))

        return result


class BotConverter(commands.Converter):

    async def convert(self, ctx: commands.Context, argument: str) -> discord.Member:
        member = await commands.MemberConverter().convert(ctx, argument)

        if member.bot:
            return member

        raise commands.BadArgument('{} is not a bot.'.format(argument))
