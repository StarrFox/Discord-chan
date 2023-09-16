import random

import discord
from discord.ext import commands

import discord_chan


FEATURE_NAME = "cope"


BIG_COPE = 301790265725943808
COPE_MAX = 100


class Cope(commands.Cog, name="cope"):
    def __init__(self, bot: discord_chan.DiscordChan) -> None:
        super().__init__()
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_message(
        self,
        message: discord.Message
    ):
        if message.guild is None:
            return

        if not await self.bot.is_feature_enabled(message.guild.id, FEATURE_NAME):
            return

        if message.author.id == BIG_COPE:
            range = COPE_MAX // 2
        else:
            range = COPE_MAX

        num = random.randrange(0, range)
        if num == 1:
            return await message.channel.send("Cope")

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def cope(self, ctx: commands.Context):
        # commands.guild_only prevents this
        assert ctx.guild is not None
        enabled = await self.bot.is_feature_enabled(ctx.guild.id, FEATURE_NAME)

        if enabled:
            return await ctx.send("Cope is enabled for this guild")
        else:
            return await ctx.send("Cope is not enabled for this guild")

    @cope.command()
    @discord_chan.checks.guild_owner()
    async def toggle(self, ctx: discord_chan.SubContext):
        """Toggle coping"""
        assert ctx.guild is not None

        if await self.bot.is_feature_enabled(ctx.guild.id, FEATURE_NAME):
            await self.bot.set_feature_disabled(ctx.guild.id, FEATURE_NAME)
            return await ctx.confirm("Cope disabled")

        await self.bot.set_feature_enabled(ctx.guild.id, FEATURE_NAME)
        return await ctx.confirm("Cope enabled")


async def setup(bot: discord_chan.DiscordChan):
    await bot.add_cog(Cope(bot))
