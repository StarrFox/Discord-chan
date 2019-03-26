import discord
from discord.ext import commands
import asyncio
import typing
from extras.paginator import paginator

class snipe(commands.Cog):
    """Snipe and related events"""

    def __init__(self, bot):
        self.bot = bot
        self.snipe_dict = {} #Channel_id: list of discord.Message

    @commands.Cog.listener()
    async def on_message_delete(self, msg):
        """Saves deleted messages to snipe dict"""
        if not msg.content or msg.author.bot:
            return
        if not msg.channel.id in self.snipe_dict:
            self.snipe_dict[msg.channel.id] = []
        self.snipe_dict[msg.channel.id].insert(0, msg)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Saves edited messages to snipe dict"""
        if not before.content != after.content or not before.content:
            return
        if not before.channel.id in self.snipe_dict:
            self.snipe_dict[before.channel.id] = []
        self.snipe_dict[before.channel.id].insert(0, before)

    @commands.group(name='snipe', invoke_without_command=True)
    async def snipe_command(self, ctx, channel: typing.Optional[discord.TextChannel] = None, index: int = 0):
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
            description=msg.content,
            timestamp=msg.created_at
        )
        e.set_author(
            name=msg.author.name,
            icon_url=msg.author.avatar_url
        )
        e.set_footer(
            text=f"{index}/{len(self.snipe_dict[channel.id])-1}"
        )
        await ctx.send(embed=e)

    @snipe_command.command(name='list')
    async def snipe_list(self, ctx, channel: discord.TextChannel = None):
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
    bot.add_cog(snipe(bot))
