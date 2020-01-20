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

import argparse
import shlex
import typing
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from textwrap import shorten

import discord
import humanize
from discord_chan import EmbedDictPaginator, EmbedDictInterface
from discord.ext import commands

# Todo: move this to general to deal with help snipe conflict

class SnipeMode(Enum):
    edited  = 0
    deleted = 1
    purged  = 2

    def __str__(self):
        return self.name

class SnipeMsg:

    def __init__(self, message: discord.Message, mode: SnipeMode):
        self.mode = mode
        self.id = message.id
        self.time = datetime.utcnow()
        self.author = message.author
        self.content = message.content
        self.channel = message.channel

    @property
    def readable_time(self) -> str:
        return humanize.naturaltime(datetime.utcnow() - self.time)

    # TODO: replace this with equals f-string thing after switching to 3.8
    def __repr__(self):
        return f"<Snipe_msg author={self.author} channel={self.channel} time={self.time}>"

    def __str__(self):
        return f"[{self.mode}] {self.author} ({self.readable_time})"


def get_dict_from_snipes(snipes: typing.Iterable) -> dict:
    res = {}

    for snipe in snipes:
        res[str(snipe)] = shorten(snipe.content, 1_024, placeholder='...')  # Field value limit

    return res


class Snipe(commands.Cog, name='snipe'):
    """Snipe and related events"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snipe_dict: typing.Dict[int, deque] = defaultdict(lambda: deque())

    def attempt_add_snipe(self, message: discord.Message, mode: str):
        try:
            mode = SnipeMode[mode]
        except KeyError:
            raise ValueError(f'{mode} is not a valid snipe mode.')
        if message.content:
            snipe = SnipeMsg(message, mode)
            self.snipe_dict[message.channel.id].appendleft(snipe)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Saves deleted messages to snipe dict"""
        self.attempt_add_snipe(message, 'deleted')

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: [discord.Message]):
        """Saves bulk deleted messages to snipe dict"""
        for message in messages:
            self.attempt_add_snipe(message, 'purged')

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Saves edited messages to snipe dict"""
        if before.content != after.content:
            self.attempt_add_snipe(before, 'edited')

    async def get_snipes(self,
                         channel: discord.TextChannel,
                         member: discord.Member = None,
                         text: str = None
                         ):

        if member and text:
            channel_snipes = self.snipe_dict[channel.id]
            snipes = [s for s in channel_snipes if s.author == member and text in s.content]

        elif member:
            channel_snipes = self.snipe_dict[channel.id]
            snipes = [s for s in channel_snipes if s.author == member]

        else:
            snipes = self.snipe_dict[channel.id]

        return snipes

    # TODO: replace with snipe2 when it's working nicely
    @commands.group(name='snipe', invoke_without_command=True)
    async def snipe_command(self,
                            ctx: commands.Context,
                            index: typing.Optional[int] = 0,
                            channel: typing.Optional[discord.TextChannel] = None,
                            member: typing.Optional[discord.Member] = None,
                            *, text: str = None
                            ):
        """Snipe messages deleted/edited in a channel
        You can also search for a specific channel or/and author or/and text
        Ex:
        "snipe #general @starrfox hello" will find snipes from starrfox in general containing the text "hello"
        "snipe #general @starrfox" will find snipes from starrfox in general
        "snipe @starrfox" will find snipes from starrfox in current channel
        "snipe #general" will find snipes in general
        "snipe" with find snipes in the current channel
        """
        channel = channel or ctx.channel

        if not ctx.channel.is_nsfw() and channel.is_nsfw():
            return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel.")

        # TODO: possible fix needs testing
        if not channel.permissions_for(ctx.author).read_messages:
            return await ctx.send("You need permission to view a channel to snipe from it.")

        snipes = await self.get_snipes(channel, member, text)

        if not snipes:
            return await ctx.send("No snipes found.")

        try:
            snipe = snipes[index]
        except IndexError:
            return await ctx.send("Index out of bounds.")

        e = discord.Embed(title=str(snipe), description=snipe.content)

        # Todo: this is kinda bad? 0/0
        e.set_footer(text=f'{index}/{len(snipes) - 1}')

        return await ctx.send(embed=e)

    # noinspection PyTypeChecker
    @snipe_command.command(name='list')
    async def snipe_list(self,
                         ctx: commands.Context,
                         channel: typing.Optional[discord.TextChannel] = None,
                         member: typing.Optional[discord.Member] = None,
                         *, text: str = None
                         ):
        """list Sniped messages deleted/edited in a channel
        You can also search for a specific channel or/and author or/and text
        Ex:
        "snipe list #general @starrfox hello" will find snipes from starrfox in general containing the text "hello"
        "snipe list #general @starrfox" will find snipes from starrfox in general
        "snipe list @starrfox" will find snipes from starrfox in current channel
        "snipe list #general" will find snipes in general
        "snipe list" with find snipes in the current channel
        """
        channel = channel or ctx.channel

        if not ctx.channel.is_nsfw() and channel.is_nsfw():
            return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel.")

        # TODO: possible fix needs testing
        if not channel.permissions_for(ctx.author).read_messages:
            return await ctx.send("You need permission to view a channel to snipe from it.")

        snipes = await self.get_snipes(channel, member, text)

        if not snipes:
            return await ctx.send("No snipes found.")

        paginator = EmbedDictPaginator(max_fields=10)

        data = get_dict_from_snipes(snipes)

        paginator.add_fields(data)

        interface = EmbedDictInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)

    @commands.command()
    async def snipe2(self, ctx: commands.Context, *, options: str = ''):
        """
        Normal snipe but with command line arg parsing

        --users: List of user ids that authored the snipe
        --channel: Channel id to snipe from
        --before: Message id that snipes must be before
        --after: Message id that snipes must be after
        --start: The index to start at, defaults to 0
        --end: The index to end at, defaults to infinity
        --mode: Mode of the snipes (edited, deleted, purged)
        --contains: String that must be in the snipes
        """
        # Todo: see about switching to using discord-flags?
        parser = argparse.ArgumentParser(add_help=False)

        parser.add_argument('--users', nargs='+', type=int)
        parser.add_argument('--channel', default=ctx.channel.id, type=int)
        parser.add_argument('--before', type=int)
        parser.add_argument('--after', type=int)
        parser.add_argument('--start', default=0, type=int)
        parser.add_argument('--end', default=None, type=int)
        # parser.add_argument('--list', action='store_true') this would prob be a hassle to add
        # Todo: add server option to see all server snipes? make sure to check if they can view and nsfw
        # Todo: add back indexing behavior to see full messages? or take entire page for larger messages?
        # Todo: expanding on one per page, --per-page (large [over 1,024], all)
        # Todo: --diff arg using diff lib
        parser.add_argument('--mode', choices=['deleted', 'purged', 'edited'])
        parser.add_argument('--contains', nargs='+')

        try:
            args = parser.parse_args(shlex.split(options))
        except Exception as e:
            return await ctx.send(str(e))

        channel = ctx.guild.get_channel(args.channel)

        if channel is None:
            return await ctx.send('Channel not found.')

        if not ctx.channel.is_nsfw() and channel.is_nsfw():
            return await ctx.send('You cannot snipe a nsfw channel from a non-nsfw channel.')

        if not channel.permissions_for(ctx.author).read_messages:
            return await ctx.send('You need permission to view a channel to snipe from it.')

        try:
            snipes = self.snipe_dict[channel.id][args.start:args.end]
        except IndexError:
            return await ctx.send('No snipes found for this search.')

        # Todo: put this in a get_filters function or something (70 lined function atm)
        filters = []

        if args.users:
            filters.append(lambda snipe: snipe.author.id in args.users)

        # Todo: test if before and after work and intended
        if args.before:
            filters.append(lambda snipe: snipe.id < args.before)

        if args.after:
            filters.append(lambda snipe: snipe.id > args.after)

        if args.mode:
            mode = SnipeMode[args.mode]
            filters.append(lambda snipe: snipe.mode == mode)

        if args.contains:
            to_match = ' '.join(args.contains)
            filters.append(lambda snipe: to_match in snipe.content)

        for _filter in filters:
            snipes = list(filter(_filter, snipes))

        if not snipes:
            return await ctx.send("No snipes found for this search.")

        paginator = EmbedDictPaginator(max_fields=10)

        data = get_dict_from_snipes(snipes)

        paginator.add_fields(data)

        interface = EmbedDictInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)


def setup(bot):
    bot.add_cog(Snipe(bot))
