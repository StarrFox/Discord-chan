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
from PIL.Image import Image

from . import utils
from .image import url_to_image, FileTooLarge, InvalidImageType

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

    async def convert(self, ctx: commands.Context, argument: str) -> discord.TextChannel:
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

        raise commands.BadArgument('That is not a bot.')


class ImageUrlConverter(commands.Converter):
    """
    Attempts to convert an argument to an image url in the following order
    1. Member -> str(.avatar_url_as(static_format=png))
    2. Emoji -> str(.url)
    3. Url regex
    """

    def __init__(self, force_format: str = None):
        self.force_format = force_format

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        try:
            member = await commands.MemberConverter().convert(ctx, argument)

        except commands.BadArgument:
            member = None

        if member:
            if not self.force_format:
                return str(member.avatar_url_as(static_format='png'))

            else:
                return str(member.avatar_url_as(format=self.force_format))

        try:
            emoji = await commands.PartialEmojiConverter().convert(ctx, argument)

        except commands.BadArgument:
            emoji = None

        if emoji:
            if not self.force_format:
                return str(emoji.url)

            else:
                return f'https://cdn.discordapp.com/emojis/{emoji.id}.{self.force_format}'

        url_regex = re.fullmatch(utils.link_regex, argument)

        if url_regex:
            return url_regex.string

        raise commands.BadArgument('"{}" is not a member, custom emoji, or url.'.format(argument))


class ImageUrlDefault(commands.CustomDefault, display='LastImage'):

    async def default(self, ctx: commands.Context, param: str) -> str:
        if ctx.message.attachments:
            return ctx.message.attachments[0].url

        async for message in await ctx.history():
            if message.attachments:
                return message.attachments[0].url

        raise commands.MissingRequiredArgument(param)


class ImageConverter(ImageUrlConverter):

    async def convert(self, ctx: commands.Context, argument: str) -> Image:
        url = await super().convert(ctx, argument)

        try:
            return await url_to_image(url)

        except FileTooLarge as e:
            raise commands.BadArgument(str(e))

        except InvalidImageType as e:
            raise commands.BadArgument(str(e))


class ImageDefault(ImageUrlDefault):

    async def default(self, ctx: commands.Context, param: str) -> Image:
        url = await super().default(ctx, param)

        try:
            return await url_to_image(url)

        except (FileTooLarge, InvalidImageType):
            raise commands.MissingRequiredArgument(param)
