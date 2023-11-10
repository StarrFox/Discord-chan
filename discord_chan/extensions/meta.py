from typing import Annotated, Optional

import discord
from discord.ext import commands

from discord_chan import BotConverter


class Meta(commands.Cog, name="meta"):
    """Informational commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """
        Sends the bot's websocket latency
        """
        await ctx.send(
            f"\N{TABLE TENNIS PADDLE AND BALL} {round(ctx.bot.latency * 1000)}ms"
        )

    @commands.command()
    async def invite(
        self,
        ctx: commands.Context,
        target_bot: Annotated[
            discord.Member | discord.User | discord.ClientUser | None, BotConverter
        ] = None,
    ):
        """
        Get the invite link for a bot,
        defaults to myself
        """
        if target_bot is None:
            target_bot = ctx.me

        url = discord.utils.oauth_url(target_bot.id)
        await ctx.send(url)

    @commands.command()
    async def source(self, ctx: commands.Context):
        """
        Links to the bot's source url
        """
        await ctx.send("https://github.com/StarrFox/Discord-chan")


async def setup(bot):
    cog = Meta(bot)
    await bot.add_cog(cog)
    bot.help_command.cog = cog


async def teardown(bot):
    bot.help_command.cog = None
