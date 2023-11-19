import asyncio
from collections import defaultdict
from datetime import datetime

import discord
from discord.ext import commands

import discord_chan


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
        when: datetime,
    ):
        if not isinstance(channel, discord.TextChannel):
            # return if not in a guild
            return

        assert isinstance(user, discord.Member)

        if not await self.bot.feature_manager.is_enabled(
            discord_chan.Feature.typing_watch, channel.guild.id
        ):
            return

        if not self.typing_watchers[channel.id].get(user.id):
            self.typing_watchers[channel.id][user.id] = asyncio.create_task(
                self._typing_wait_task(user, channel)
            )
        else:
            self.typing_watchers[channel.id][user.id].cancel()
            self.typing_watchers[channel.id][user.id] = asyncio.create_task(
                self._typing_wait_task(user, channel)
            )

    async def _typing_wait_task(
        self, user: discord.Member, channel: discord.TextChannel
    ):
        def _predicate(message: discord.Message):
            return message.author.id == user.id and message.channel.id == channel.id

        try:
            await self.bot.wait_for("message", check=_predicate, timeout=300)
        except asyncio.TimeoutError:
            # TODO: make this send an image showing them typing instead
            await channel.send(f"{user.display_name} typed without sending a message")
        else:
            del self.typing_watchers[channel.id][user.id]


async def setup(bot: discord_chan.DiscordChan):
    await bot.add_cog(TypingWatch(bot))
