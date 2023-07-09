import asyncio
from collections import defaultdict
from datetime import datetime

import discord
from discord.ext import commands


import discord_chan


FEATURE_NAME = "typing_watch"

class TypingWatch(commands.Cog, name="typing_watch"):
    def __init__(self, bot: discord_chan.DiscordChan) -> None:
        super().__init__()
        self.bot = bot
        # {channel_id: {user_id: task}}
        self.typing_watchers = defaultdict(lambda: dict())

    @commands.Cog.listener("on_typing")
    async def on_typing(
        self,
        channel: discord.TextChannel | discord.GroupChannel | discord.DMChannel,
        user: discord.Member | discord.User,
        when: datetime
    ):
        if not isinstance(channel, discord.TextChannel):
            # return if not in a guild
            return
        
        assert isinstance(user, discord.Member)

        if not await self.bot.is_feature_enabled(channel.guild.id, FEATURE_NAME):
            return

        if not self.typing_watchers[channel.id].get(user.id):
            self.typing_watchers[channel.id][user.id] = asyncio.create_task(self._typing_wait_task(user, channel))
        else:
            self.typing_watchers[channel.id][user.id].cancel()
            self.typing_watchers[channel.id][user.id] = asyncio.create_task(self._typing_wait_task(user, channel))

    async def _typing_wait_task(self, user: discord.Member, channel: discord.TextChannel):
        def _predicate(message: discord.Message):
            return message.author.id == user.id and message.channel.id == channel.id

        try:
            await self.bot.wait_for("message", check=_predicate, timeout=300)
        except asyncio.TimeoutError:
            # TODO: make this send an image showing them typing instead
            await channel.send(f"{user.display_name} typed without sending a message")
        else:
            del self.typing_watchers[channel.id][user.id]

    @commands.group(name="typing_watch", invoke_without_command=True, aliases=["tw"])
    @commands.guild_only()
    async def tw(self, ctx: commands.Context):
        # commands.guild_only prevents this
        assert ctx.guild is not None
        enabled = await self.bot.is_feature_enabled(ctx.guild.id, FEATURE_NAME)

        if enabled:
            return await ctx.send("Typing watch is enabled for this guild")
        else:
            return await ctx.send("Typing watch is not enabled for this guild")
        
    @tw.command()
    @discord_chan.checks.guild_owner()
    async def enable(self, ctx: discord_chan.SubContext):
        assert ctx.guild is not None
        await self.bot.set_feature_enabled(ctx.guild.id, FEATURE_NAME)
        await ctx.confirm("Typing watch enabled")

    @tw.command()
    @discord_chan.checks.guild_owner()
    async def disable(self, ctx: discord_chan.SubContext):
        assert ctx.guild is not None
        await self.bot.set_feature_disabled(ctx.guild.id, FEATURE_NAME)
        await ctx.confirm("Typing watch disabled")


async def setup(bot: discord_chan.DiscordChan):
    await bot.add_cog(TypingWatch(bot))
