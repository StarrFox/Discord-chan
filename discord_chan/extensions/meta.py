from typing import Annotated

import discord
from discord.ext import commands

from discord_chan import BotConverter
from discord_chan.checks import cog_loaded


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
    @cog_loaded("Jishaku")
    async def source(self, ctx: commands.Context, *, command_name: str):
        """
        Get a command's source code
        """
        jsk_source = self.bot.get_command("jishaku source")

        jsk = self.bot.get_cog("Jishaku")

        if jsk is None:
            raise RuntimeError("Jishaku cog somehow unloaded even with check")

        if jsk_source is None:
            return await ctx.send("Missing source command")

        await jsk_source.callback(jsk, ctx, command_name=command_name)  # type: ignore


async def setup(bot):
    cog = Meta(bot)
    await bot.add_cog(cog)
    bot.help_command.cog = cog


async def teardown(bot):
    bot.help_command.cog = None
