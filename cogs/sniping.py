import discord
from discord.ext import commands

import asyncio
import typing
from datetime import datetime

from extras.paginator import paginator

class snipe_msg:

    def __init__(self, message):
        self.content = message.content
        self.author = message.author
        self.time = message.created_at
        self.channel = message.channel

    def __repr__(self):
        return f"<snipe_msg author={self.author} channel={self.channel} time={self.time}>"

class sniping(commands.Cog):
    """Snipe and related events"""

    def __init__(self, bot):
        self.bot = bot
        self.snipe_dict = {} #Channel_id: list of snipe_msg

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        """Saves deleted messages to snipe dict"""
        if not msg.content or msg.author.bot:
            return
        if not msg.channel.id in self.snipe_dict:
            self.snipe_dict[msg.channel.id] = []
        snipe_obj = snipe_msg(msg)
        snipe_obj.time = datetime.utcnow()
        self.snipe_dict[msg.channel.id].insert(0, snipe_obj)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Saves edited messages to snipe dict"""
        if not before.content != after.content or not before.content or before.author.bot:
            return
        if not before.channel.id in self.snipe_dict:
            self.snipe_dict[before.channel.id] = []
        snipe_obj = snipe_msg(before)
        snipe_obj.time = datetime.utcnow()
        self.snipe_dict[before.channel.id].insert(0, snipe_obj)

    @commands.group(name='snipe', invoke_without_command=True)
    async def snipe_command(self, ctx, index: typing.Optional[int] = 0, *searches: typing.Optional[typing.Union[discord.Member, discord.TextChannel]]):
        """Snipe messages deleted/edited in a channel
        You can also search for a specific channel or/and author
        Ex:
        snipe @starrfox #general will find snipes from starrfox in general
        snipe @starrfox will find snipes from starrfox
        snipe #general will find snipes in general
        """
        if index < 0:
            return await ctx.send("Positive indexes only")
        author = None
        channel = None
        for i in searches:
            if isinstance(i, discord.Member):
                author = i
            elif isinstance(i, discord.TextChannel):
                channel = i
        if channel is None and author is None:
            channel = ctx.channel
        if channel:
            if ctx.channel.is_nsfw() is False and channel.is_nsfw() is True:
                return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel")
            if not channel.id in self.snipe_dict:
                return await ctx.send("This channel has no recorded messages")
            if len(self.snipe_dict[channel.id])-1 < index:
                return await ctx.send("No snipes found or index too large")
        if author and channel:
            msgs = []
            for i in self.snipe_dict[channel.id]:
                if i.author == author:
                    msgs.append(i)
            if len(msgs) == 0 or len(msgs)-1 < index:
                return await ctx.send("No snipes found or index too large")
            msg = msgs[index]
        elif author:
            snipes = []
            for i in self.snipe_dict.values():
                snipes.append(i[0])
            msgs = []
            for i in snipes:
                if i.author == author:
                    msgs.append(i)
            if len(msgs) == 0 or len(msgs)-1 < index:
                return await ctx.send("No snipes found or index too large")
            msg = msgs[index]
        elif channel:
            msg = self.snipe_dict[channel.id][index]
        e = discord.Embed(
            color=discord.Color.blurple(),
            description=msg.content,
            timestamp=msg.time
        )
        e.set_author(
            name=msg.author.name,
            icon_url=msg.author.avatar_url
        )
        e.set_footer(
            text=f"{msgs.index(msg)}/{len(msgs)-1}"
        )
        await ctx.send(embed=e)

    @snipe_command.command(name='list')
    async def snipe_list(self, ctx, *searches: typing.Optional[typing.Union[discord.Member, discord.TextChannel]]):
        """list Sniped messages deleted/edited in a channel
        You can also search for a specific channel or/and author
        Ex:
        snipe list @starrfox #general will find all snipes from starrfox in general
        snipe list @starrfox will find all snipes from starrfox
        snipe list #general will find all snipes in general
        """
        author = None
        channel = None
        for i in searches:
            if isinstance(i, discord.Member):
                author = i
            elif isinstance(i, discord.TextChannel):
                channel = i
        if channel is None and author is None:
            channel = ctx.channel
        if channel:
            if ctx.channel.is_nsfw() is False and channel.is_nsfw() is True:
                return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel")
            if not channel.id in self.snipe_dict:
                return await ctx.send("Channel has no recorded messages")
        if author and channel:
            msgs = []
            for i in self.snipe_dict[channel.id]:
                if i.author == author:
                    msgs.append(i)
        elif author:
            snipes = []
            for i in self.snipe_dict.values():
                snipes.append(i[0])
            msgs = []
            for i in snipes:
                if i.author == author:
                    msgs.append(i)
        elif channel:
            msgs = self.snipe_dict[channel.id]
        if len(msgs) == 0:
            return await ctx.send("No snipes found")
        pager = paginator(self.bot)
        e = discord.Embed(color=discord.Color.blurple())
        Set = 1
        for msg in msgs:
            if len(e.fields) >= 5:
                pager.add_page(data=e)
                e = discord.Embed(color=discord.Color.blurple())
            else:
                e.add_field(
                    name=f"**{msg.author.display_name}** said in **#{msg.channel.name}**",
                    value=msg.content[:100],
                    inline=False
                )
        pager.add_page(data=e)
        await pager.do_paginator(ctx)

def setup(bot):
    bot.add_cog(sniping(bot))
