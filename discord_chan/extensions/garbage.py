import re

import discord
from discord.ext import commands

import discord_chan


loli_filter = re.compile(r"\?tags=(\w|\+)*loli([^a-zA-Z]|$)?")


class Garbage(commands.Cog):
    def __init__(self, bot: discord_chan.DiscordChan) -> None:
        super().__init__()
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def block_olaf_lolis(self, message: discord.Message):
        if message.guild is None:
            return

        # wizspoil
        if message.guild.id != 1015677559020724264:
            return

        # anti-olaf
        if len(list(loli_filter.finditer(message.content))) > 0:
            return await message.delete()


async def setup(bot: discord_chan.DiscordChan):
    await bot.add_cog(Garbage(bot))
