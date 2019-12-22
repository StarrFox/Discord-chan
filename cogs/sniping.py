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

import typing
from collections import defaultdict
from datetime import datetime

import discord
import humanize
from bot_stuff import EmbedDictPaginator, EmbedDictInterface
from discord.ext import commands


class snipe_msg:

    def __init__(self, message: discord.Message, mode: str):
        self.content = message.content
        self.author = message.author
        self.time = datetime.now()
        self.channel = message.channel
        self.mode = mode

    @property
    def readable_time(self):
        return humanize.naturaltime(datetime.now() - self.time)

    # TODO: replace this with equals f-string thing after switching to 3.8
    def __repr__(self):
        return f"<Snipe_msg author={self.author} channel={self.channel} time={self.time}>"

    def __str__(self):
        return f"[{self.mode}] {self.author} ({self.readable_time})"


def get_dict_from_snipes(snipes: list):
    res = {}

    for snipe in snipes:
        res[str(snipe)] = snipe.content[:1_024]  # Field value limit

    return res


class sniping(commands.Cog):
    """Snipe and related events"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snipe_dict = defaultdict(lambda: [])

    def attempt_add_snipe(self, message: discord.Message, mode: str):
        if message.content:
            snipe = snipe_msg(message, mode)
            self.snipe_dict[message.channel.id].insert(0, snipe)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Saves deleted messages to snipe dict"""
        self.attempt_add_snipe(message, 'Deleted')

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: [discord.Message]):
        """Saves bulk deleted messages to snipe dict"""
        for message in messages:
            self.attempt_add_snipe(message, 'Purged')

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Saves edited messages to snipe dict"""
        if before.content != after.content:
            self.attempt_add_snipe(before, 'Edited')

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

    # TODO: only allow snipes for channels they can see
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
        if not channel.permissions_for(ctx.author).read_messages():
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

        snipes = await self.get_snipes(channel, member, text)

        if not snipes:
            return await ctx.send("No snipes found.")

        paginator = EmbedDictPaginator(max_fields=10)

        data = get_dict_from_snipes(snipes)

        paginator.add_fields(data)

        interface = EmbedDictInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)


def setup(bot):
    bot.add_cog(sniping(bot))
