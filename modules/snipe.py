import discord
from discord.ext import commands
import asyncio
import typing
from extras.paginator import paginator

class snipe:
    """Snipe and related events"""

    def __init__(self, bot):
        self.bot = bot
        self.snipe_dict = {}

    async def on_message_delete(self, msg):
        """Saves deleted messages to snipe dict"""
        if not msg.content:
            return
        if not msg.channel.id in self.snipe_dict:
            self.snipe_dict[msg.channel.id] = []
        self.snipe_dict[msg.channel.id].insert(0, msg)

    async def on_message_edit(self, before, after):
        """Saves edited messages to snipe dict"""
        checks = [
            before.content == after.content,
            before.embeds != after.embeds and before.content == after.content,
            not after.content,
            before.pinned != after.pinned
        ]
        if any(checks):
            return
        if not before.channel.id in self.snipe_dict:
            self.snipe_dict[before.channel.id] = []
        self.snipe_dict[before.channel.id].insert(0, before)

    @commands.group(name='snipe', invoke_without_command=True)
    async def _snipe(self, ctx, channel: typing.Optional[discord.TextChannel] = None, index: int = 0):
        """Snipe messages deleted/edited in a channel"""
        if index < 0:
            return await ctx.send("Positive numbers only")
        if not channel:
            channel = ctx.channel
        if ctx.channel.is_nsfw() is False and channel.is_nsfw() is True:
            return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel")
        if not channel.id in self.snipe_dict:
            return await ctx.send("This channel has no recorded messages")
        if len(self.snipe_dict[channel.id])-1 < index:
            return await ctx.send("I don't have that many messages recorded")
        msg = self.snipe_dict[channel.id][index]
        e = discord.Embed(
            color=discord.Color.blurple(),
            description=msg.content
        )
        e.set_author(
            name=msg.author.name,
            icon_url=msg.author.avatar_url
        )
        e.set_footer(
            text=f"{index}/{len(self.snipe_dict[channel.id])-1}"
        )
        await ctx.send(embed=e)

    @_snipe.command(name='list')
    async def _list(self, ctx, channel: discord.TextChannel = None):
        """List deleted/edited messages for a channel"""
        if not channel:
            channel = ctx.channel
        if ctx.channel.is_nsfw() is False and channel.is_nsfw() is True:
            return await ctx.send("You cannot snipe a nsfw channel from a non-nsfw channel")
        if not channel.id in self.snipe_dict:
            return await ctx.send("This channel has no recorded messages")
        pager = paginator(self.bot)
        e = discord.Embed(color=discord.Color.blurple())
        Set = 1
        for msg in self.snipe_dict[channel.id]:
            if len(e.fields) >= 5:
                e.set_footer(text=f"{Set*5-4}-{Set*5}/{len(self.snipe_dict[channel.id])-1}")
                Set += 1
                pager.add_page(data=e)
                e = discord.Embed(color=discord.Color.blurple())
            else:
                e.add_field(
                    name=f"**{msg.author.display_name}** said in **#{msg.channel.name}**",
                    value=msg.content[:100],
                    inline=False
                )
        e.set_footer(text=f"{Set*5-4}-{Set*5}/{len(self.snipe_dict[channel.id])-1}")
        pager.add_page(data=e)
        await pager.do_paginator(ctx)

def setup(bot):
    bot.add_cog(snipe(bot))