import random

import discord
from discord.ext import commands

import discord_chan

BIG_COPE = 301790265725943808
COPE_MAX = 100


class Cope(commands.Cog, name="cope"):
    def __init__(self, bot: discord_chan.DiscordChan) -> None:
        super().__init__()
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild is None:
            return

        if not await self.bot.feature_manager.is_enabled(
            discord_chan.Feature.cope, message.guild.id
        ):
            return

        if message.author.id == BIG_COPE:
            range = COPE_MAX // 2
        else:
            range = COPE_MAX

        num = random.randrange(0, range)
        if num == 1:
            return await message.channel.send("cope")


async def setup(bot: discord_chan.DiscordChan):
    await bot.add_cog(Cope(bot))
