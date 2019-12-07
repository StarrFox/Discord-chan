import typing
from datetime import datetime

import discord
import humanize
from bot_stuff.paginators import EmbedDictPaginator, EmbedDictInterface
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

    def __repr__(self):
        return f"<Snipe_msg author={self.author} channel={self.channel} time={self.time}>"

    def __str__(self):
        return f"{self.mode} by {self.author} ({self.readable_time})"

class sniping(commands.Cog):
    """Snipe and related events"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snipe_dict = {} #Channel_id: list of snipe_msg

    @commands.Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        """Saves deleted messages to snipe dict"""
        if not msg.content:
            return
        if not msg.channel.id in self.snipe_dict:
            self.snipe_dict[msg.channel.id] = []
        snipe_obj = snipe_msg(msg, 'Deleted')
        self.snipe_dict[msg.channel.id].insert(0, snipe_obj)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Saves edited messages to snipe dict"""
        if not before.content != after.content or not before.content:
            return
        if not before.channel.id in self.snipe_dict:
            self.snipe_dict[before.channel.id] = []
        snipe_obj = snipe_msg(before, 'Edited')
        self.snipe_dict[before.channel.id].insert(0, snipe_obj)

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

        if not channel.id in self.snipe_dict:
            return await ctx.send("No snipes found.")

        if member and text:
            channel_snipes = self.snipe_dict[channel.id]
            snipes = [s for s in channel_snipes if s.author == member and text in s.content]
        elif member:
            channel_snipes = self.snipe_dict[channel.id]
            snipes = [s for s in channel_snipes if s.author == member]
        else:
            snipes = self.snipe_dict[channel.id]

        if not snipes:
            return await ctx.send("No snipes found.")

        try:
            snipe = snipes[index]
        except IndexError:
            return await ctx.send("Index out of bounds.")

        e = discord.Embed(title=str(snipe), description=snipe.content)

        return await ctx.send(embed = e)

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

        if not channel.id in self.snipe_dict:
            return await ctx.send("No snipes found.")

        if member and text:
            channel_snipes = self.snipe_dict[channel.id]
            snipes = [s for s in channel_snipes if s.author == member and text in s.content]
        elif member:
            channel_snipes = self.snipe_dict[channel.id]
            snipes = [s for s in channel_snipes if s.author == member]
        else:
            snipes = self.snipe_dict[channel.id]

        if not snipes:
            return await ctx.send("No snipes found.")

        paginator = EmbedDictPaginator(max_fields=10)

        data = self.get_dict_from_snipes(snipes)

        paginator.add_fields(data)

        interface = EmbedDictInterface(self.bot, paginator, owner=ctx.author)

        await interface.send_to(ctx)

    def get_dict_from_snipes(self, snipes: list):
        res = {}

        for snipe in snipes:
            res[str(snipe)] = snipe.content[:1_024] # Field value limit

        return res

def setup(bot):
    bot.add_cog(sniping(bot))
